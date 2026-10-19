#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
core/settings_manager.py
========================

Central hanterare för alla programinställningar.

Version: 24.7 – AUTOSTART v2 (stale_console + verify + dubbelklick-VBS)

ÄNDRINGAR mot v24.6:
  - ✅ Autostart v2 (lånat mönster): klassificering missing | correct |
      stale_console | stale_path | stale_args | different
  - ✅ stale_console: registry-post som pekar på python.exe (konsolblink)
      upptäcks EXAKT och repareras automatiskt i sync_autostart()
  - ✅ Verify-after-write: varje registry-skrivning läses tillbaka
  - ✅ Registry-backup (roterad, max 10) före ändring/borttagning
  - ✅ Konflikt-detektion: andra produkters Run-poster → get_autostart_info()["conflicts"]
      (läs-only, rör aldrig andras poster)
  - ✅ --background i autostart-kommandot (tyst tray-start)
  - ✅ Föredrar Starta EmailApp.vbs via wscript //B när filen finns
      (samma robusta dubbelklick-kedja som autostart)
  - ✅ _find_pythonw(): även sys.prefix + %LOCALAPPDATA%\\Programs\\Python\\Python3*

ÄNDRINGAR mot v24.5:
  - ✅ _find_pythonw(): hittar pythonw.exe (ingen konsol) via kedja:
      1) bredvid sys.executable (även venv) 2) sys.base_prefix
      3) PATH (shutil.which). Används av autostart-kommandot.
  - ✅ _script_path(): robust sökväg till main.pyw – sys.argv[0] om
      det är en befintlig .pyw/.py, annars <projektrot>/main.pyw
      (förra versionen kunde peka fel vid relativ start från annan mapp)
  - ✅ _get_autostart_command()/_get_autostart_args(): använder
      pythonw.exe på Windows → autostart via registret öppnar ALDRIG
      en terminal
  - ✅ Schema-version oförändrad (24) – inga nya nycklar

ÄNDRINGAR mot v24.4:
  - ✅ default_template: str = "" – standardmallen som väljs
      automatiskt vid start (filnamn i Mallar/). Tom = senast valda.
      * get_defaults(): "default_template": ""
      * Valideras som str (str_fields)
      * get_default_template() / set_default_template()
      * Schema-version oförändrad (24) – defaults-merge täcker gamla
        filer (ingen migration krävs)
      * Användaren kan alltid ändra i dropdown-menyn på Skicka-fliken –
        manuella val gäller tills appen startas om

Kvitton (infört i v24.4):
  - ✅ request_receipts: bool = False (default) – standardvärde för
      checkboxen \"Begär leverans- och läskvitto\" i sänddialogen
      * get_defaults(): \"request_receipts\": False
      * Valideras som bool (bool_fields)
      * Schema-version oförändrad (24) – defaults-merge täcker gamla
        filer (ingen migration krävs)

ÄNDRINGAR mot v24.2:
  - ✅ default_to: standard-To-adresser (läggs alltid till i To-listan
      vid start och efter formulärrensning)
      * get_defaults(): "default_to": []
      * Valideras som lista av strängar (samma som default_bcc)
      * get_default_to() / set_default_to()

ÄNDRINGAR mot v24.1:
  - ✅ archive_copy_email: fast e-postadress som ALLTID får en kopia
      (dold Bcc) på varje skickat mail
      * get_defaults(): "archive_copy_email": ""
      * Valideras som str (str_fields)
      * get_archive_copy_email() / set_archive_copy_email()
      * Inga migrationer krävs – default merge täcker gamla filer

ÄNDRINGAR mot v24:
- ✅ SNABBARE: copy-on-write-inställningar
    * ALLA mutationer (set/update/add_recent/clear/…) bygger en ny
      dict och byter referens UNDER lås.
    * ALLA läsningar (get/get_all/get_recent_recipients/…) är
      LÅS-FRIA – dict-access är atomärt i CPython och dict:en muteras
      aldrig på plats efter publicering.
    * get() är den absolut vanligaste operationen (sändning, UI,
      komprimeringscheck) – nu utan RLock per anrop.
- ✅ Korrupt markdown/inklistringssyntax borttagen
  (__init__, __all__, __repr__, __future__, log.info,
   _get_config_dir, _resolve_settings_path, _migrate_and_merge,
   _validate_and_coerce, _get_autostart_command, _get_autostart_args,
   _set_autostart_windows/_macos/_linux,
   attempt.read_text, _dt.datetime.now().isoformat,
   self.is_autostart_enabled, <, <=, >)
- ✅ Schema-version oförändrad (24) – inga nya nycklar, ingen migration
- ✅ default_cc HELT borttagen (migration v22 + validering + spara)

Inställningar sparas i användarspecifik konfigurationskatalog per OS:
- Windows : %APPDATA%\EmailApp\email_settings.json
- macOS   : ~/Library/Application Support/EmailApp/email_settings.json
- Linux   : ~/.config/EmailApp/email_settings.json

Funktioner:
- Atomär skrivning (.tmp → replace) – korrupterar aldrig filen
- Automatisk backup (.bak) vid varje sparande
- Thread-safe: RLock för mutationer, lås-fri läsning (v24.1)
- Automatisk migrering från äldre versioner och gammal sökväg
- Per-version migreringslogik
- Validering av alla inställningsvärden
- Autostart-stöd: Windows (registry), macOS (LaunchAgent), Linux (.desktop)
- Teman: light / dark / system (auto → system vid migration)
- Standardmottagare Bcc (default_bcc)
- Senaste mottagare (recent_recipients, max 50, FIFO)
- Egen e-post alltid med som TO (own_email)
- Reply-To-header (reply_to)
- Placeholder AI-översättning (translate_placeholders)
- Bildkomprimeringsinställningar för bilagor (compress_images,
  preserve_image_dimensions, preserve_image_sharpness,
  image_jpeg_quality, image_png_compress_level)

OBS:
- Fritext ovan signatur är en renderingsregel i mailflödet och hanteras i
  core/email_sender.py / ui/preview.py, inte här.

FIL: core/settings_manager.py
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import platform
import shutil
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import winreg  # type: ignore
    HAS_WINREG = True
except ImportError:
    winreg = None  # type: ignore
    HAS_WINREG = False

try:
    import plistlib
    HAS_PLISTLIB = True
except ImportError:
    plistlib = None  # type: ignore
    HAS_PLISTLIB = False

log = logging.getLogger(__name__)

SETTINGS_FILE_NAME = "email_settings.json"
APP_NAME = "E-postofferten"
LAUNCH_AGENT_ID = "com.emailapp.launch"
DEFAULT_SMTP_PORT = 587
CURRENT_SETTINGS_VERSION = 24
MAX_RECENT_RECIPIENTS = 50
MAX_AUTOSTART_BACKUPS = 10
AUTOSTART_BACKGROUND_FLAG = "--background"

VALID_THEMES = frozenset({"light", "dark", "system", "auto"})
CANONICAL_THEMES = frozenset({"light", "dark", "system"})
VALID_LANGUAGES = frozenset({"sv", "en"})
VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})

IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"
IS_LINUX = not IS_WINDOWS and not IS_MACOS


def get_defaults() -> Dict[str, Any]:
    """Returnerar säkra standardvärden för alla inställningar."""
    return {
        # Metadata
        "settings_version": CURRENT_SETTINGS_VERSION,
        "mode": "prod",
        "smart_cache": True,

        # Autostart & tray
        "startup": False,
        "autostart": False,
        "start_minimized": True,
        "close_to_tray": True,
        "minimize_to_tray": True,

        # Utseende
        "theme": "system",
        # UI-språk (sv/en) – styr core/i18n (v5.4: hela app-skalet)
        "language": "sv",

        # Uppdateringar från GitHub Releases (v5.4) – schema oförändrad
        # (24), defaults-merge täcker gamla filer precis som tidigare
        # nycklar (request_receipts m.fl.).
        "auto_update_check": True,
        "last_update_check": "",

        # Donation (v5.4) – tom = projektets standardlänkar i
        # core/donate.py används. Redigeras under
        # Inställningar → ❤️ Stöd & om.
        "donation_url": "",
        "donation_paypal_url": "",
        "donation_swish": "",

        # Fönster
        "window_geometry": "",

        # Flikar
        "visible_tabs": {
            "tab_template": True,
            "tab_recipients": True,
            "tab_attachments": True,
            "tab_settings": True,
            "tab_contacts": True,
            "tab_preview": True,
            "tab_templates": True,
            "tab_logs": True,
            "tab_history": True,
        },

        # SMTP
        "smtp_server": "",
        "smtp_port": DEFAULT_SMTP_PORT,
        "sender_email": "",
        "sender_name": "",
        "username": "",
        "password": "",
        "use_ssl": False,

        # Egen e-post & reply-to
        "own_email": "",
        "reply_to": "",

        # Arkivkopia – fast adress som alltid får kopia (dold Bcc)
        "archive_copy_email": "",

        # Mallar, språk, placeholders
        "template_dir": "Mallar",
        "address_dir": "adresslistor",
        "word_file_path": "",
        # Standardmall (v24.5) – väljs automatiskt vid start om satt;
        # användaren kan alltid ändra i dropdown-menyn på Skicka-fliken
        "default_template": "",
        "include_english": False,
        "translate_placeholders": True,
        "replacements_values": {},
        "recent_files": [],

                # Sändning
        "validate_recipients": False,
        "skip_invalid_recipients": True,
        "bcc_batch_size": 0,
        "delay_between_batches": 0.5,
        "max_retries": 2,
        "smtp_timeout": 30,
        "generate_html_from_plain": True,

        # Leverans-/läskvitto (v24.4) – standardvärde för checkboxen i
        # sänddialogen. Lägger till Disposition-Notification-To /
        # Return-Receipt-To samt SMTP-DSN (NOTIFY) när servern stödjer det.
        "request_receipts": False,

        # Bildkomprimering för bifogade bilder
        "compress_images": True,
        "preserve_image_dimensions": True,
        "preserve_image_sharpness": True,
        "image_jpeg_quality": 92,
        "image_png_compress_level": 6,

        # Standardmottagare (To + Bcc)
        "default_to": [],
        "default_bcc": [],

        # Senaste mottagare
        "recent_recipients": [],

        # Formulärbeteende
        "clear_form_after_send": True,
        "save_last_recipients": True,

        # Plugins
        "plugin_states": {},

        # Loggning
        "debug_logging": False,
        "log_level": "INFO",
    }


class SettingsManager:
    """Central hanterare för alla programinställningar.

    Trådsäkerhetsmodell (v24.1):
    - Mutationer sker ENBART via copy-on-write under self._lock
      (ny dict byggs och referensen byts – befintlig dict ändras aldrig)
    - Läsningar är lås-fria (dict-access är atomär i CPython)
    - get() är den vanligaste operationen och tar numera inget lås
    """

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self._lock = threading.RLock()
        self.settings_path = self._resolve_settings_path()
        self._data: Dict[str, Any] = self._load()

        log.info(
            "SettingsManager initierad. Fil: %s, Version: %s",
            self.settings_path,
            self._data.get("settings_version"),
        )

    # ------------------------------------------------------------------
    # Sökvägshantering
    # ------------------------------------------------------------------

    def _get_config_dir(self) -> Path:
        """Returnera konfigurationskatalog.

        Portabelt läge (USB / valfri sökväg): EMAILAPP_PORTABLE=1 eller
        filen ``.portable`` bredvid appen → inställningar i <app>/.data
        så sökvägen till appen aldrig spelar roll.
        """
        flag = str(os.getenv("EMAILAPP_PORTABLE", "") or "").strip().lower()
        if flag in {"1", "true", "yes", "on"}:
            return self.base_dir / ".data"
        try:
            if (self.base_dir / ".portable").is_file():
                return self.base_dir / ".data"
        except Exception:
            pass
        if IS_WINDOWS:
            appdata = os.getenv("APPDATA")
            if appdata:
                return Path(appdata) / APP_NAME
            return Path.home() / "AppData" / "Roaming" / APP_NAME

        if IS_MACOS:
            return Path.home() / "Library" / "Application Support" / APP_NAME

        xdg = os.getenv("XDG_CONFIG_HOME", "")
        return Path(xdg) / APP_NAME if xdg else Path.home() / ".config" / APP_NAME

    def _resolve_settings_path(self) -> Path:
        """Bestäm sökväg till inställningsfilen med migration från gammal plats."""
        config_dir = self._get_config_dir()
        new_path = config_dir / SETTINGS_FILE_NAME
        old_path = self.base_dir / SETTINGS_FILE_NAME

        if old_path.exists() and not new_path.exists():
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old_path, new_path)
                log.info("Migrerade inställningar: %s → %s", old_path, new_path)
            except Exception as exc:
                log.warning(
                    "Kunde inte migrera inställningsfil (%s) – använder gammal plats.",
                    exc,
                )
                return old_path

        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            return new_path
        except Exception as exc:
            log.warning(
                "Kunde inte skapa konfigurationskatalog (%s) – faller tillbaka till programrot.",
                exc,
            )
            return old_path

    @property
    def config_dir(self) -> Path:
        return self.settings_path.parent

    @property
    def settings_file_path(self) -> Path:
        return self.settings_path

    # ------------------------------------------------------------------
    # Laddning & migrering
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, Any]:
        """Ladda inställningar från fil, med fallback till .bak och defaults."""
        candidates = [
            self.settings_path,
            self.settings_path.with_suffix(".json.bak"),
        ]

        for attempt in candidates:
            if not attempt.exists():
                continue
            try:
                raw = attempt.read_text(encoding="utf-8-sig")
                data = json.loads(raw)
                if not isinstance(data, dict):
                    log.warning(
                        "Ogiltig struktur i %s – provar nästa kandidat.", attempt
                    )
                    continue
                if attempt != self.settings_path:
                    log.warning("Läste inställningar från backup: %s", attempt)
                return self._migrate_and_merge(data)
            except (json.JSONDecodeError, OSError):
                log.warning(
                    "Kunde inte läsa %s – provar nästa kandidat.",
                    attempt,
                    exc_info=True,
                )

        log.info("Ingen inställningsfil hittades – startar med standardvärden.")
        return get_defaults()

    def _migrate_and_merge(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Migrera äldre inställningar stegvis och slå ihop med defaults."""
        version = int(raw.get("settings_version", 1))
        data = dict(raw)

        if version < 13:
            data.setdefault("start_minimized", True)
            data.setdefault("close_to_tray", True)

        if version < 15:
            data.setdefault("theme", "system")
            data.setdefault("language", "sv")

        if version < 19:
            data.setdefault(
                "visible_tabs",
                {
                    "tab_template": True,
                    "tab_recipients": True,
                    "tab_attachments": True,
                    "tab_settings": True,
                },
            )

        if version < 20:
            data.setdefault("validate_recipients", False)
            data.setdefault("skip_invalid_recipients", True)
            data.setdefault("bcc_batch_size", 0)
            data.setdefault("delay_between_batches", 0.5)
            data.setdefault("max_retries", 2)
            data.setdefault("smtp_timeout", 30)
            data.setdefault("generate_html_from_plain", True)
            data.setdefault("mode", "prod")
            data.setdefault("smart_cache", True)
            data.setdefault("use_ssl", False)
            data.setdefault("startup", False)
            data.setdefault("minimize_to_tray", True)
            data.setdefault("template_dir", "Mallar")
            data.setdefault("address_dir", "adresslistor")
            data.setdefault("recent_files", [])
            data.setdefault("plugin_states", {})

        if version < 21:
            data.setdefault("default_bcc", [])
            data.setdefault("recent_recipients", [])
            data.setdefault("clear_form_after_send", True)
            data.setdefault("save_last_recipients", True)
            tabs = data.setdefault("visible_tabs", {})
            for key in ("tab_contacts", "tab_preview", "tab_templates", "tab_logs"):
                tabs.setdefault(key, True)

        if version < 22:
            if "default_cc" in data:
                removed = data.pop("default_cc")
                log.info(
                    "Migration v22: tog bort default_cc (%d adresser ignoreras)",
                    len(removed) if isinstance(removed, list) else 0,
                )

        if version < 23:
            data.setdefault("own_email", "")
            data.setdefault("reply_to", "")
            data.setdefault("translate_placeholders", True)

        if version < 24:
            data.setdefault("compress_images", True)
            data.setdefault("preserve_image_dimensions", True)
            data.setdefault("preserve_image_sharpness", True)
            data.setdefault("image_jpeg_quality", 92)
            data.setdefault("image_png_compress_level", 6)
            tabs = data.setdefault("visible_tabs", {})
            tabs.setdefault("tab_history", True)

        if data.get("theme") == "auto":
            data["theme"] = "system"
            log.info("Migration: tema 'auto' → 'system'")

        defaults = get_defaults()
        merged = defaults.copy()
        merged.update(data)
        merged.pop("default_cc", None)
        merged = self._validate_and_coerce(merged)
        merged["settings_version"] = CURRENT_SETTINGS_VERSION

        if version != CURRENT_SETTINGS_VERSION:
            log.info(
                "Inställningar migrerade: v%d → v%d",
                version, CURRENT_SETTINGS_VERSION,
            )

        return merged

    def _validate_and_coerce(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validera och typkorrigera alla inställningsvärden."""
        defaults = get_defaults()
        d = dict(data)

        try:
            port = int(d.get("smtp_port", DEFAULT_SMTP_PORT))
            if not (1 <= port <= 65535):
                raise ValueError(f"Port {port} utanför intervall")
            d["smtp_port"] = port
        except (TypeError, ValueError) as exc:
            log.warning(
                "Ogiltig smtp_port (%r) – återställer: %s",
                d.get("smtp_port"), exc,
            )
            d["smtp_port"] = DEFAULT_SMTP_PORT

        bool_fields = [
            "include_english",
            "autostart",
            "startup",
            "close_to_tray",
            "start_minimized",
            "minimize_to_tray",
            "debug_logging",
            "validate_recipients",
            "skip_invalid_recipients",
            "generate_html_from_plain",
            "use_ssl",
            "smart_cache",
            "clear_form_after_send",
            "save_last_recipients",
            "translate_placeholders",
            "compress_images",
            "preserve_image_dimensions",
            "preserve_image_sharpness",
            # v24.4 – leverans-/läskvitto
            "request_receipts",
            # v5.4 – autosökning av GitHub-uppdateringar
            "auto_update_check",
        ]
        for key in bool_fields:
            try:
                d[key] = bool(d.get(key, defaults.get(key, False)))
            except Exception:
                d[key] = defaults.get(key, False)

        # Alltid enligt aktuell design
        d["start_minimized"] = True

        if d.get("startup") and not d.get("autostart"):
            d["autostart"] = True
        elif d.get("autostart") and not d.get("startup"):
            d["startup"] = True

        int_fields: Dict[str, Tuple[int, int, int]] = {
            "bcc_batch_size": (0, 0, 10_000),
            "max_retries": (2, 0, 10),
            "smtp_timeout": (30, 5, 300),
            "image_jpeg_quality": (92, 60, 100),
            "image_png_compress_level": (6, 0, 9),
        }
        for key, (default, lo, hi) in int_fields.items():
            try:
                value = int(d.get(key, default))
                d[key] = max(lo, min(hi, value))
            except (TypeError, ValueError):
                d[key] = default

        float_fields: Dict[str, Tuple[float, float, float]] = {
            "delay_between_batches": (0.5, 0.0, 60.0),
        }
        for key, (default, lo, hi) in float_fields.items():
            try:
                value = float(d.get(key, default))
                d[key] = max(lo, min(hi, value))
            except (TypeError, ValueError):
                d[key] = default

        theme = d.get("theme", "system")
        if theme == "auto":
            theme = "system"
        if theme not in CANONICAL_THEMES:
            log.warning("Ogiltigt tema %r – återställer till 'system'.", theme)
            theme = "system"
        d["theme"] = theme

        if d.get("language") not in VALID_LANGUAGES:
            log.warning(
                "Ogiltigt språk %r – återställer till 'sv'.", d.get("language")
            )
            d["language"] = "sv"

        log_level = str(d.get("log_level", "INFO")).upper()
        d["log_level"] = log_level if log_level in VALID_LOG_LEVELS else "INFO"

        if d.get("mode") not in ("prod", "dev"):
            d["mode"] = "prod"

        default_tabs = defaults["visible_tabs"]
        tabs = d.get("visible_tabs", {})
        if not isinstance(tabs, dict):
            tabs = {}
        for tab_id, default_value in default_tabs.items():
            tabs.setdefault(tab_id, default_value)
        d["visible_tabs"] = tabs

        if not isinstance(d.get("replacements_values"), dict):
            d["replacements_values"] = {}
        if not isinstance(d.get("plugin_states"), dict):
            d["plugin_states"] = {}
        if not isinstance(d.get("recent_files"), list):
            d["recent_files"] = []

        d["own_email"] = str(d.get("own_email") or "").strip()
        d["reply_to"] = str(d.get("reply_to") or "").strip()

        default_to = d.get("default_to", [])
        if not isinstance(default_to, list):
            log.warning("default_to är inte en lista – återställer.")
            default_to = []
        cleaned_to = [
            str(item).strip()
            for item in default_to
            if item and isinstance(item, (str, int, float))
        ]
        d["default_to"] = [item for item in cleaned_to if item]

        default_bcc = d.get("default_bcc", [])
        if not isinstance(default_bcc, list):
            log.warning("default_bcc är inte en lista – återställer.")
            default_bcc = []
        cleaned_bcc = [
            str(item).strip()
            for item in default_bcc
            if item and isinstance(item, (str, int, float))
        ]
        d["default_bcc"] = [item for item in cleaned_bcc if item]
        d.pop("default_cc", None)

        recent = d.get("recent_recipients", [])
        if not isinstance(recent, list):
            log.warning("recent_recipients ogiltig – återställer.")
            recent = []
        clean_recent: List[Dict[str, str]] = []
        for item in recent:
            if isinstance(item, dict) and item.get("email"):
                clean_recent.append(
                    {
                        "email": str(item.get("email", "")).strip(),
                        "name": str(item.get("name", "")).strip(),
                        "last_used": str(item.get("last_used", "")).strip(),
                    }
                )
            elif isinstance(item, str) and item.strip():
                clean_recent.append({
                    "email": item.strip(),
                    "name": "",
                    "last_used": "",
                })
        if len(clean_recent) > MAX_RECENT_RECIPIENTS:
            clean_recent = clean_recent[-MAX_RECENT_RECIPIENTS:]
        d["recent_recipients"] = clean_recent

        str_fields = [
            "smtp_server",
            "sender_email",
            "sender_name",
            "username",
            "password",
            "word_file_path",
            "window_geometry",
            "template_dir",
            "address_dir",
            "archive_copy_email",
            # v24.5 – standardmall (filnamn i Mallar/)
            "default_template",
            # v5.4 – GitHub-uppdatering + donation
            "last_update_check",
            "donation_url",
            "donation_paypal_url",
            "donation_swish",
        ]
        for key in str_fields:
            if d.get(key) is None:
                d[key] = ""
            else:
                d[key] = str(d.get(key))

        return d

    # ------------------------------------------------------------------
    # Publikt API – läsa/skriva inställningar (v24.1: copy-on-write)
    # ------------------------------------------------------------------

    def reload(self) -> None:
        with self._lock:
            self._data = self._load()
        log.info("Inställningar omladdade från disk.")

    def get(self, key: str, default: Any = None) -> Any:
        """Lås-fri läsning (v24.1) – dict-access är atomär i CPython."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Copy-on-write-skrivning: ny dict byggs och referensen byts."""
        with self._lock:
            new_data = dict(self._data)
            new_data[key] = value
            self._data = new_data

    def update_from_dict(self, values: Dict[str, Any]) -> None:
        """Uppdatera flera inställningar från en dict med validering."""
        if not isinstance(values, dict):
            log.warning("update_from_dict: ogiltigt argument: %r", type(values))
            return

        values = {
            key: value for key, value in values.items() if key != "default_cc"
        }
        with self._lock:
            new_data = dict(self._data)
            new_data.update(values)
            self._data = self._validate_and_coerce(new_data)
        log.debug("update_from_dict: uppdaterade %d nycklar.", len(values))

    def get_all(self, *, redact_secrets: bool = False) -> Dict[str, Any]:
        data = dict(self._data)
        if redact_secrets and "password" in data:
            data["password"] = "***"
        return data

    # ------------------------------------------------------------------
    # Egen e-post / reply-to / placeholder-översättning
    # ------------------------------------------------------------------

    def get_own_email(self) -> str:
        return str(self.get("own_email", "")).strip()

    def set_own_email(self, email: str) -> None:
        self.set("own_email", (email or "").strip())

    def get_reply_to(self) -> str:
        reply = str(self.get("reply_to", "")).strip()
        return reply or str(self.get("sender_email", "")).strip()

    def set_reply_to(self, email: str) -> None:
        self.set("reply_to", (email or "").strip())

    def get_archive_copy_email(self) -> str:
        """Returnera fast arkivkopia-adress (tom sträng om ej satt)."""
        return str(self.get("archive_copy_email", "")).strip()

    def set_archive_copy_email(self, email: str) -> None:
        self.set("archive_copy_email", (email or "").strip())

    # ------------------------------------------------------------------
    # UI-språk / GitHub-uppdatering / donation (v5.4)
    # ------------------------------------------------------------------

    def get_ui_language(self) -> str:
        """Valt UI-språk som garanterat "sv" eller "en"."""
        language = str(self.get("language", "sv") or "sv").strip().lower()
        return language if language in VALID_LANGUAGES else "sv"

    def get_donation_url(self) -> str:
        """Inlagd donationslänk (Ko-fi), tom sträng om ej satt."""
        return str(self.get("donation_url", "") or "").strip()

    def set_donation_url(self, url: str) -> None:
        self.set("donation_url", (url or "").strip())

    def get_default_to(self) -> List[str]:
        """Returnera standard-To-adresser (v24.3)."""
        value = self.get("default_to", [])
        return list(value) if isinstance(value, list) else []

    def set_default_to(self, emails: List[str]) -> None:
        self.set(
            "default_to",
            [
                str(email).strip()
                for email in (emails or [])
                if str(email).strip()
            ],
        )

    def should_translate_placeholders(self) -> bool:
        return bool(self.get("translate_placeholders", True))

    # ------------------------------------------------------------------
    # Standardmall (v24.5)
    # ------------------------------------------------------------------

    def get_default_template(self) -> str:
        """Returnera standardmallen (filnamn i Mallar/, tom = av)."""
        return str(self.get("default_template", "") or "").strip()

    def set_default_template(self, name: str) -> None:
        """Sätt standardmallen (tom sträng = av)."""
        self.set("default_template", (name or "").strip())

    # ------------------------------------------------------------------
    # Bildkomprimeringsinställningar
    # ------------------------------------------------------------------

    def should_compress_images(self) -> bool:
        return bool(self.get("compress_images", True))

    def image_compression_settings(self) -> Dict[str, Any]:
        """Returnera samlade inställningar för bildkomprimering.

        Avsikten enligt spec är att bifogade bilder ska behålla skärpa och
        dimensioner, men komprimeras i MB. Själva komprimeringen utförs i
        core/email_sender.py eller närliggande bilageflöde.
        """
        return {
            "compress_images": bool(self.get("compress_images", True)),
            "preserve_image_dimensions": bool(
                self.get("preserve_image_dimensions", True)
            ),
            "preserve_image_sharpness": bool(
                self.get("preserve_image_sharpness", True)
            ),
            "image_jpeg_quality": int(self.get("image_jpeg_quality", 92)),
            "image_png_compress_level": int(
                self.get("image_png_compress_level", 6)
            ),
        }

    # ------------------------------------------------------------------
    # Senaste mottagare
    # ------------------------------------------------------------------

    def add_recent_recipient(self, email: str, name: str = "") -> None:
        email = (email or "").strip()
        if not email:
            return

        with self._lock:
            recent = list(self._data.get("recent_recipients", []))
            recent = [
                item for item in recent
                if isinstance(item, dict) and item.get("email") != email
            ]
            recent.append(
                {
                    "email": email,
                    "name": (name or "").strip(),
                    "last_used": _dt.datetime.now().isoformat(
                        timespec="seconds"
                    ),
                }
            )
            if len(recent) > MAX_RECENT_RECIPIENTS:
                recent = recent[-MAX_RECENT_RECIPIENTS:]
            new_data = dict(self._data)
            new_data["recent_recipients"] = recent
            self._data = new_data

        log.debug("add_recent_recipient: %s (%d totalt)", email, len(recent))

    def get_recent_recipients(self) -> List[Dict[str, str]]:
        return list(self._data.get("recent_recipients", []))

    def clear_recent_recipients(self) -> None:
        with self._lock:
            new_data = dict(self._data)
            new_data["recent_recipients"] = []
            self._data = new_data
        log.info("Senaste mottagare rensade.")

    # ------------------------------------------------------------------
    # Spara
    # ------------------------------------------------------------------

    def save(self) -> bool:
        """Spara alla inställningar atomärt till disk."""
        with self._lock:
            try:
                self.settings_path.parent.mkdir(parents=True, exist_ok=True)

                if self.settings_path.exists():
                    try:
                        shutil.copy2(
                            self.settings_path,
                            self.settings_path.with_suffix(".json.bak"),
                        )
                    except OSError as exc:
                        log.warning("Kunde inte skapa backup: %s", exc)

                self._data["settings_version"] = CURRENT_SETTINGS_VERSION
                self._data.pop("default_cc", None)

                tmp = self.settings_path.with_suffix(".json.tmp")
                wrote_ok = False
                try:
                    tmp.write_text(
                        json.dumps(
                            self._data,
                            indent=4,
                            ensure_ascii=False,
                            sort_keys=False,
                        ),
                        encoding="utf-8",
                    )
                    tmp.replace(self.settings_path)
                    wrote_ok = True
                except OSError:
                    log.exception("Kunde inte skriva inställningsfil")
                    return False
                finally:
                    if not wrote_ok and tmp.exists():
                        try:
                            tmp.unlink()
                        except OSError:
                            pass

                try:
                    self.settings_path.chmod(0o600)
                except OSError:
                    pass

                log.debug("Inställningar sparade: %s", self.settings_path)
                return True
            except Exception:
                log.exception("Oväntat fel vid sparande")
                return False

    # ------------------------------------------------------------------
    # Autostart (v24.7 – stale_console + verify-after-write)
    # ------------------------------------------------------------------

    def _script_path(self) -> Path:
        """Projektets huvudskript (main.pyw) – robust sökväg.

        Prioritet:
          1. sys.argv[0] om det är en .pyw/.py-fil som finns
             (fungerar vid dubbelklick, py-launcher och registry-start)
          2. <projektrot>/main.pyw (härlett från denna fil)
        """
        try:
            argv0 = Path(sys.argv[0]).resolve()
            if argv0.suffix.lower() in (".pyw", ".py") and argv0.exists():
                return argv0
        except Exception:
            pass
        return Path(__file__).resolve().parents[1] / "main.pyw"

    def _vbs_launcher_path(self) -> Path:
        """Starta EmailApp.vbs – dubbelklick-lanserare utan terminal."""
        return self.base_dir / "Starta EmailApp.vbs"

    def _find_pythonw(self) -> Optional[str]:
        """Hitta pythonw.exe på Windows (ingen konsol).

        Sökkedja (v24.7):
          1. bredvid sys.executable (python.exe → pythonw.exe, även venv)
          2. sys.base_prefix / sys.prefix (basinstallationen)
          3. %LOCALAPPDATA%\\Programs\\Python\\Python3*\\pythonw.exe
          4. PATH (shutil.which pythonw.exe)

        Returns:
            Sökväg till pythonw.exe eller None om den inte hittas.
        """
        seen: set = set()
        candidates: List[Path] = []
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
                resolved = str(candidate)
                if resolved in seen:
                    continue
                seen.add(resolved)
                if candidate.is_file():
                    return resolved
            except Exception:
                continue
        try:
            found = shutil.which("pythonw.exe")
            if found:
                return found
        except Exception:
            pass
        return None

    @staticmethod
    def _norm_cmd(cmd: str) -> str:
        """Normalisera ett autostart-kommando för jämförelse."""
        text = (cmd or "").replace('"', "").replace("'", "")
        return " ".join(text.strip().lower().split())

    def _uses_console_python(self, cmd: str) -> bool:
        """True om kommandot startar python.exe (konsolblink) – inte pythonw."""
        low = self._norm_cmd(cmd)
        if not low:
            return False
        if "pythonw.exe" in low or "pythonw " in low or low.endswith("pythonw"):
            return False
        if "wscript.exe" in low or "pyw.exe" in low:
            return False
        tokens = low.replace("\\", "/").split()
        for token in tokens:
            name = token.rsplit("/", 1)[-1]
            if name in {"python.exe", "python", "py.exe", "py"}:
                return True
        return False

    def _command_paths_ok(self, cmd: str) -> bool:
        """True om citerade sökvägar i kommandot finns på disk (best-effort)."""
        if not cmd:
            return False
        parts: List[str] = []
        buf = ""
        in_quote = False
        for ch in cmd:
            if ch == '"':
                if in_quote:
                    parts.append(buf)
                    buf = ""
                    in_quote = False
                else:
                    in_quote = True
                continue
            if in_quote:
                buf += ch
        for part in parts:
            p = Path(part)
            if ("\\" in part or "/" in part) and p.suffix.lower() in {
                ".exe", ".pyw", ".py", ".vbs", ".bat",
            }:
                try:
                    if not p.exists():
                        return False
                except Exception:
                    return False
        return True

    def _get_autostart_command(self) -> str:
        """Kommando som skrivs till OS-autostart (ingen konsol)."""
        script = self._script_path()
        flag = AUTOSTART_BACKGROUND_FLAG
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}" {flag}'
        if IS_WINDOWS:
            vbs = self._vbs_launcher_path()
            try:
                if vbs.is_file():
                    return f'wscript.exe //B //nologo "{vbs}" {flag}'
            except Exception:
                pass
            runner = self._find_pythonw() or sys.executable
            return f'"{runner}" "{script}" {flag}'
        return f'"{sys.executable}" "{script}" {flag}'

    def _get_autostart_args(self) -> List[str]:
        script = self._script_path()
        flag = AUTOSTART_BACKGROUND_FLAG
        if getattr(sys, "frozen", False):
            return [sys.executable, flag]
        if IS_WINDOWS:
            vbs = self._vbs_launcher_path()
            try:
                if vbs.is_file():
                    return ["wscript.exe", "//B", "//nologo", str(vbs), flag]
            except Exception:
                pass
            runner = self._find_pythonw() or sys.executable
            return [runner, str(script), flag]
        return [sys.executable, str(script), flag]

    def _run_key_path(self) -> str:
        return r"Software\Microsoft\Windows\CurrentVersion\Run"

    def _read_run_value(self) -> Optional[str]:
        """Läs EmailApp-värdet i HKCU Run. None = saknas."""
        if not HAS_WINREG or winreg is None:
            return None
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, self._run_key_path(), 0, winreg.KEY_READ
            ) as key:
                try:
                    value, _typ = winreg.QueryValueEx(key, APP_NAME)
                    return str(value) if value is not None else ""
                except FileNotFoundError:
                    return None
        except OSError:
            return None

    def _list_run_conflicts(self) -> List[Dict[str, str]]:
        """Andra produkters Run-poster (läs-only – rörs aldrig)."""
        conflicts: List[Dict[str, str]] = []
        if not HAS_WINREG or winreg is None:
            return conflicts
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, self._run_key_path(), 0, winreg.KEY_READ
            ) as key:
                index = 0
                while True:
                    try:
                        name, value, _typ = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    index += 1
                    if str(name) == APP_NAME:
                        continue
                    text = str(value or "")
                    low = text.lower()
                    if "emailapp" in low or "main.pyw" in low:
                        conflicts.append({"name": str(name), "value": text})
        except OSError:
            pass
        return conflicts

    def _backup_run_value(self, value: Optional[str]) -> None:
        """Spara tidigare Run-värde (roterad, max MAX_AUTOSTART_BACKUPS)."""
        if not value:
            return
        path = self.config_dir / "autostart_run_backup.json"
        try:
            entries: List[Dict[str, str]] = []
            if path.exists():
                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(raw, list):
                        entries = [e for e in raw if isinstance(e, dict)]
                except Exception:
                    entries = []
            entries.append(
                {
                    "ts": _dt.datetime.now().isoformat(timespec="seconds"),
                    "value": value,
                }
            )
            entries = entries[-MAX_AUTOSTART_BACKUPS:]
            path.write_text(
                json.dumps(entries, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            log.debug("Kunde inte spara autostart-backup", exc_info=True)

    def classify_autostart(self) -> str:
        """Klassificera OS-autostartposten.

        Returnerar en av:
          missing | correct | stale_console | stale_path | stale_args | different
        """
        expected = self._norm_cmd(self._get_autostart_command())
        if IS_WINDOWS and HAS_WINREG:
            current = self._read_run_value()
            if current is None:
                return "missing"
            norm = self._norm_cmd(current)
            if norm == expected:
                return "correct"
            if self._uses_console_python(current):
                return "stale_console"
            if not self._command_paths_ok(current):
                return "stale_path"
            if AUTOSTART_BACKGROUND_FLAG not in current.lower():
                return "stale_args"
            return "different"
        if IS_MACOS:
            plist_path = (
                Path.home() / "Library" / "LaunchAgents" / f"{LAUNCH_AGENT_ID}.plist"
            )
            if not plist_path.exists():
                return "missing"
            try:
                if HAS_PLISTLIB and plistlib is not None:
                    with open(plist_path, "rb") as handle:
                        data = plistlib.load(handle)
                    args = [str(a) for a in data.get("ProgramArguments", [])]
                    joined = " ".join(args)
                    if self._uses_console_python(joined):
                        return "stale_console"
                    if AUTOSTART_BACKGROUND_FLAG not in joined:
                        return "stale_args"
                    if self._norm_cmd(joined) == self._norm_cmd(
                        " ".join(self._get_autostart_args())
                    ):
                        return "correct"
                    return "different"
            except Exception:
                return "different"
            return "correct"
        desktop = Path.home() / ".config" / "autostart" / f"{APP_NAME}.desktop"
        if not desktop.exists():
            return "missing"
        try:
            text = desktop.read_text(encoding="utf-8")
        except Exception:
            return "different"
        exec_line = ""
        for line in text.splitlines():
            if line.startswith("Exec="):
                exec_line = line[5:]
                break
        if self._uses_console_python(exec_line):
            return "stale_console"
        if AUTOSTART_BACKGROUND_FLAG not in exec_line:
            return "stale_args"
        if self._norm_cmd(exec_line) == expected:
            return "correct"
        return "different"

    def get_autostart_info(self) -> Dict[str, Any]:
        """Diagnostik för autostart (UI/logg). Rör aldrig andras poster."""
        classification = self.classify_autostart()
        info: Dict[str, Any] = {
            "wanted": bool(self.get("autostart", False)),
            "os_enabled": self.is_autostart_enabled(),
            "classification": classification,
            "command": self._get_autostart_command(),
            "pythonw": self._find_pythonw() if IS_WINDOWS else sys.executable,
            "script": str(self._script_path()),
            "vbs": str(self._vbs_launcher_path()),
            "conflicts": self._list_run_conflicts() if IS_WINDOWS else [],
        }
        if IS_WINDOWS:
            info["current"] = self._read_run_value()
        return info

    def set_autostart(self, enable: bool) -> bool:
        try:
            if IS_WINDOWS:
                ok = self._set_autostart_windows(enable)
            elif IS_MACOS:
                ok = self._set_autostart_macos(enable)
            else:
                ok = self._set_autostart_linux(enable)

            if ok:
                with self._lock:
                    new_data = dict(self._data)
                    new_data["autostart"] = enable
                    new_data["startup"] = enable
                    self._data = new_data
            return ok
        except Exception:
            log.exception("Kunde inte ändra autostart")
            return False

    def _set_autostart_windows(self, enable: bool) -> bool:
        if not HAS_WINREG or winreg is None:
            log.warning("winreg saknas – kan inte sätta autostart.")
            return False

        existing = self._read_run_value()
        self._backup_run_value(existing)

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self._run_key_path(),
                0,
                winreg.KEY_ALL_ACCESS,
            )
            try:
                if enable:
                    cmd = self._get_autostart_command()
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                    written = None
                    try:
                        written, _typ = winreg.QueryValueEx(key, APP_NAME)
                    except OSError:
                        written = None
                    if self._norm_cmd(str(written or "")) != self._norm_cmd(cmd):
                        log.warning(
                            "Autostart verify-after-write misslyckades: skrev %r läste %r",
                            cmd,
                            written,
                        )
                        return False
                    log.info("Autostart aktiverat (Windows): %s", cmd)
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                        log.info("Autostart inaktiverat (Windows).")
                    except FileNotFoundError:
                        pass
            finally:
                key.Close()
            return True
        except OSError:
            log.exception("Registret – autostart")
            return False

    def _set_autostart_macos(self, enable: bool) -> bool:
        if not HAS_PLISTLIB or plistlib is None:
            log.warning("plistlib saknas – kan inte sätta autostart.")
            return False

        agents_dir = Path.home() / "Library" / "LaunchAgents"
        plist_path = agents_dir / f"{LAUNCH_AGENT_ID}.plist"
        try:
            if enable:
                agents_dir.mkdir(parents=True, exist_ok=True)
                log_dir = self.base_dir / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                plist: Dict[str, Any] = {
                    "Label": LAUNCH_AGENT_ID,
                    "ProgramArguments": self._get_autostart_args(),
                    "RunAtLoad": True,
                    "KeepAlive": False,
                    "WorkingDirectory": str(self.base_dir),
                    "StandardOutPath": str(log_dir / "launch_stdout.log"),
                    "StandardErrorPath": str(log_dir / "launch_stderr.log"),
                }
                with open(plist_path, "wb") as handle:
                    plistlib.dump(plist, handle)
                log.info("Autostart aktiverat (macOS): %s", plist_path)
            else:
                if plist_path.exists():
                    plist_path.unlink()
                log.info("Autostart inaktiverat (macOS).")
            return True
        except OSError:
            log.exception("LaunchAgent – autostart")
            return False

    def _set_autostart_linux(self, enable: bool) -> bool:
        autostart_dir = Path.home() / ".config" / "autostart"
        desktop_path = autostart_dir / f"{APP_NAME}.desktop"
        try:
            if enable:
                autostart_dir.mkdir(parents=True, exist_ok=True)
                cmd = self._get_autostart_command()
                content = (
                    "[Desktop Entry]\n"
                    "Type=Application\n"
                    f"Name={APP_NAME}\n"
                    f"Exec={cmd}\n"
                    "Terminal=false\n"
                    "Hidden=false\n"
                    "NoDisplay=false\n"
                    "X-GNOME-Autostart-enabled=true\n"
                    f"Comment=Starta {APP_NAME} vid inloggning\n"
                )
                desktop_path.write_text(content, encoding="utf-8")
                try:
                    desktop_path.chmod(0o755)
                except OSError:
                    pass
                # verify-after-write
                try:
                    read_back = desktop_path.read_text(encoding="utf-8")
                    if f"Exec={cmd}" not in read_back:
                        log.warning("Autostart verify-after-write (Linux) misslyckades.")
                        return False
                except OSError:
                    return False
                log.info("Autostart aktiverat (Linux): %s", desktop_path)
            else:
                if desktop_path.exists():
                    desktop_path.unlink()
                log.info("Autostart inaktiverat (Linux).")
            return True
        except OSError:
            log.exception("Desktop-fil – autostart")
            return False

    def is_autostart_enabled(self) -> bool:
        try:
            if IS_WINDOWS and HAS_WINREG and winreg is not None:
                return self._read_run_value() is not None
            if IS_MACOS:
                return (
                    Path.home() / "Library" / "LaunchAgents"
                    / f"{LAUNCH_AGENT_ID}.plist"
                ).exists()
            return (
                Path.home() / ".config" / "autostart" / f"{APP_NAME}.desktop"
            ).exists()
        except Exception:
            log.exception("Kunde inte kontrollera autostart")
            return False

    def sync_autostart(self) -> bool:
        """Synka OS-autostart mot settings. Reparera stale_console automatiskt."""
        enable = bool(self.get("autostart", False))
        classification = self.classify_autostart()
        os_enabled = classification != "missing"
        needs_repair = enable and classification in {
            "stale_console",
            "stale_path",
            "stale_args",
            "different",
        }
        if enable != os_enabled or needs_repair:
            log.info(
                "Synkroniserar autostart: inställning=%s, klass=%s",
                enable,
                classification,
            )
            return self.set_autostart(enable)
        return True

    def apply_autostart_preference(self) -> bool:
        return self.sync_autostart()

    # ------------------------------------------------------------------
    # Systeminfo
    # ------------------------------------------------------------------

    def system_info(self) -> Dict[str, str]:
        return {
            "app_name": APP_NAME,
            "settings_version": str(CURRENT_SETTINGS_VERSION),
            "settings_file": str(self.settings_path),
            "config_dir": str(self.config_dir),
            "base_dir": str(self.base_dir),
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "autostart_enabled": str(self.is_autostart_enabled()),
            "autostart_class": self.classify_autostart(),
            "theme": str(self.get("theme", "system")),
            "language": str(self.get("language", "sv")),
            "mode": str(self.get("mode", "prod")),
            "own_email": self.get_own_email(),
            "reply_to": self.get_reply_to(),
            "translate_placeholders": str(self.should_translate_placeholders()),
            "compress_images": str(self.should_compress_images()),
        }

    def __repr__(self) -> str:
        return (
            f"SettingsManager(path={str(self.settings_path)!r}, "
            f"version={self._data.get('settings_version')})"
        )


__all__ = [
    "SettingsManager",
    "APP_NAME",
    "SETTINGS_FILE_NAME",
    "CURRENT_SETTINGS_VERSION",
    "DEFAULT_SMTP_PORT",
    "MAX_RECENT_RECIPIENTS",
    "VALID_THEMES",
    "CANONICAL_THEMES",
    "VALID_LANGUAGES",
    "VALID_LOG_LEVELS",
    "get_defaults",
]
