#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ui/donate.py – Donationsdialog (Ko-fi) för E-postofferten.

Länken kommer från inställningen ``donation_url`` (normaliseras med
``core.donate``). Är ingen länk inlagd visas en vänlig förklaring i
stället för en död knapp. All text går via ``core.i18n.tr`` (sv/en).

FIL: ui/donate.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.donate import configured_donation_url
from core.i18n import tr

log = logging.getLogger(__name__)


def open_url_in_browser(url: str) -> bool:
    """Öppna URL i standardwebbläsaren. True om Qt tog emot anropet."""
    try:
        return bool(QDesktopServices.openUrl(QUrl(str(url))))
    except Exception:
        log.warning("Kunde inte öppna URL: %s", url, exc_info=True)
        return False


class DonateDialog(QDialog):
    """❤️ Donationsdialog med Ko-fi-länk + kopieringsknapp."""

    def __init__(
        self, parent: Optional[QWidget] = None, donation_url: str = ""
    ) -> None:
        super().__init__(parent)
        self._url = configured_donation_url(donation_url) or ""
        self.setWindowTitle(tr("donate.title"))
        self.setMinimumWidth(460)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 18, 20, 18)

        heart = QLabel("❤️☕")
        heart.setStyleSheet("font-size: 40pt; background: transparent;")
        heart.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heart)

        heading = QLabel(tr("donate.heading"))
        heading.setStyleSheet("font-size: 15pt; font-weight: bold;")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)

        text = QLabel(tr("donate.text"))
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text)

        if self._url:
            row = QHBoxLayout()
            self._url_edit = QLineEdit(self._url)
            self._url_edit.setReadOnly(True)
            row.addWidget(self._url_edit, stretch=1)
            btn_copy = QPushButton(tr("donate.copy_btn"))
            btn_copy.clicked.connect(self._copy_url)
            row.addWidget(btn_copy)
            layout.addLayout(row)

            btn_open = QPushButton(tr("donate.open_btn"))
            btn_open.setProperty("cssClass", "success")
            btn_open.clicked.connect(self._open_url)
            layout.addWidget(btn_open)
        else:
            hint = QLabel(tr("donate.not_configured"))
            hint.setWordWrap(True)
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint.setProperty("cssClass", "muted")
            layout.addWidget(hint)

        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setProperty("cssClass", "subtext")
        layout.addWidget(self._status)

        btn_close = QPushButton("OK")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

    def _copy_url(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is not None and self._url:
            clipboard.setText(self._url)
            self._status.setText(tr("donate.copied"))

    def _open_url(self) -> None:
        if self._url and not open_url_in_browser(self._url):
            self._status.setText(tr("donate.invalid_url"))


__all__ = ["DonateDialog", "open_url_in_browser"]
