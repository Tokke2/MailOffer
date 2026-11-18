#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ui/donate.py – Stöd projektet-sidan i appen (Ko-fi, PayPal, Swish).

En komplett donationssida inuti appen (samma upplägg som systerappen
ArkivPiloten, anpassad för E-postofferten): säker-betalning-rad,
PayPal- och Ko-fi-knappar med kopiera-länk, Swish med QR-kod som
ritas direkt från numret i inställningarna, "varför din hjälp betyder
allt" och FAQ. All text via ``core.i18n.tr`` (sv/en).

Länkarna löses upp av ``core.donate.resolve_donation_links``:
projektets fasta mottagare används; sparade överstyrningar ignoreras.

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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.donate import (
    build_swish_payload,
    format_swish_number,
    is_valid_swish_number,
    normalize_swish_number,
    resolve_donation_links,
    DEFAULT_SWISH_NUMBER,
    paypal_donation_url,
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

        # Whole-pixel modules and a four-module quiet zone: no interpolation.
        qr = qrcode.QRCode(border=4, box_size=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(payload)
        qr.make(fit=True)
        modules = qr.modules_count + 8
        qr.box_size = max(1, size // modules)
        image = qr.make_image(fill_color='black', back_color='white')
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        pixmap = QPixmap()
        if not pixmap.loadFromData(buffer.getvalue()):
            return None
        return pixmap
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
        self._swish_number = DEFAULT_SWISH_NUMBER
        self._swish_payload = ""
        if is_valid_swish_number(self._swish_number):
            try:
                self._swish_payload = build_swish_payload(self._swish_number)
            except ValueError:
                self._swish_payload = ""
        self._qr_pixmap: Optional[QPixmap] = None

        self.setWindowTitle(tr("donate.title"))
        self.setMinimumSize(320, 360)
        self.resize(580, 760)
        self._build_ui()
        from ui.screen_fit import fit_window
        fit_window(self)

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

        hero = QWidget()
        hero.setObjectName('donationHero')
        hero.setStyleSheet('#donationHero { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #168555, stop:0.5 #20794e, stop:0.85 #b75d18, stop:1 #ac7b16); border-radius:22px; } #donationHero QLabel { color:white; background:transparent; }')
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.addWidget(self._header_icon())
        eyebrow = _centered(QLabel('FRIVILLIGT STÖD • GRATIS ANVÄNDNING'))
        eyebrow.setStyleSheet('font-size:9pt; font-weight:700; letter-spacing:1px;')
        hero_layout.addWidget(eyebrow)
        heading = _centered(QLabel('Gillar du E-postofferten? 💚'))
        heading.setStyleSheet('font-size:21pt; font-weight:800;')
        hero_layout.addWidget(heading)
        hero_layout.addWidget(_centered(QLabel('Har E-postofferten sparat tid i din vardag?\nDitt stöd hjälper till med fortsatt utveckling, felsökning och underhåll.\nAppen är gratis att använda privat och kommersiellt. Donationer är helt frivilliga – inga funktioner eller förmåner kräver betalning.\nTack för att du hjälper projektet vidare!')))
        layout.addWidget(hero)
        layout.addWidget(_centered(QLabel('🔒 Fasta mottagare · Rickard Längkvist\nVälj Swish, Ko-fi eller PayPal. Granska och bekräfta alltid betalningen hos betaltjänsten.')))
        amounts = QGroupBox('Valfritt belopp – inga nivåer eller krav')
        amount_layout = QVBoxLayout(amounts)
        chips = QHBoxLayout()
        self._amount = QSpinBox()
        self._amount.setRange(0, 99999)
        self._amount.setSpecialValueText('Välj hos betaltjänsten')
        self._amount.setSuffix(' kr')
        self._amount.setValue(50)
        self._amount_buttons = {}
        for value in (25, 50, 100, 200):
            button = QPushButton(f'{value} kr')
            button.setCheckable(True)
            button.setAccessibleName(f'Donationsbelopp {value} kronor')
            button.setMinimumHeight(40)
            button.setStyleSheet('QPushButton { border:1px solid #779486; border-radius:16px; padding:6px; } QPushButton:checked { background:#19754d; color:white; border:2px solid #19754d; font-weight:700; }')
            self._amount_buttons[value] = button
            button.clicked.connect(lambda checked=False, n=value: self._amount.setValue(n))
            chips.addWidget(button)
        amount_layout.addLayout(chips)
        amount_layout.addWidget(self._amount)
        hint = QLabel('Beloppet följer med i Swish-QR och till PayPal. På Ko-fi väljer du belopp hos tjänsten. Välj 0 för att ange belopp hos betaltjänsten.')
        hint.setWordWrap(True)
        amount_layout.addWidget(hint)
        self._amount_info = QLabel()
        self._amount_info.setObjectName('donationAmountInfo')
        self._amount_info.setWordWrap(True)
        amount_layout.addWidget(self._amount_info)
        layout.addWidget(self._swish_group())
        layout.addWidget(amounts)
        self._amount.valueChanged.connect(self._refresh_swish_qr)
        self._refresh_swish_qr()
        alternatives = QGroupBox('Fler sätt att stödja projektet')
        alternative_layout = QVBoxLayout(alternatives)
        for label, name, action in (
            ('☕ Stöd via Ko-fi ↗', 'donationKofiButton', self._open_kofi),
            ('💙 Stöd via PayPal ↗', 'donationPaypalButton', self._open_paypal),
        ):
            button = QPushButton(label)
            button.setObjectName(name)
            button.setMinimumHeight(48)
            base, hover = ('#be3e43', '#a93136') if name == 'donationKofiButton' else ('#086ca8', '#055789')
            button.setStyleSheet(f'QPushButton {{ background:{base}; color:white; border:0; border-radius:13px; padding:12px; font-weight:700; }} QPushButton:hover {{ background:{hover}; }} QPushButton:focus {{ border:2px solid #c49b30; }}')
            button.clicked.connect(action)
            alternative_layout.addWidget(button)
        note = QLabel('Knapparna öppnar respektive betaltjänst i webbläsaren. Appen tar inte emot kort- eller bankuppgifter. Mottagarna kan inte ändras via inställningarna.')
        note.setWordWrap(True)
        alternative_layout.addWidget(note)
        layout.addWidget(alternatives)
        thanks = QGroupBox('💚 Tack för att du stödjer E-postofferten')
        thanks_layout = QVBoxLayout(thanks)
        for title, body in (
            ('🔧 Underhåll & felsökning', 'Ditt frivilliga stöd bidrar till arbetet med att hitta problem och förbättra appen.'),
            ('💡 Fortsatt utveckling', 'Enklare arbetsflöden, tydligare mallar och bättre användbarhet – utan donationsnivåer eller betalvägg.'),
            ('⭐ Hjälp även utan pengar', 'Rapportera ett fel, föreslå en förbättring eller tipsa någon som kan ha nytta av appen. Det uppskattas också!'),
        ):
            title_label = QLabel(title)
            title_label.setWordWrap(True)
            title_label.setStyleSheet('font-weight:700;')
            thanks_layout.addWidget(title_label)
            body_label = QLabel(body)
            body_label.setWordWrap(True)
            thanks_layout.addWidget(body_label)
        layout.addWidget(thanks)
        footer = _centered(QLabel('© 2026 Rickard Längkvist • Kostnadsfri privat och kommersiell användning'))
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
        button.setMinimumHeight(48)
        color = '#0070ba' if 'PayPal' in caption else '#ce465c'
        button.setStyleSheet(f'QPushButton {{ background:{color}; color:white; border:0; border-radius:12px; padding:12px; font-weight:700; }} QPushButton:hover {{ background:#285b80; }}')
        button.clicked.connect(on_open)
        row.addWidget(button, stretch=1)
        copy_btn = QPushButton(tr("donate.copy_btn"))
        copy_btn.clicked.connect(on_copy)
        row.addWidget(copy_btn)
        return row

    def _swish_group(self) -> QGroupBox:
        group = QGroupBox('💚 Swish – förstahandsval')
        group.setObjectName('swishCard')
        group.setStyleSheet('#swishCard { border:2px solid #159b70; border-radius:14px; margin-top:12px; padding:14px; }')
        layout = QVBoxLayout(group)
        self._swish_qr_label = QLabel()
        self._swish_qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._swish_qr_label.setWordWrap(True)
        self._swish_qr_label.setStyleSheet('background:white; color:#17324d; padding:10px; border-radius:12px;')
        layout.addWidget(self._swish_qr_label, alignment=Qt.AlignmentFlag.AlignCenter)
        hint = _centered(QLabel('Skanna QR-koden med Swish-appen. Kontrollera mottagaren i Swish och bekräfta där. Beloppet kan ändras.'))
        layout.addWidget(hint)
        return group

    def _refresh_swish_qr(self, *_):
        value = self._amount.value()
        for amount, button in self._amount_buttons.items():
            button.setChecked(amount == value)
        self._amount_info.setText(f'Valt: {value} kr – tack! 💚' if value else 'Valfritt belopp – välj hos betaltjänsten. Tack! 💚')
        self._swish_payload = build_swish_payload(DEFAULT_SWISH_NUMBER, amount=str(value) if value else '')
        self._qr_pixmap = swish_qr_pixmap(self._swish_payload)
        if self._qr_pixmap is not None and not self._qr_pixmap.isNull():
            self._swish_qr_label.setPixmap(self._qr_pixmap)
        else:
            self._swish_qr_label.clear()
            self._swish_qr_label.setText('QR-koden kunde inte skapas. Kontrollera tillägget qrcode. Inget Swish-nummer visas i klartext.')

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

    def _open_kofi(self) -> None:
        if not open_url_in_browser(self._kofi_url):
            self._status.setText(tr("donate.invalid_url"))

    def _open_paypal(self) -> None:
        if not open_url_in_browser(paypal_donation_url(self._amount.value())):
            self._status.setText(tr("donate.invalid_url"))


__all__ = ["DonateDialog", "open_url_in_browser", "swish_qr_pixmap"]
