#!/usr/bin/env pythonw
# -*- coding: utf-8 -*-
"""
main.pyw – EmailApp Entry Point (PyQt6)

Version: 5.4 – MALL-WIZARD + SV/EN-UI + GITHUB-UPDATE + DONATION
(tidigare: 5.0 – AUTOSTART v2 + DUBBELKLICK (stale_console + --background))

Nytt i 5.4:
- ✅ MALL-WIZARD (ui/template_wizard): skapa mallar steg för steg
    (TXT/HTML/DOCX, SV + valfritt [en]-block, förhandsgranskning)
- ✅ APPEN PÅ SV/EN (core/i18n): skal, menyer, flikar, wizard,
    uppdatering och donation via tr(); språkbyte i Språk-menyn
- ✅ AUTOUPDATE FRÅN GITHUB RELEASES (core/github_update): tyst
    sökning vid start (max 1/dygn) + manuell sökknapp; mallar, JSON
    och inställningar rörs aldrig (Mallar/ skyddas nu också)
- ✅ DONATION via Ko-fi: ❤️-knapp/dialog, länk i Inställningar
- ✅ core/version.py = enda versionskällan; EMAILAPP_RELAUNCH ger
    ren omstart (låset släpps först) efter språkbyte/uppdatering

Fixar mot v4.8:
- ✅ MUSHJULSSKYDD (ui/wheel_guard v1.0): mushjulet ändrar ALDRIG
    värden i dropdowns/spinnrutor/reglage/radfält – det skrollar
    i stället närmaste skrollområde (sidan). Installeras på
    QApplication direkt efter skapandet (steg 9.6).
- ✅ APP-IKON: QApplication.setWindowIcon (via core/app_icon v1.0)

Fixar mot v4.7:
- ✅ _ensure_pythonw(): om appen startats med python.exe (konsol) på
    Windows startas den OM automatiskt med pythonw.exe (ingen terminal)
    * Sökkedja: bredvid sys.executable → sys.base_prefix → PATH
    * Skyddad mot loop via miljövariabel EMAILAPP_USE_PYTHONW=1
    * Fungerar för dubbelklick, .bat, registry-autostart – allt
    * Hoppas över vid frozen (pyinstaller) och icke-Windows
- ✅ Autostart via registret (Windows Run-nyckeln) skrivs med
    pythonw.exe – se core/settings_manager v24.6 (_find_pythonw + _script_path)
- ✅ Kompletteras av Starta EmailApp.vbs – dubbelklick utan terminal
    även om .pyw-associationen saknas

Fixar mot v4.6:
- ✅ APP-IKON: QApplication.setWindowIcon (via core/app_icon v1.0)
    * Ikonen (icons/app_icon.png) visas på: huvudfönster, taskbar,
      alla dialoger (SendConfirmDialog, inställningar, meddelanden)
    * _safe_show_critical sätter ikonen även på tillfällig QApplication
    * Fallback: saknas ikonfilen ritas en kuvertikon programmatiskt
- ✅ APP_VERSION synkad till app-versionen (5.1.0) – låg tidigare på
  4.6.0 trots att UI visade v5.1

Fixar mot v4.5:
- ✅ Korrupt markdown/inklistringssyntax borttagen
  (__future__, __name__, log.info, settings.save,
   _safe_show_critical, _write_startup_crash_file,
   main_window.show(), main_window.save_geometry())
- ✅ shutdown_logging() anropas i finally
    * core.logger v3.5 är queue-baserad (QueueListener i bakgrundstråd)
    * Utan shutdown_logging() tappas loggposter vid avslut
    * Körs innan EventBus stängs
- ✅ handle_uncaught_exception() använder samma _safe_show_critical-logik
- ✅ Qt-runtime-env sätts före QApplication (ingen ctypes-DPI-hack)

Startsekvens:
 1.  Projektrot/sys.path + Qt-runtime env före QApplication
 2.  Logging setup
 3.  sys.excepthook
 4.  Single instance check
 5.  SettingsManager
 6.  EventBus singleton
 7.  RecoveryManager
 8.  CacheManager
 9.  QApplication
 10. MainWindow
 11. SystemTray
 11.5 main_window.set_tray(tray)
 12. sync_autostart
 13. bus.publish("app.startup")
 14. show/hide beroende på start_minimized
 15. app.exec()
 16. finally: geometri, tray.shutdown, settings.save,
     cache.cleanup, bus.shutdown, shutdown_logging,
     app.quit, instance.release

Viktigt v4.6:
- Ingen ctypes-DPI-hack. Qt6 hanterar DPI själv.
- Detta undviker Windows-varningen/kollisionen med
  SetProcessDpiAwarenessContext() failed: Åtkomst nekad.
- Projektroten läggs i sys.path innan lokala imports.
- Startup-fel loggas alltid och visas i QMessageBox om möjligt.
- Lokala imports för centrala moduler görs i main() så importfel också kan
  fångas, loggas och presenteras tydligt.

FIL: main.pyw
"""

from __future__ import annotations

# stdlib
import logging
import os
import platform
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any, Optional

# Projektrot måste in i sys.path INNAN lokala imports.
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Qt runtime-env måste sättas före QApplication skapas.
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

# third-party
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox

# Tidig logging – denna modul måste finnas för att bootstrap ska kunna logga.
from core.logger import get_logger, setup_logging

APP_NAME = "E-postofferten"
# (v5.4) Versionen bor i core/version.py – enda sanningskällan
# (GitHub-uppdateraren jämför release-taggar mot samma värde).
try:
    from core.version import __version__ as APP_VERSION
except Exception:  # pragma: no cover – nödfall om core/version saknas
    APP_VERSION = "5.4.0"
IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"
BACKGROUND_FLAGS = frozenset({"--background", "--minimized", "-background"})
CREATE_NO_WINDOW = 0x08000000
MIN_PYTHON_VERSION = (3, 10)
PYTHON_INSTALLER_BAT = "Installera_Python.bat"


def setup_qt_runtime() -> None:
    """Runtime-setup före QApplication.

    Qt6 sätter normalt DPI-awareness själv. Vi kör därför inte ctypes-anrop som
    SetProcessDpiAwarenessContext/SetProcessDpiAwareness/SetProcessDPIAware,
    eftersom de kan ge 'Åtkomst nekad' om DPI-context redan är satt.
    """
    # Medvetet tom förutom env ovan. Behålls som krok för framtida Qt-runtime.
    return


def _find_pythonw() -> Optional[str]:
    """Hitta pythonw.exe (Windows – ingen konsol).

    Sökkedja (v5.0): bredvid sys.executable → sys.base_prefix/prefix →
    %LOCALAPPDATA%\\Programs\\Python\\Python3* → PATH.
    """
    seen = set()
    candidates = []
    try:
        candidates.append(Path(sys.executable).with_name("pythonw.exe"))
    except Exception:
        pass
    for prefix in (getattr(sys, "base_prefix", ""), getattr(sys, "prefix", "")):
        if prefix:
            candidates.append(Path(prefix) / "pythonw.exe")
    local = os.getenv("LOCALAPPDATA") or ""
    if local:
        py_root = Path(local) / "Programs" / "Python"
        try:
            if py_root.is_dir():
                for child in sorted(py_root.glob("Python3*"), reverse=True):
                    candidates.append(child / "pythonw.exe")
        except Exception:
            pass
    for candidate in candidates:
        try:
            key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            if candidate.is_file():
                return key
        except Exception:
            continue
    try:
        import shutil

        found = shutil.which("pythonw.exe")
        if found:
            return found
    except Exception:
        pass
    return None


def _consume_background_flag(argv: list) -> bool:
    """Ta bort --background/--minimized från argv (Qt ska inte se dem)."""
    background = False
    kept = [argv[0]] if argv else [""]
    for arg in argv[1:]:
        if arg in BACKGROUND_FLAGS:
            background = True
        else:
            kept.append(arg)
    argv[:] = kept
    return background


def _ensure_pythonw() -> None:
    """(v5.0) Starta om med pythonw.exe om appen körs med konsol.

    Om appen startats med python.exe (t.ex. via .bat, fel association
    eller registry-start med fel tolk) startas den OM med pythonw.exe
    så att INGEN terminal syns. Skyddad mot loopar via
    miljövariabeln EMAILAPP_USE_PYTHONW=1.

    Hoppas över: icke-Windows, pythonw redan aktiv, frozen (pyinstaller),
    eller när ingen pythonw.exe hittas (då körs appen ändå).
    """
    if not IS_WINDOWS:
        return
    if getattr(sys, "frozen", False):
        return
    try:
        exe_name = Path(sys.executable).name.lower()
    except Exception:
        return
    if exe_name == "pythonw.exe":
        return
    if os.environ.get("EMAILAPP_USE_PYTHONW") == "1":
        return

    pythonw = _find_pythonw()
    if not pythonw:
        return

    script = Path(__file__).resolve()
    os.environ["EMAILAPP_USE_PYTHONW"] = "1"
    try:
        kwargs: dict = {
            "cwd": str(script.parent),
            "close_fds": True,
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if IS_WINDOWS:
            kwargs["creationflags"] = CREATE_NO_WINDOW
        extra = list(sys.argv[1:])
        subprocess.Popen([pythonw, str(script), *extra], **kwargs)
        sys.exit(0)
    except Exception:
        # Kan inte starta om – kör vidare med konsol ändå
        try:
            os.environ.pop("EMAILAPP_USE_PYTHONW", None)
        except Exception:
            pass
        return


def _python_supported(version_info: Any = None) -> bool:
    """True om tolken uppfyller minimikravet (Python 3.10+)."""
    info = version_info or sys.version_info
    try:
        return tuple(info[:2]) >= MIN_PYTHON_VERSION
    except Exception:
        return False


def _launch_python_installer_silent() -> bool:
    """Kör Installera_Python.bat /silent UTAN konsolfönster (Windows).

    Nödbroms när appen startats med för gammal Python. Normalfallet –
    Python saknas helt – hanteras före appstart av Starta EmailApp.vbs,
    som kör samma .bat dolt och väntar tills den är klar.
    """
    if not IS_WINDOWS:
        return False
    bat = BASE_DIR / PYTHON_INSTALLER_BAT
    if not bat.is_file():
        return False
    try:
        subprocess.Popen(
            ["cmd", "/c", str(bat), "/silent"],
            cwd=str(BASE_DIR),
            close_fds=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )
        return True
    except Exception:
        return False


def _safe_show_critical(title: str, message: str) -> None:
    """Visa kritiskt fel i QMessageBox om Qt finns; annars skriv till stderr."""
    try:
        app = QApplication.instance()
        temp_app: Optional[QApplication] = None
        if app is None:
            temp_app = QApplication(sys.argv)
            app = temp_app
        # (v4.7) App-ikonen även på kritiska dialoger
        try:
            from core.app_icon import set_app_icon

            set_app_icon(app)
        except Exception:
            pass
        QMessageBox.critical(None, title, message)
        if temp_app is not None:
            temp_app.quit()
    except Exception:
        try:
            sys.stderr.write(f"{title}\n{message}\n")
        except Exception:
            pass


def handle_uncaught_exception(
    exc_type: type,
    exc_value: BaseException,
    exc_traceback: object,
) -> None:
    """Fångar ohanterade exceptions, loggar och visar Qt-dialog."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    try:
        log = get_logger(__name__)
        log.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
    except Exception:
        pass

    log_file = BASE_DIR / "logs" / "email_app.log"
    message = (
        f"{APP_NAME} har stött på ett oväntat fel:\n\n"
        f"{exc_value}\n\n"
        f"Se loggen:\n{log_file}"
    )

    app = QApplication.instance()
    if app is None:
        _safe_show_critical("Kritiskt fel", message)
        return

    def show_dialog() -> None:
        try:
            QMessageBox.critical(app.activeWindow(), "Kritiskt fel", message)
        except Exception:
            pass

    QTimer.singleShot(0, show_dialog)


def save_window_geometry(
    settings: Any, main_window: Any, log: logging.Logger
) -> None:
    """Spara fönstergeometri till settings."""
    try:
        if hasattr(main_window, "save_geometry"):
            main_window.save_geometry()
            log.debug("Geometri sparad via main_window.save_geometry().")
            return
    except Exception as exc:
        log.debug("save_geometry() misslyckades: %s", exc)

    try:
        if hasattr(main_window, "geometry"):
            geo = main_window.geometry()
            geometry_str = f"{geo.width()}x{geo.height()}+{geo.x()}+{geo.y()}"
            settings.set("window_geometry", geometry_str)
            log.debug("Geometri sparad via geometry(): %s", geometry_str)
    except Exception as exc:
        log.debug("Kunde inte spara geometri via fallback: %s", exc)


def _write_startup_crash_file(exc: BaseException) -> None:
    """Sista skyddsnät för pythonw/tyst krasch: skriv crash-fil."""
    try:
        crash_path = BASE_DIR / "logs" / "startup_crash.log"
        crash_path.parent.mkdir(parents=True, exist_ok=True)
        crash_path.write_text(
            "Startup crash\n"
            f"Python: {sys.version}\n"
            f"Platform: {platform.platform()}\n"
            f"Error: {exc}\n\n"
            f"{traceback.format_exc()}\n",
            encoding="utf-8",
        )
    except Exception:
        pass


def _install_python_addons_with_progress(app: QApplication) -> None:
    """Visa progressbar och installera/uppdatera saknade tillägg."""
    try:
        from core.dep_check import install_needed, needed_packages
    except Exception:
        return
    todo = needed_packages(True)
    if not todo:
        return
    try:
        from PyQt6.QtWidgets import QProgressDialog
        from PyQt6.QtCore import Qt
    except Exception:
        install_needed(True, None)
        return

    dialog = QProgressDialog(
        "Kontrollerar Python-tillägg…", None, 0, max(1, len(todo)), None
    )
    dialog.setWindowTitle("E-postofferten – tillägg")
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    dialog.setCancelButton(None)
    dialog.setValue(0)
    dialog.show()
    app.processEvents()

    def on_progress(current: int, total: int, message: str) -> None:
        try:
            dialog.setMaximum(max(1, total))
            dialog.setLabelText(message)
            dialog.setValue(min(current, total))
            app.processEvents()
        except Exception:
            pass

    try:
        summary = install_needed(True, on_progress)
    finally:
        try:
            dialog.close()
        except Exception:
            pass
    failed = summary.get("failed") or []
    if failed:
        QMessageBox.warning(
            None,
            "Tillägg",
            "Kunde inte installera:\n" + "\n".join(failed),
        )


def main() -> None:
    """Tunn bootstrapper – ingen affärslogik."""
    # (v4.8/v5.0) Först av allt: garantera pythonw (ingen terminal) på Windows
    _ensure_pythonw()
    # (v5.4) För gammal Python: starta 3.12-installationen tyst i
    # bakgrunden och avsluta snällt i stället för att krascha i imports.
    if not _python_supported():
        _launch_python_installer_silent()
        _safe_show_critical(
            APP_NAME,
            "E-postofferten kräver Python 3.10 eller nyare.\n\n"
            "Installation av Python 3.12 har startats i bakgrunden "
            "(Installera_Python.bat). Vänta någon minut och starta "
            "sedan appen igen via Starta EmailApp.vbs.",
        )
        return
    background_start = _consume_background_flag(sys.argv)

    setup_qt_runtime()

    # Initiera logging så tidigt som möjligt.
    log_dir = BASE_DIR / "logs"
    setup_logging(log_dir, level="INFO", debug=False)
    log = get_logger(__name__)
    try:
        from core.logger import cleanup_old_logs

        n = cleanup_old_logs(log_dir, days=10)
        if n:
            log.info("Rensade %d gamla loggfiler", n)
    except Exception:
        pass

    log.info(
        "🚀 %s v%s startar på %s",
        APP_NAME, APP_VERSION, platform.platform(),
    )
    sys.excepthook = handle_uncaught_exception

    acquired = False
    instance: Optional[Any] = None
    app: Optional[QApplication] = None
    settings: Optional[Any] = None
    tray: Optional[Any] = None
    cache: Optional[Any] = None
    main_window: Optional[Any] = None
    event_bus: Optional[Any] = None
    exit_code = 0

    try:
        # Importera projektmoduler här så även importfel kan fångas i bootstrap.
        from core.cache_manager import CacheManager
        from core.event_bus import bus
        from core.recovery_manager import init_recovery_manager
        from core.settings_manager import SettingsManager
        from core.single_instance import ensure_single_instance
        from ui.main_window import MainWindow
        from ui.tray import SystemTray

        event_bus = bus

        # Single instance
        acquired, instance = ensure_single_instance(APP_NAME)
        if not acquired:
            log.info(
                "En annan instans kör – fokuserar den och avslutar."
            )
            if instance is not None:
                try:
                    instance.focus_existing()
                except Exception:
                    log.debug(
                        "focus_existing misslyckades", exc_info=True
                    )
            return

        # Settings
        settings = SettingsManager(BASE_DIR)
        # (v5.4) Sätt UI-språket (sv/en) så tidigt att även eventuella
        # startdialoger använder rätt språk (MainWindow sätter det igen).
        try:
            from core.i18n import set_language as _set_ui_language

            _set_ui_language(
                settings.get_ui_language()
                if hasattr(settings, "get_ui_language")
                else settings.get("language", "sv")
            )
        except Exception:
            log.debug("i18n-språkinit hoppades över", exc_info=True)
        try:
            from core.user_backup import backup_address_lists, backup_settings

            backup_address_lists(BASE_DIR)
            backup_settings(BASE_DIR)
        except Exception:
            log.debug("Adresslist-backup hoppades över", exc_info=True)
        try:
            from core.tb_bridge import register_thunderbird_host

            register_thunderbird_host(BASE_DIR)
        except Exception:
            log.debug("Thunderbird-koppling hoppades över", exc_info=True)
        log.debug(
            "Settings laddade: %s",
            getattr(settings, "settings_file_path", "?"),
        )

        # Re-konfigurera logging efter laddade settings för korrekt nivå/debug.
        try:
            setup_logging(
                log_dir,
                level=str(settings.get("log_level", "INFO")),
                debug=bool(settings.get("debug_logging", False)),
            )
            log = get_logger(__name__)
            log.debug("Logging omkonfigurerad från settings.")
        except Exception:
            log.warning(
                "Kunde inte omkonfigurera logging från settings",
                exc_info=True,
            )

        # Recovery
        recovery = init_recovery_manager(event_bus)
        log.debug("RecoveryManager initierad.")

        # Cache
        cache = CacheManager(
            base_dir=BASE_DIR,
            mode=settings.get("mode", "prod"),
            smart_cache=settings.get("smart_cache", True),
        )
        log.debug("CacheManager initierad: %s", cache)

        # QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        app.setQuitOnLastWindowClosed(False)

        # Saknade/för gamla Python-tillägg – progressbar, sedan vidare
        try:
            _install_python_addons_with_progress(app)
        except Exception:
            log.debug("Tilläggsinstallation hoppades över", exc_info=True)

        # (v4.7) App-ikonen – ärvs av huvudfönster, dialoger och taskbar
        try:
            from core.app_icon import set_app_icon

            if set_app_icon(app):
                log.debug("App-ikon satt (QApplication.setWindowIcon).")
        except Exception:
            log.debug("Kunde inte sätta app-ikonen", exc_info=True)

        # (v4.9) Muskjulsskydd – mushjulet skrollar sidan, ändrar
        # aldrig fältvärden (dropdowns, spinnrutor, reglage, radfält)
        try:
            from ui.wheel_guard import install_wheel_guard

            if install_wheel_guard(app):
                log.debug("Muskjulsskydd installerat.")
        except Exception:
            log.debug("Kunde inte installera muskjulsskydd", exc_info=True)

        # MainWindow
        main_window = MainWindow(settings, event_bus, recovery)
        log.debug("MainWindow initierad.")

        # SystemTray
        tray = SystemTray(app, settings, event_bus, main_window)
        tray.setup()
        log.debug("SystemTray setup klar.")

        # Koppla tray till MainWindow
        if hasattr(main_window, "set_tray"):
            main_window.set_tray(tray)
            log.debug("main_window.set_tray() anropad.")

        # Sync autostart (v24.7: reparerar python.exe/stale_console)
        try:
            settings.sync_autostart()
            try:
                info = settings.get_autostart_info()
                log.debug(
                    "Autostart: wanted=%s klass=%s pythonw=%s",
                    info.get("wanted"),
                    info.get("classification"),
                    info.get("pythonw"),
                )
            except Exception:
                pass
            log.debug("Autostart synkroniserad.")
        except Exception as exc:
            log.warning("sync_autostart misslyckades: %s", exc)

        # Startup event
        try:
            event_bus.publish(
                "app.startup",
                {
                    "version": APP_VERSION,
                    "mode": settings.get("mode", "prod"),
                },
            )
        except Exception:
            log.debug("Kunde inte publicera app.startup", exc_info=True)

        # Visa/dölj vid start (--background tvingar tray, ingen splash)
        if background_start or settings.get("start_minimized", True):
            main_window.hide()
            log.debug(
                "Startar minimerat (background=%s, start_minimized=%s).",
                background_start,
                settings.get("start_minimized", True),
            )
        else:
            main_window.show()
            log.debug("Fönster visas (start_minimized=False).")

        log.info(
            "✅ %s v%s redo – enter app.exec().", APP_NAME, APP_VERSION
        )
        exit_code = app.exec()

    except Exception as exc:
        _write_startup_crash_file(exc)
        log.exception("Kritiskt fel vid uppstart av %s.", APP_NAME)
        _safe_show_critical(
            "Startfel",
            f"{APP_NAME} kunde inte starta:\n\n{exc}\n\n"
            f"Se loggar:\n{BASE_DIR / 'logs'}",
        )
        exit_code = 1

    finally:
        try:
            log.info("🛑 %s stängs ner…", APP_NAME)
        except Exception:
            pass

        if settings is not None and main_window is not None:
            try:
                save_window_geometry(settings, main_window, log)
            except Exception as exc:
                log.debug("Geometri kunde inte sparas: %s", exc)

        if tray is not None:
            try:
                tray.shutdown()
                log.debug("SystemTray stoppad.")
            except Exception as exc:
                log.debug("tray.shutdown() fel: %s", exc)

        if event_bus is not None:
            try:
                event_bus.publish("app.shutdown", {"reason": "exit"})
            except Exception:
                pass

        if settings is not None:
            try:
                settings.save()
                log.debug("Inställningar sparade.")
            except Exception as exc:
                log.error("Kunde inte spara inställningar: %s", exc)

        if cache is not None:
            try:
                cache.cleanup()
                log.debug("CacheManager cleanup klar.")
            except Exception as exc:
                log.debug("cache.cleanup() fel: %s", exc)

        if event_bus is not None:
            try:
                event_bus.shutdown()
                log.debug("EventBus stoppad.")
            except Exception as exc:
                log.debug("bus.shutdown() fel: %s", exc)

        # (v4.6) Töm logg-kön – annars tappas poster vid avslut
        try:
            from core.logger import shutdown_logging
            shutdown_logging()
        except Exception:
            pass

        if app is not None:
            try:
                app.quit()
            except Exception:
                pass

        if instance is not None:
            try:
                instance.release()
                log.debug("Single instance lock frigjord.")
            except Exception as exc:
                log.debug("instance.release() fel: %s", exc)

        # (v5.4) Omstart begärd inifrån appen (språkbyte eller
        # GitHub-uppdatering): starta ersättaren FÖRST NU, när
        # single-instance-låset ovan är släppt och allt är sparat.
        if os.environ.pop("EMAILAPP_RELAUNCH", "") == "1":
            try:
                script = Path(__file__).resolve()
                exe = (_find_pythonw() if IS_WINDOWS else None) or sys.executable
                relaunch_kwargs: dict = {
                    "cwd": str(BASE_DIR),
                    "close_fds": True,
                    "stdin": subprocess.DEVNULL,
                    "stdout": subprocess.DEVNULL,
                    "stderr": subprocess.DEVNULL,
                }
                if IS_WINDOWS:
                    relaunch_kwargs["creationflags"] = CREATE_NO_WINDOW
                subprocess.Popen([exe, str(script)], **relaunch_kwargs)
            except Exception:
                pass

        try:
            log.info("✅ %s avslutad.", APP_NAME)
        except Exception:
            pass

    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
