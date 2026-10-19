#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ui/donate.py – Stöd projektet-sidan i appen (Ko-fi, PayPal, Swish).

En komplett donationssida inuti appen (samma upplägg som systerappen
ArkivPiloten, anpassad för E-postofferten): säker-betalning-rad,
PayPal- och Ko-fi-knappar med kopiera-länk, Swish med QR-kod som
ritas direkt från numret i inställningarna, "varför din hjälp betyder
allt" och FAQ. All text via ``core.i18n.tr`` (sv/en).

Länkarna löses upp av ``core.donate.resolve_donation_links``:
sparade inställningar vinner, annars projektets standardlänkar.

Swish-QR kräver paketet ``qrcode`` (OPTIONAL i core/dep_check –
installeras automatiskt vid start). Saknas det visas numret ändå
(fail-soft, aldrig krasch).

FIL: ui/donate.py
"""

from __future__ import annotations

import io
import logging
import sys
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.donate import (
    build_swish_payload,
    format_swish_number,
    is_valid_swish_number,
    normalize_swish_number,
    resolve_donation_links,
)
from core.i18n import tr

log = logging.getLogger(__name__)


def open_url_in_browser(url: str) -> bool:
    """Öppna URL i standardwebbläsaren. True om Qt tog emot anropet."""
    try:
        return bool(QDesktopServices.openUrl(QUrl(str(url))))
    except Exception:
        log.warning("Kunde inte öppna URL: %s", url, exc_info=True)
        return False


def swish_qr_pixmap(payload: str, size: int = 230) -> Optional[QPixmap]:
    """Rita QR-kod för en Swish-payload. None om qrcode-paketet saknas."""
    if not payload:
        return None
    try:
        import qrcode  # type: ignore

        image = qrcode.make(payload, border=2, box_size=10)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        pixmap = QPixmap()
        if not pixmap.loadFromData(buffer.getvalue()):
            return None
        return pixmap.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    except Exception:
        log.debug("Kunde inte rita Swish-QR (qrcode saknas?)", exc_info=True)
        return None


def _centered(label: QLabel, word_wrap: bool = True) -> QLabel:
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setWordWrap(word_wrap)
    return label


class DonateDialog(QDialog):
    """❤️ Stöd projektet – PayPal, Ko-fi och Swish med QR-kod."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        kofi_url: str = "",
        paypal_url: str = "",
        swish_number: str = "",
        donation_url: Optional[str] = None,
    ) -> None:
        super().__init__(parent)
        # donation_url = bakåtkompatibelt alias för Ko-fi-länken
        self._kofi_url, self._paypal_url = resolve_donation_links(
            kofi_url or donation_url or "", paypal_url
        )
        self._url = self._kofi_url  # bakåtkompat (äldre anrop/tester)
        self._swish_number = normalize_swish_number(swish_number)
        self._swish_payload = ""
        if is_valid_swish_number(self._swish_number):
            try:
                self._swish_payload = build_swish_payload(self._swish_number)
            except ValueError:
                self._swish_payload = ""
        self._qr_pixmap: Optional[QPixmap] = None

        self.setWindowTitle(tr("donate.title"))
        self.setMinimumSize(540, 620)
        self.resize(580, 760)
        self._build_ui()

    # ────────────────────────────────────────────────────────────────
    # UI
    # ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        root.addWidget(scroll, stretch=1)

        inner = QWidget()
        scroll.setWidget(inner)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)

        layout.addWidget(self._header_icon())
        heading = _centered(QLabel(tr("donate.heading")))
        heading.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(heading)
        badges = _centered(QLabel(f"<b>{tr('donate.badges')}</b>"))
        layout.addWidget(badges)
        secure = _centered(QLabel(tr("donate.secure_line")))
        secure.setProperty("cssClass", "subtext")
        layout.addWidget(secure)

        intro = _centered(QLabel(tr("donate.intro")))
        layout.addWidget(intro)

        layout.addLayout(
            self._link_row(
                tr("donate.paypal_btn"), self._paypal_url,
                self._open_paypal, self._copy_paypal, "success",
            )
        )
        layout.addLayout(
            self._link_row(
                tr("donate.kofi_btn"), self._kofi_url,
                self._open_kofi, self._copy_url, "accent",
            )
        )
        monthly = _centered(QLabel(tr("donate.monthly_hint")))
        monthly.setProperty("cssClass", "subtext")
        layout.addWidget(monthly)

        layout.addWidget(self._swish_group())
        layout.addWidget(self._why_group())
        layout.addWidget(self._faq_group())

        footer = _centered(QLabel(tr("donate.footer")))
        footer.setProperty("cssClass", "muted")
        layout.addWidget(footer)

        self._status = _centered(QLabel(""))
        self._status.setProperty("cssClass", "subtext")
        layout.addWidget(self._status)

        btn_close = QPushButton("OK")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

    def _header_icon(self) -> QLabel:
        """App-ikonen överst (samma som överallt annars i appen)."""
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            from core.app_icon import get_app_icon

            icon = get_app_icon()
            pixmap = icon.pixmap(84, 84) if icon is not None else QPixmap()
            if not pixmap.isNull():
                label.setPixmap(pixmap)
                return label
        except Exception:
            log.debug("Kunde inte ladda app-ikonen till donationen", exc_info=True)
        label.setText("❤️☕")
        label.setStyleSheet("font-size: 40pt; background: transparent;")
        return label

    def _link_row(self, caption, url, on_open, on_copy, css_class):
        row = QHBoxLayout()
        button = QPushButton(caption)
        button.setProperty("cssClass", css_class)
        button.setMinimumHeight(40)
        button.clicked.connect(on_open)
        row.addWidget(button, stretch=1)
        copy_btn = QPushButton(tr("donate.copy_btn"))
        copy_btn.clicked.connect(on_copy)
        row.addWidget(copy_btn)
        return row

    def _swish_group(self) -> QGroupBox:
        group = QGroupBox(tr("donate.swish_title"))
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        if not self._swish_payload:
            hint = _centered(QLabel(tr("donate.swish_not_configured")))
            hint.setProperty("cssClass", "muted")
            layout.addWidget(hint)
            return group

        self._qr_pixmap = swish_qr_pixmap(self._swish_payload)
        if self._qr_pixmap is not None and not self._qr_pixmap.isNull():
            qr_label = QLabel()
            qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qr_label.setPixmap(self._qr_pixmap)
            # Vit lugn yta bakom koden så den alltid går att skanna,
            # även i mörkt tema.
            qr_label.setStyleSheet(
                "background: #FFFFFF; padding: 8px; border-radius: 8px;"
            )
            layout.addWidget(qr_label, alignment=Qt.AlignmentFlag.AlignCenter)
            hint = _centered(QLabel(tr("donate.swish_scan_hint")))
            hint.setProperty("cssClass", "subtext")
            layout.addWidget(hint)
        else:
            hint = _centered(QLabel(tr("donate.swish_missing_lib")))
            hint.setProperty("cssClass", "muted")
            layout.addWidget(hint)

        row = QHBoxLayout()
        number_edit = QLineEdit(format_swish_number(self._swish_number))
        number_edit.setReadOnly(True)
        number_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(number_edit, stretch=1)
        copy_btn = QPushButton(tr("donate.copy_btn"))
        copy_btn.clicked.connect(self._copy_swish)
        row.addWidget(copy_btn)
        layout.addLayout(row)
        return group

    def _why_group(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)
        for n in (1, 2, 3):
            title = QLabel(f"<b>{tr(f'donate.why{n}_title')}</b>")
            layout.addWidget(title)
            body = QLabel(tr(f"donate.why{n}_body"))
            body.setWordWrap(True)
            body.setProperty("cssClass", "subtext")
            layout.addWidget(body)
        return widget

    def _faq_group(self) -> QGroupBox:
        group = QGroupBox(tr("donate.faq_title"))
        layout = QVBoxLayout(group)
        layout.setSpacing(6)
        for n in (1, 2, 3, 4):
            question = QLabel(f"<b>{tr(f'donate.faq{n}_q')}</b>")
            question.setWordWrap(True)
            layout.addWidget(question)
            answer = QLabel(tr(f"donate.faq{n}_a"))
            answer.setWordWrap(True)
            answer.setProperty("cssClass", "subtext")
            layout.addWidget(answer)
        return group

    # ────────────────────────────────────────────────────────────────
    # Åtgärder
    # ────────────────────────────────────────────────────────────────

    def _clipboard_set(self, text: str, status_key: str) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is not None and text:
            clipboard.setText(text)
            self._status.setText(tr(status_key))

    def _copy_url(self) -> None:
        self._clipboard_set(self._kofi_url, "donate.copied")

    def _copy_paypal(self) -> None:
        self._clipboard_set(self._paypal_url, "donate.copied")

    def _copy_swish(self) -> None:
        self._clipboard_set(self._swish_number, "donate.swish_number_copied")

    def _open_kofi(self) -> None:
        if not open_url_in_browser(self._kofi_url):
            self._status.setText(tr("donate.invalid_url"))

    def _open_paypal(self) -> None:
        if not open_url_in_browser(self._paypal_url):
            self._status.setText(tr("donate.invalid_url"))


__all__ = ["DonateDialog", "open_url_in_browser", "swish_qr_pixmap"]
