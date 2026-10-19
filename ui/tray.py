#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/tray.py – SystemTray för EmailApp (PyQt6)

Version: 4.5 – APP-IKON I SYSTEMFÄLTET (samma ikon överallt)

ÄNDRINGAR mot v4.4:
- ✅ Tray-ikonen är nu APP-IKONEN (icons/app_icon.png via
    core/app_icon.get_app_icon()) i stället för den enkla
    cirkel-kuverten – samma ikon som fönster, taskbar och dialoger
- ✅ Statuslägen (sending/error/success) = app-ikonen + liten
    status-badge nere till höger (symbol …/!/✓) – konsistent design
- ✅ Fallback kvar: saknas ikonfilen ritar core/app_icon en kuvertikon
    programmatiskt – tray fungerar alltid
- ✅ APP_VERSION synkad till app-versionen (5.1)

Fixar mot v4.3:
- ✅ Korrupt markdown/inklistringssyntax borttagen
  (__init__, __all__, __future__, log.info, self.APP_NAME,
   self.APP_VERSION, self._tray.show(), self.show_notification,
   main_window.show(), self._main_window.select_tab(),
   core.email_sender, _build_menu, _connect_signals,
   _subscribe_events, _unsubscribe_events, _slot_update_icon,
   _slot_notify, _slot_mail_sent, _slot_mail_failed,
   _slot_mod_disabled, _slot_startup, _slot_form_reset,
   _slot_default_loaded, _on_mail_sent, _on_mail_failed,
   _on_module_disabled, _on_startup, _on_form_reset,
   _on_default_loaded, _on_activated, _do_show, _do_hide,
   _do_open_settings, _do_test_smtp, _do_quit,
   _show_window_fallback, _create_tray_icon, >=)
- ✅ SNABBARE: ikonlägen cachas
    * create_tray_icon() ritar QPixmap varje gång ikonen byts
    * Nu: QIcon-cache per läge – endast första anropet ritar
- ✅ SNABBARE: notifications via QSystemTrayIcon.showMessage med
  timeout – ingen blockering
- ✅ QAction.setDefault() → QMenu.setDefaultAction() (PyQt6-fix,
  behålls från v4.2 – förhindrar startup-krasch)
- ✅ Dubbelklick-aktivering (DoubleClick) visar också fönster

Funktioner:
- QSystemTrayIcon (inbyggt i Qt – inget pystray/Pillow)
- Tydlig kuvertikon ritad via QPixmap + QPainter
- Kontextmeny via QMenu + QAction
- Enkelklick → visa huvudfönster
- Notiser via QSystemTrayIcon.showMessage()
- Trådsäker EventBus-integration via pyqtSignal
- Ikonlägen: idle / sending / error / success
- Success återgår till idle efter 3 sekunder

REGLER:
- Ingen Tkinter-kod
- Inga pystray/Pillow-beroenden
- EventBus-callbacks går via Qt-signals
- Ingen CC-logik i ny kod

FIL: ui/tray.py
"""

from __future__ import annotations

# stdlib
import logging
import threading
from typing import Any, Dict, Optional

# third-party
from PyQt6.QtCore import QObject, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

# local
from core.event_bus import EventBus
from core.settings_manager import SettingsManager

try:
    from core.app_icon import get_app_icon
except Exception:  # pragma: no cover
    def get_app_icon() -> QIcon:  # type: ignore[no-redef]
        return _idle_fallback_icon()

log = logging.getLogger("ui.tray")


# ═══════════════════════════════════════════════════════════════════════════
# Ikonlägen
# ═══════════════════════════════════════════════════════════════════════════

ICON_COLORS: Dict[str, str] = {
    "idle": "#2563EB",      # blå
    "sending": "#F59E0B",   # orange
    "error": "#DC2626",     # röd
    "success": "#16A34A",   # grön
}

ICON_SYMBOLS: Dict[str, str] = {
    "idle": "",
    "sending": "…",
    "error": "!",
    "success": "✓",
}

ICON_SIZE = 128

# ── Ikoncache (v4.4) ────────────────────────────────────────────────────
_icon_cache: Dict[str, QIcon] = {}


def _idle_fallback_icon() -> QIcon:
    """Enkel fallback-ikon om core.app_icon inte kan importeras."""
    from PyQt6.QtCore import QRectF, Qt

    size = ICON_SIZE
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    try:
        painter.setPen(QPen(QColor(255, 255, 255, 210), 5))
        painter.setBrush(QColor(ICON_COLORS["idle"]))
        painter.drawEllipse(QRectF(6, 6, size - 12, size - 12))
    finally:
        painter.end()
    return QIcon(pixmap)


def create_tray_icon(state: str = "idle") -> QIcon:
    """Skapa QIcon för systemfältet (v4.5: app-ikonen som bas).

    - idle:    exakt app-ikonen (icons/app_icon.png via
               core/app_icon.get_app_icon()) – samma ikon som
               fönster, taskbar och dialoger
    - sending/error/success: app-ikonen + liten status-badge nere
               till höger (symbol …/!/✓)

    Ikonerna cachas per läge – efterföljande anrop returnerar samma
    QIcon-objekt (snabbare uppdateringar).
    """
    state = state if state in ICON_COLORS else "idle"
    cached = _icon_cache.get(state)
    if cached is not None:
        return cached

    if state == "idle":
        icon = get_app_icon()
        _icon_cache["idle"] = icon
        return icon

    # Statuslägen: app-ikonen + badge nere till höger
    pixmap = get_app_icon().pixmap(ICON_SIZE, ICON_SIZE)
    if pixmap.isNull():
        pixmap = QPixmap(ICON_SIZE, ICON_SIZE)
        pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    try:
        badge_rect = QRectF(ICON_SIZE - 46, ICON_SIZE - 46, 38, 38)
        painter.setPen(QPen(QColor(255, 255, 255, 245), 4))
        painter.setBrush(QColor(ICON_COLORS[state]))
        painter.drawEllipse(badge_rect)

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        font = QFont()
        font.setBold(True)
        font.setPointSize(22 if state != "sending" else 18)
        painter.setFont(font)
        painter.drawText(
            badge_rect, Qt.AlignmentFlag.AlignCenter, ICON_SYMBOLS[state]
        )
    finally:
        painter.end()

    icon = QIcon(pixmap)
    _icon_cache[state] = icon
    return icon


# Bakåtkompatibelt alias för äldre importer
_create_tray_icon = create_tray_icon


# ═══════════════════════════════════════════════════════════════════════════
# TraySignals – trådsäker brygga (EventBus → Qt main thread)
# ═══════════════════════════════════════════════════════════════════════════

class _TraySignals(QObject):
    """Interna Qt-signals för trådsäker kommunikation."""

    mail_sent = pyqtSignal(dict)
    mail_failed = pyqtSignal(dict)
    mod_disabled = pyqtSignal(dict)
    startup = pyqtSignal(dict)
    form_reset = pyqtSignal(dict)
    default_loaded = pyqtSignal(dict)
    update_icon_sig = pyqtSignal(str)
    notify_sig = pyqtSignal(str, str)


# ═══════════════════════════════════════════════════════════════════════════
# SystemTray (PyQt6)
# ═══════════════════════════════════════════════════════════════════════════

class SystemTray:
    """Hanterar systemfältet för EmailApp via QSystemTrayIcon."""

    APP_NAME = "E-postofferten"
    APP_VERSION = "5.1"

    def __init__(
        self,
        app: QApplication,
        settings: SettingsManager,
        event_bus: EventBus,
        main_window: object,
    ) -> None:
        self._app = app
        self._settings = settings
        self._bus = event_bus
        self._main_window = main_window

        self._tray: Optional[QSystemTrayIcon] = None
        self._menu: Optional[QMenu] = None
        self._state = "idle"
        self._is_shutdown = False

        # Måste ägas av instansen för GC-skydd.
        self._signals = _TraySignals()

        log.debug("SystemTray (PyQt6) initierad.")

    # ─────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────

    def setup(self) -> None:
        """Skapa QSystemTrayIcon och koppla EventBus."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            log.warning(
                "Systemfältet är inte tillgängligt – visar fönster direkt."
            )
            self._show_window_fallback()
            return

        self._menu = QMenu()
        self._build_menu()

        self._tray = QSystemTrayIcon(create_tray_icon("idle"), self._app)
        self._tray.setToolTip(f"{self.APP_NAME} v{self.APP_VERSION}")
        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

        self._connect_signals()
        self._subscribe_events()

        log.info("SystemTray startad (QSystemTrayIcon).")

    def shutdown(self) -> None:
        """Stoppa tray och avprenumerera EventBus."""
        if self._is_shutdown:
            return
        self._is_shutdown = True

        self._unsubscribe_events()

        if self._tray is not None:
            self._tray.hide()
            self._tray = None

        self._menu = None
        log.debug("SystemTray stoppad.")

    def update_icon(self, state: str) -> None:
        """Byt ikonläge trådsäkert via signal."""
        if state not in ICON_COLORS:
            log.warning("Okänt ikonläge: %s", state)
            state = "idle"
        self._signals.update_icon_sig.emit(state)

    def show_notification(self, title: str, message: str) -> None:
        """Visa systemnotis trådsäkert via signal."""
        self._signals.notify_sig.emit(title, message)

    # ─────────────────────────────────────────────────────────────────
    # INIT-HJÄLPARE
    # ─────────────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._signals.mail_sent.connect(self._slot_mail_sent)
        self._signals.mail_failed.connect(self._slot_mail_failed)
        self._signals.mod_disabled.connect(self._slot_mod_disabled)
        self._signals.startup.connect(self._slot_startup)
        self._signals.form_reset.connect(self._slot_form_reset)
        self._signals.default_loaded.connect(self._slot_default_loaded)
        self._signals.update_icon_sig.connect(self._slot_update_icon)
        self._signals.notify_sig.connect(self._slot_notify)

    def _subscribe_events(self) -> None:
        # Bundna metoder – lambdas GC:as av weakref-bussen.
        # Handlers sparas i instansen (v4.4) så att unsubscribe använder
        # EXAKT samma bound-method-objekt (annars fungerar inte
        # is-jämförelsen i EventBus.unsubscribe).
        self._handlers: Dict[str, Any] = {
            "mail.sent": self._on_mail_sent,
            "mail.failed": self._on_mail_failed,
            "module.disabled": self._on_module_disabled,
            "app.startup": self._on_startup,
            "ui.form_reset": self._on_form_reset,
            "recipients.default_loaded": self._on_default_loaded,
        }
        for event_name, handler in self._handlers.items():
            self._bus.subscribe(event_name, handler)

    def _unsubscribe_events(self) -> None:
        for event_name, handler in getattr(self, "_handlers", {}).items():
            try:
                self._bus.unsubscribe(event_name, handler)
            except Exception:
                log.debug(
                    "Kunde inte avprenumerera %s", event_name, exc_info=True
                )
        self._handlers = {}

    # ─────────────────────────────────────────────────────────────────
    # MENYUPPBYGGNAD
    # ─────────────────────────────────────────────────────────────────

    def _build_menu(self) -> None:
        """Bygg QMenu med alla menyval."""
        if self._menu is None:
            return

        self._menu.clear()

        act_show = self._menu.addAction("👁️ Visa fönster")
        act_show.triggered.connect(self._do_show)
        # QAction har ingen setDefault() i PyQt6. Default-action sätts
        # på QMenu (v4.2-fix – förhindrar startup-krasch).
        self._menu.setDefaultAction(act_show)

        act_hide = self._menu.addAction("🙈 Dölj fönster")
        act_hide.triggered.connect(self._do_hide)

        self._menu.addSeparator()

        act_settings = self._menu.addAction("⚙️ Inställningar")
        act_settings.triggered.connect(self._do_open_settings)

        act_smtp = self._menu.addAction("🔌 Testa SMTP")
        act_smtp.triggered.connect(self._do_test_smtp)

        self._menu.addSeparator()

        act_quit = self._menu.addAction("❌ Avsluta helt")
        act_quit.triggered.connect(self._do_quit)

    # ─────────────────────────────────────────────────────────────────
    # SLOTS (körs i Qt main thread)
    # ─────────────────────────────────────────────────────────────────

    def _slot_update_icon(self, state: str) -> None:
        """Byt ikon i main thread (v4.4: cachad ikon – ingen omritning)."""
        if self._tray is None:
            return

        self._state = state
        try:
            self._tray.setIcon(create_tray_icon(state))
            self._tray.setToolTip(f"{self.APP_NAME} – {state}")
        except Exception:
            log.debug("_slot_update_icon misslyckades", exc_info=True)

        if state == "success":
            QTimer.singleShot(3000, lambda: self._slot_update_icon("idle"))

    def _slot_notify(self, title: str, message: str) -> None:
        """Visa notis i main thread."""
        if self._tray is None:
            return
        try:
            self._tray.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                3500,
            )
        except Exception:
            log.debug("_slot_notify misslyckades", exc_info=True)

    def _slot_mail_sent(self, data: dict) -> None:
        count = data.get("count", 0)
        subject = data.get("subject", "")
        self._slot_update_icon("success")
        self._slot_notify(
            "✅ E-post skickad",
            f"Skickad till {count} mottagare. Ämne: {subject}",
        )

    def _slot_mail_failed(self, data: dict) -> None:
        error = data.get("error", "Okänt fel")
        subject = data.get("subject", "")
        self._slot_update_icon("error")
        self._slot_notify(
            "❌ Sändning misslyckades", f"Ämne: {subject} – {error}"
        )

    def _slot_mod_disabled(self, data: dict) -> None:
        module = data.get("module", "Okänd modul")
        reason = data.get("reason", "")
        self._slot_notify(
            "⚠️ Modul inaktiverad", f"'{module}' inaktiverades: {reason}"
        )

    def _slot_startup(self, data: dict) -> None:
        del data
        self._slot_notify(self.APP_NAME, "E-postofferten är igång och redo.")

    def _slot_form_reset(self, data: dict) -> None:
        del data
        self._slot_notify(
            "🧹 Formulär rensat",
            "Formuläret rensades efter lyckad sändning.",
        )

    def _slot_default_loaded(self, data: dict) -> None:
        """Visa notis för standardmottagare. Ingen CC – endast Bcc."""
        bcc = int(data.get("bcc_count", 0) or 0)
        if bcc > 0:
            self._slot_notify(
                "📌 Standardmottagare", f"{bcc} standard-Bcc tillagda."
            )

    # ─────────────────────────────────────────────────────────────────
    # EVENTBUS-CALLBACKS (valfri tråd → Qt signal)
    # ─────────────────────────────────────────────────────────────────

    def _on_mail_sent(self, data: dict) -> None:
        self._signals.mail_sent.emit(data)

    def _on_mail_failed(self, data: dict) -> None:
        self._signals.mail_failed.emit(data)

    def _on_module_disabled(self, data: dict) -> None:
        self._signals.mod_disabled.emit(data)

    def _on_startup(self, data: dict) -> None:
        self._signals.startup.emit(data)

    def _on_form_reset(self, data: dict) -> None:
        self._signals.form_reset.emit(data)

    def _on_default_loaded(self, data: dict) -> None:
        self._signals.default_loaded.emit(data)

    # ─────────────────────────────────────────────────────────────────
    # UI-ACTIONS (Qt main thread)
    # ─────────────────────────────────────────────────────────────────

    def _on_activated(
        self, reason: QSystemTrayIcon.ActivationReason
    ) -> None:
        """Klick på tray-ikon → visa fönster (v4.4: även dubbelklick)."""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._do_show()

    def _do_show(self) -> None:
        """Visa och fokusera huvudfönster."""
        try:
            main_window = self._main_window
            if hasattr(main_window, "show"):
                main_window.show()
            if hasattr(main_window, "raise_"):
                main_window.raise_()
            if hasattr(main_window, "activateWindow"):
                main_window.activateWindow()
            self._bus.publish("ui.window_shown", {})
        except Exception:
            log.error("_do_show misslyckades", exc_info=True)

    def _do_hide(self) -> None:
        """Dölj huvudfönster."""
        try:
            if hasattr(self._main_window, "hide"):
                self._main_window.hide()
            self._bus.publish("ui.window_hidden", {})
        except Exception:
            log.error("_do_hide misslyckades", exc_info=True)

    def _do_open_settings(self) -> None:
        """Visa inställningsfliken."""
        try:
            self._do_show()
            if hasattr(self._main_window, "select_tab"):
                self._main_window.select_tab("Inställningar")
        except Exception:
            log.error("_do_open_settings misslyckades", exc_info=True)

    def _do_test_smtp(self) -> None:
        """Testa SMTP i bakgrundstråd och rapportera via tray."""
        self._do_show()
        if hasattr(self._main_window, "select_tab"):
            self._main_window.select_tab("Inställningar")

        def _test() -> None:
            try:
                from core.email_sender import test_smtp_connection

                server = self._settings.get("smtp_server", "")
                port = int(self._settings.get("smtp_port", 587))
                user = self._settings.get("username", "")
                pwd = self._settings.get("password", "")
                use_ssl = port == 465

                self.update_icon("sending")
                ok, message = test_smtp_connection(
                    server, port, user, pwd, use_ssl=use_ssl
                )
                self.update_icon("success" if ok else "error")
                title = (
                    "✅ SMTP-test lyckades"
                    if ok
                    else "❌ SMTP-test misslyckades"
                )
                self.show_notification(title, message)
            except Exception as exc:
                log.error("SMTP-test misslyckades", exc_info=True)
                self.update_icon("error")
                self.show_notification("❌ SMTP-test fel", str(exc))

        threading.Thread(target=_test, daemon=True, name="SMTPTestThread").start()

    def _do_quit(self) -> None:
        """Full shutdown via tray.

        main.pyw bör fortfarande ansvara för slutlig save/cache/bus-cleanup i
        sin finally-sektion. Här publiceras shutdown och appen stängs.
        """
        try:
            log.info("Avsluta via tray-meny.")
            try:
                self._bus.publish("app.shutdown", {"reason": "user_quit"})
            except Exception:
                log.debug("Kunde inte publicera app.shutdown", exc_info=True)
            self.shutdown()
            self._app.quit()
        except Exception:
            log.error("_do_quit misslyckades", exc_info=True)
            try:
                self._app.quit()
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────
    # FALLBACK
    # ─────────────────────────────────────────────────────────────────

    def _show_window_fallback(self) -> None:
        """Visa fönster direkt när systray inte är tillgängligt."""
        try:
            if hasattr(self._main_window, "show"):
                self._main_window.show()
            log.info("Fallback: fönster visas direkt (ingen tray).")
        except Exception:
            log.error("Fallback misslyckades", exc_info=True)

    # ─────────────────────────────────────────────────────────────────
    # BAKÅTKOMPATIBILITET
    # ─────────────────────────────────────────────────────────────────

    def stop(self) -> None:
        """Alias för shutdown()."""
        self.shutdown()


__all__ = [
    "SystemTray",
    "create_tray_icon",
    "_create_tray_icon",
    "ICON_COLORS",
    "ICON_SIZE",
]
