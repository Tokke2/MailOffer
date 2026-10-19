#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modul för att skicka e-post via SMTP.

Version: 3.10 – VIN ENDAST I ENGELSK VERSION

ÄNDRINGAR mot v3.9:
  - ✅ Platshållaren ::vin:: skickas BARA i EN-versionen
      (plockas bort ur SV-replacements)
  - ✅ Tom VIN → VIN-raden tas bort ur engelska mailet

ÄNDRINGAR mot v3.8:
  - ✅ Nya parametrar recipients_to_lang / recipients_bcc_lang:
      Dict {e-post: "sv"|"en"} – språk PER mottagare
      * "sv"-mottagare får ENBART svensk version av mailet
      * "en"-mottagare får ENBART engelsk version
      * Gäller även när include_english=True (SV får aldrig engelsk)
      * include_english=False → alla får svensk version (som förut)
      * Saknad nyckel/annat värde → "sv" · Utan dicts = exakt som förut
  - ✅ Mallen parsas per språk (endast språk som används – ingen
      onödig dubbelparsning när alla är SV)
  - ✅ Placeholder-översättning sker endast för EN-gruppen
  - ✅ Batchar: to_sv/to_en/bcc_sv/bcc_en (Bcc-batchning per språk)
      med tydliga etiketter i progress/logg
  - ✅ SendResult: recipients_sv, recipients_en, had_language_split
      + rad i summary() ("🌐 Språk: SV n · EN n")
  - ✅ To-headern visar rätt språkgrupps synliga mottagare

ÄNDRINGAR mot v3.7.1:
  - ✅ Ny parameter request_receipts: bool = False (sista keyword-param):
      * True → headers läggs till i mailet:
        - Disposition-Notification-To: <avsändare>   (läskvitto, RFC 3798
          – Outlook visar "leverera läskvitto"-fråga)
        - Return-Receipt-To: <avsändare>             (stöds av många
          servrar/klienter som leverans-/läskvitto)
      * True → SMTP-DSN (RFC 3461) begärs via rcpt_options
        NOTIFY=SUCCESS,FAILURE för leveranskvitto – MEN endast om
        servern annonserar DSN i EHLO (esmtp_features)
      * Fail-safe: om servern trots allt nekar mottagaren med
        DSN-optionen görs ett nytt försök UTAN DSN (mailet skickas
        alltid ändå – kvitto är aldrig ett skäl att misslyckas)
      * SendResult.receipts_requested sätts till True
  - ✅ Bakåtkompatibel: request_receipts=False är default – alla
    gamla anrop fungerar oförändrat
  - ✅ build_message() får request_receipts-parametern (headers)

ÄNDRINGAR mot v3.7:
  - ✅ Om INGEN bilaga är en bild (enbart PDF/dokument/övriga filer)
      görs INGENTING:
      * send_email() startar inte komprimeringsflödet (guard innan
        _compress_attachments)
      * _compress_attachments() returnerar direkt – ingen temp-katalog
        skapas, ingen loggning
  - ✅ Tidigare skapades en TemporaryDirectory + iteration även när
      bilagorna saknade bilder (onödigt arbete + loggbrus)

ÄNDRINGAR mot v3.6:
  - ✅ Nya parametrar (matchar SettingsManager v24 + SendWorker):
      * preserve_image_dimensions: bool = True
          → True:  behåll pixelstorleken, komprimera bara filstorleken
          → False: skala ner stora bilder (max 1920px längsta sida)
      * preserve_image_sharpness: bool = True
          → True:  SmoothTransformation / LANCZOS
          → False: FastTransformation / BILINEAR (snabbare)
      * image_jpeg_quality: int = 92   (kvalitet 0-100)
      * image_png_compress_level: int = 6  (0-9)
  - ✅ Komprimeringsinställningar trådas genom hela kedjan
      (_compress_attachments → _compress_single_image →
       _compress_with_qimage / _compress_with_pillow)
  - ✅ Bakåtkompatibel: alla nya parametrar har defaults – gamla anrop
      fungerar oförändrat

ÄNDRINGAR mot v3.5:
  - ✅ compress_images: komprimerar bildbilagor innan sändning
      * Skalar ner bilder vars längsta sida överstiger MAX_IMAGE_DIMENSION
      * Omsparar med kvalitet (JPEG / PNG / WEBP)
      * Om komprimerad fil inte blir mindre → originalet behålls
      * Animerade GIF:er rörs aldrig
      * Gör INGET om parametern är False eller om inga bilder finns
      * Komprimering via PyQt6.QtGui.QImage (finns i appen), fallback: Pillow
  - ✅ SendResult.images_compressed (antal komprimerade bilder)
  - ✅ Temporära komprimerade filer rensas efter sändning (atexit-säkerhet)

ÄNDRINGAR mot v3.4:
  - ✅ own_email: egen adress alltid först i TO-listan
  - ✅ reply_to: defaultar till sender_email om ej satt
  - ✅ translate_placeholders: AI-översätter värden vid engelsk utdata
  - ✅ _translate_placeholder_values() med fast mappning + deep_translator
  - ✅ merge_recipients() accepterar own_email

Funktioner:
  - Mallbaserat innehåll via parse_subject_and_body
  - Bilagor (bilder/filer) med MIME-detektering
  - To/Bcc-mottagare med deduplicering
  - Flerspråkighet ([en]-block)
  - STARTTLS/SSL autodetektering
  - Retry med exponentiell backoff och reconnect
  - Validering av e-postadresser
  - BCC-batchning med throttling
  - Alternativ MIME (text + HTML)
  - Reply-To och extra headers
  - Progressrapportering via callback
  - Dry-run-läge för testning
  - Detaljerad sändningsstatistik (SendResult)
  - Fritext appendas till brödtexten
  - Standardmottagare (default_bcc) via merge_recipients()
  - Egen e-post alltid med som TO (own_email)
  - Placeholder AI-översättning vid include_english

FIL: core/email_sender.py
"""

from __future__ import annotations

import atexit
import html as html_module
import logging
import mimetypes
import re
import smtplib
import ssl
import tempfile
import time
from dataclasses import dataclass, field
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from script.templates import parse_subject_and_body

log = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────────────────
# Valfri förbättrad validering
# ───────────────────────────────────────────────────────────────────────────
try:
    from email_validator import (  # type: ignore
        validate_email as ev_validate_email,
        EmailNotValidError,
    )
    HAS_EMAIL_VALIDATOR = True
except Exception:
    ev_validate_email   = None
    EmailNotValidError  = Exception
    HAS_EMAIL_VALIDATOR = False

# ═══════════════════════════════════════════════════════════════════════════
# Konstanter
# ═══════════════════════════════════════════════════════════════════════════
USER_AGENT = "EmailApp/3.8"

SIMPLE_EMAIL_RE = re.compile(
    r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$",
    re.IGNORECASE,
)

MAX_ATTACHMENT_SIZE_MB   = 25
MAX_TOTAL_ATTACHMENTS_MB = 50

# ── Bildkomprimering (v3.6) ─────────────────────────────────────────────
IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif",
    ".bmp", ".webp", ".tif", ".tiff",
}

# Längsta sida (px) efter nerskalning. Större bilder skalas ner.
MAX_IMAGE_DIMENSION = 1920

# Kvalitet vid omskrivning (0–100).
IMAGE_JPEG_QUALITY = 82
IMAGE_PNG_LEVEL    = 75
IMAGE_WEBP_QUALITY = 80

# Bilder mindre än detta (bytes) rörs inte – inget att vinna.
MIN_IMAGE_SIZE_TO_COMPRESS = 100 * 1024  # 100 KB

# ── Fast mappning för kända placeholder-värden (sv → en) ──────────────
GLASS_TYPE_MAP: Dict[str, str] = {
    "Vindruta": "Windshield",
    "Bakruta": "Rear window",
    "Höger sidoruta fram": "Front right side window",
    "Vänster sidoruta fram": "Front left side window",
    "Höger sidoruta bak": "Rear right side window",
    "Vänster sidoruta bak": "Rear left side window",
    "Höger ventilationsruta": "Front right vent window",
    "Vänster ventilationsruta": "Front left vent window",
    "Höger kvarts-/hörn-ruta": "Right quarter/corner window",
    "Vänster kvarts-/hörn-ruta": "Left quarter/corner window",
    "Taklucka / Panoramatak": "Sunroof / Panoramic roof",
    "Vindruteglas (laminerad)": "Windshield glass (laminated)",
    "Vindruteglas (härdad)": "Windshield glass (tempered)",
}

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                 Roboto, 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #333333;
    max-width: 680px;
    margin: 0 auto;
    padding: 16px;
  }}
  p {{ margin: 0 0 12px 0; }}
  .free-text {{
    border-top: 1px solid #DDDDDD;
    margin-top: 16px;
    padding-top: 12px;
    color: #555555;
    font-style: italic;
  }}
</style>
</head>
<body>
{body}
</body>
</html>
"""

# ═══════════════════════════════════════════════════════════════════════════
# Undantag
# ═══════════════════════════════════════════════════════════════════════════
class EmailSendConfigError(Exception):
    """Fel i konfiguration/parametrar inför e-postsändning."""


class EmailSendError(Exception):
    """Fel under själva sändningen (SMTP, nätverk, etc.)."""


class EmailValidationError(EmailSendConfigError):
    """Specifikt fel vid e-postvalidering."""

    def __init__(
        self,
        message:        str,
        invalid_emails: List[str],
    ) -> None:
        super().__init__(message)
        self.invalid_emails = invalid_emails


# ═══════════════════════════════════════════════════════════════════════════
# Dataklasser
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class SendResult:
    """Detaljerat resultat av en e-postsändning."""

    success:           bool       = False
    subject:           str        = ""
    total_recipients:  int        = 0
    batches_sent:      int        = 0
    batches_total:     int        = 0
    recipients_to:     int        = 0
    recipients_bcc:    int        = 0
    attachments_count: int        = 0
    elapsed_seconds:   float      = 0.0
    errors:            List[str]  = field(default_factory=list)
    warnings:          List[str]  = field(default_factory=list)
    invalid_emails:    List[str]  = field(default_factory=list)
    dry_run:           bool       = False
    had_free_text:     bool       = False
    had_translation:   bool       = False
    had_bcc:           bool       = False
    had_placeholder_translation: bool = False
    # v3.6 – antal bilder som komprimerades inför sändning
    images_compressed: int        = 0
    # v3.8 – leverans-/läskvitto begärt
    receipts_requested: bool      = False
    # v3.9 – språkgrupperade mottagare (SV/EN)
    recipients_sv: int            = 0
    recipients_en: int            = 0
    had_language_split: bool      = False

    @property
    def ok(self) -> bool:
        """True om sändningen lyckades utan kritiska fel."""
        return self.success and not self.errors

    def summary(self) -> str:
        """Sammanfattande text för GUI/logg."""
        status = "✅ Lyckades" if self.success else "❌ Misslyckades"
        lines  = [
            status,
            f"Ämne: {self.subject}",
            (
                f"Mottagare: {self.total_recipients} "
                f"(To: {self.recipients_to}, "
                f"Bcc: {self.recipients_bcc})"
            ),
            f"Batchar: {self.batches_sent}/{self.batches_total}",
            f"Bilagor: {self.attachments_count}",
            f"Tid: {self.elapsed_seconds:.1f}s",
        ]
        if self.dry_run:
            lines.insert(1, "⚠️ DRY RUN – inget skickades")
        if self.had_free_text:
            lines.append("💬 Fritext bifogad")
        if self.had_translation:
            lines.append("🌐 Auto-översatt till engelska")
        if self.had_placeholder_translation:
            lines.append("🤖 Placeholder-värden AI-översatta")
        if self.images_compressed:
            lines.append(
                f"🖼️ {self.images_compressed} bilder komprimerades"
            )
        if self.had_bcc:
            lines.append("🔒 Bcc-mottagare inkluderade")
        if self.receipts_requested:
            lines.append("📨 Leverans-/läskvitto begärt")
        if self.had_language_split:
            lines.append(
                f"🌐 Språk: SV {self.recipients_sv} · EN {self.recipients_en}"
            )
        if self.warnings:
            lines.append(f"\nVarningar ({len(self.warnings)}):")
            for w in self.warnings[:10]:
                lines.append(f"  ⚠️ {w}")
        if self.errors:
            lines.append(f"\nFel ({len(self.errors)}):")
            for e in self.errors[:10]:
                lines.append(f"  ❌ {e}")
        if self.invalid_emails:
            lines.append(
                f"\nOgiltiga adresser: "
                f"{', '.join(self.invalid_emails[:10])}"
            )
        return "\n".join(lines)


ProgressCallback = Optional[Callable[[int, int, str], None]]


# ═══════════════════════════════════════════════════════════════════════════
# Hjälpfunktioner
# ═══════════════════════════════════════════════════════════════════════════
def _translate_placeholder_values(
    replacements:       Dict[str, str],
    include_english:    bool,
    translate_ph:       bool,
) -> Dict[str, str]:
    """
    Översätt placeholder-värden till engelska.

    Hybrid-modell:
      - Kända värden (glastyper) → fast mappning (ögonblicklig)
      - Okända värden → deep_translator (Google Translate gratis)
      - Vid fel → ursprungsvärdet behålls

    Args:
        replacements:     Dict med placeholder-nycklar och värden
        include_english:  Om engelsk version ska inkluderas
        translate_ph:     Om placeholder-översättning är aktiverad

    Returns:
        Dict med översatta värden (oförändrat om villkor ej uppfyllda)
    """
    if not (include_english and translate_ph):
        return replacements
    if not replacements:
        return replacements

    translated: Dict[str, str] = {}
    for key, value in replacements.items():
        if not value:
            translated[key] = value
            continue

        # 1. Fast mappning för kända glastyper
        if value in GLASS_TYPE_MAP:
            translated[key] = GLASS_TYPE_MAP[value]
            log.debug("Placeholder '%s': fast mappning '%s' → '%s'",
                      key, value, translated[key])
            continue

        # 2. AI-översättning via deep_translator
        try:
            from deep_translator import GoogleTranslator
            _translator = GoogleTranslator(source="sv", target="en")
            result = _translator.translate(value)
            if result and result.strip():
                translated[key] = result.strip()
                log.debug("Placeholder '%s': AI-översatt '%s' → '%s'",
                          key, value, translated[key])
            else:
                translated[key] = value
        except ImportError:
            log.warning(
                "deep_translator saknas – placeholder-värde '%s' "
                "översätts ej (behåller original: '%s')",
                key, value,
            )
            translated[key] = value
        except Exception as exc:
            log.warning(
                "Kunde inte översätta placeholder '%s' (%s): %s – "
                "behåller original",
                key, value, exc,
            )
            translated[key] = value

    log.info("Placeholder AI-översättning: %d fält bearbetade",
             len(translated))
    return translated


def _strip_vin_from_swedish(text: str) -> str:
    """Ta bort VIN-rader ur svensk brödtext (VIN är EN-only)."""
    if not text:
        return text
    kept: List[str] = []
    for line in text.splitlines():
        low = line.strip().lower()
        if "::vin::" in low:
            continue
        if re.match(r"^vin\s*:", low):
            continue
        if re.match(r"^vin number\s*:", low):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def _strip_empty_vin_line(text: str, vin: str) -> str:
    """Om VIN är tom, ta bort VIN-raden ur engelska mailet."""
    if not text:
        return text
    if str(vin or "").strip():
        return text
    kept: List[str] = []
    for line in text.splitlines():
        low = line.strip().lower()
        if "::vin::" in low:
            continue
        if re.match(r"^vin\s*:\s*$", low):
            continue
        if re.match(r"^vin number\s*:\s*$", low):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def dedupe_preserve_order(emails: List[str]) -> List[str]:
    """Deduplicera e-postadresser case-insensitivt, bevara ordning."""
    seen:   set = set()
    result: List[str] = []
    for e in emails or []:
        if not e:
            continue
        key = e.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(e.strip())
    return result


def validate_email_address(email: str) -> bool:
    """Validera enskild e-postadress."""
    if not email or "@" not in email:
        return False
    e = email.strip()
    if HAS_EMAIL_VALIDATOR and ev_validate_email:
        try:
            ev_validate_email(e, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False
    return bool(SIMPLE_EMAIL_RE.match(e))


def validate_email_list(
    emails:       List[str],
    *,
    validate:     bool,
    skip_invalid: bool,
) -> Tuple[List[str], List[str]]:
    """Validera en lista med e-postadresser."""
    if not validate:
        return (
            [e.strip() for e in emails if e and e.strip()],
            [],
        )

    valid:   List[str] = []
    invalid: List[str] = []
    for addr in emails:
        if not addr:
            continue
        a = addr.strip()
        if validate_email_address(a):
            valid.append(a)
        else:
            invalid.append(a)

    if invalid:
        if skip_invalid:
            log.warning(
                "Filtrerade bort %d ogiltiga e-postadresser: %s",
                len(invalid), invalid,
            )
        else:
            raise EmailValidationError(
                f"Ogiltiga e-postadresser: {invalid}",
                invalid_emails=invalid,
            )
    return valid, invalid


def chunk_list(lst: List[str], size: int) -> List[List[str]]:
    """Dela en lista i bitar av angiven storlek."""
    if size <= 0:
        return [lst] if lst else []
    return [lst[i: i + size] for i in range(0, len(lst), size)]


# (v3.9) Etiketter för batchar i progress/logg
_BATCH_LABELS: Dict[str, str] = {
    "to": "TO",
    "to_sv": "TO · SV",
    "to_en": "TO · EN",
    "bcc": "BCC",
    "bcc_sv": "BCC · SV",
    "bcc_en": "BCC · EN",
}


def _normalize_lang_map(
    mapping: Optional[Dict[str, str]],
) -> Dict[str, str]:
    """Normalisera språkmap: {e-post(nedre): "sv"/"en"}.

    Nycklar görs lowercase (jämförelser är case-insensitivt),
    värden normaliseras till "sv"/"en" (allt annat → "sv").
    """
    result_map: Dict[str, str] = {}
    for key, value in (mapping or {}).items():
        try:
            email = str(key).strip().lower()
            lang = str(value or "").strip().lower()
        except Exception:
            continue
        if email:
            result_map[email] = "en" if lang == "en" else "sv"
    return result_map


def text_to_html(
    text:      str,
    free_text: str = "",
) -> str:
    """
    Konvertera ren text till HTML med styling.

    Fritext renderas i en separat sektion med kursiv stil.

    Args:
        text:      Huvudbrödtext (plain)
        free_text: Valfri fritext att appendas i separat block

    Returns:
        Komplett HTML-sträng
    """
    def _paragraphize(raw: str) -> str:
        escaped    = html_module.escape(raw)
        paragraphs = escaped.split("\n\n")
        parts: List[str] = []
        for para in paragraphs:
            stripped = para.strip()
            if stripped:
                lines = stripped.replace("\n", "<br>\n")
                parts.append(f"<p>{lines}</p>")
        return "\n".join(parts)

    body = _paragraphize(text or "")

    if free_text and free_text.strip():
        free_html = _paragraphize(free_text)
        body += f'\n<div class="free-text">\n{free_html}\n</div>'

    return HTML_TEMPLATE.format(body=body)


def validate_attachment(fpath: Path) -> Optional[str]:
    """Validera en bilagefil. Returns None om OK, annars felbeskrivning."""
    if not fpath.exists():
        return f"Filen finns inte: {fpath.name}"
    if not fpath.is_file():
        return f"Inte en fil: {fpath.name}"
    size_mb = fpath.stat().st_size / (1024 * 1024)
    if size_mb > MAX_ATTACHMENT_SIZE_MB:
        return (
            f"Bilagan '{fpath.name}' är för stor: "
            f"{size_mb:.1f} MB (max {MAX_ATTACHMENT_SIZE_MB} MB)"
        )
    return None


def append_free_text(
    body:            str,
    free_text:       str,
    include_english: bool,
) -> str:
    """
    Appendar fritext till brödtexten.

    Args:
        body:            Ursprunglig brödtext
        free_text:       Fritext att appendas
        include_english: Om engelska aktivt (för framtida hantering)

    Returns:
        Kombinerad brödtext
    """
    if not free_text or not free_text.strip():
        return body
    return f"{body}\n\n{free_text}"


def merge_recipients(
    manual_to:   Optional[List[str]] = None,
    manual_bcc:  Optional[List[str]] = None,
    default_bcc: Optional[List[str]] = None,
    own_email:   Optional[str]       = None,
) -> Tuple[List[str], List[str]]:
    """
    Slå ihop manuella mottagare med standardmottagare och egen e-post.

    - own_email placeras först i TO-listan (alltid med)
    - default_bcc läggs till i BCC-listan
    - All dedupliceras case-insensitivt

    Args:
        manual_to:   Manuella To-mottagare
        manual_bcc:  Manuella Bcc-mottagare
        default_bcc: Standard Bcc från settings.default_bcc
        own_email:   Egen e-postadress (alltid först i TO)

    Returns:
        (to, bcc) – sammanslagna och dedupliciserade listor

    Exempel::

        to, bcc = merge_recipients(
            manual_to=["kund@firma.se"],
            manual_bcc=[],
            default_bcc=["arkiv@firma.se"],
            own_email="min@firma.se",
        )
        # to  = ["min@firma.se", "kund@firma.se"]
        # bcc = ["arkiv@firma.se"]
    """
    to_final: List[str] = []

    # 1. Egen e-post först (om satt)
    own = (own_email or "").strip()
    if own and validate_email_address(own):
        to_final.append(own)

    # 2. Manuella TO
    to_final.extend(manual_to or [])

    # 3. Deduplicera
    to_final = dedupe_preserve_order(to_final)

    # 4. Bcc = manuella + standard, deduplicerade mot To
    bcc_final = dedupe_preserve_order(
        list(manual_bcc or []) + list(default_bcc or [])
    )
    to_set = {e.lower() for e in to_final}
    bcc_final = [e for e in bcc_final if e.lower() not in to_set]

    return to_final, bcc_final


# ═══════════════════════════════════════════════════════════════════════════
# Bildkomprimering (v3.7 – inställningsstyrd)
# ═══════════════════════════════════════════════════════════════════════════
def _pick_output_format(ext: str) -> Tuple[str, str, int]:
    """Välj (Qt/PIL-format, filändelse, kvalitet) för en bildändelse."""
    if ext in (".jpg", ".jpeg"):
        return "JPG", ".jpg", IMAGE_JPEG_QUALITY
    if ext == ".png":
        return "PNG", ".png", IMAGE_PNG_LEVEL
    if ext == ".webp":
        return "WEBP", ".webp", IMAGE_WEBP_QUALITY
    # .bmp / .tif / .tiff → konverteras till JPEG (mycket mindre)
    return "JPG", ".jpg", IMAGE_JPEG_QUALITY


def _compress_with_qimage(
    src:       Path,
    out_path:  Path,
    ext:       str,
    orig_size: int,
    cfg:       Dict[str, Any],
) -> Optional[Path]:
    """Komprimera med PyQt6.QtGui.QImage (finns i appen)."""
    try:
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QImage, QPainter
    except Exception:
        return None  # fallback till Pillow anropas av anroparen

    jpeg_quality = int(cfg.get("jpeg_quality", IMAGE_JPEG_QUALITY))
    png_level    = int(cfg.get("png_level", IMAGE_PNG_LEVEL))
    webp_quality = int(cfg.get("webp_quality", IMAGE_WEBP_QUALITY))
    preserve_dim = bool(cfg.get("preserve_dimensions", True))
    sharp        = bool(cfg.get("sharp", True))

    img = QImage(str(src))
    if img.isNull():
        log.warning("Kunde inte läsa bild '%s' (QImage) – behåller original.",
                    src.name)
        return None

    # Skala ner endast om dimensioner INTE ska bevaras
    if not preserve_dim:
        longest = max(img.width(), img.height())
        if longest > MAX_IMAGE_DIMENSION:
            scale = MAX_IMAGE_DIMENSION / float(longest)
            transform = (
                Qt.TransformationMode.SmoothTransformation
                if sharp
                else Qt.TransformationMode.FastTransformation
            )
            img = img.scaled(
                max(1, int(img.width() * scale)),
                max(1, int(img.height() * scale)),
                Qt.AspectRatioMode.KeepAspectRatio,
                transform,
            )

    fmt, suffix, _ = _pick_output_format(ext)
    if fmt == "JPG":
        quality = jpeg_quality
    elif fmt == "PNG":
        quality = png_level
    else:
        quality = webp_quality
    out = out_path.with_name(f"{src.stem}_c{suffix}")

    # JPEG har ingen alfakanal – lägg transparenta bilder på vit bakgrund
    if fmt == "JPG" and img.hasAlphaChannel():
        base = QImage(img.size(), QImage.Format.Format_RGB32)
        base.fill(Qt.GlobalColor.white)
        painter = QPainter(base)
        try:
            painter.drawImage(0, 0, img)
        finally:
            painter.end()
        img = base

    if not img.save(str(out), fmt, quality):
        log.debug("QImage kunde inte spara '%s' som %s – behåller original.",
                  src.name, fmt)
        return None

    if not out.exists() or out.stat().st_size >= orig_size:
        log.debug("Komprimerad '%s' är inte mindre – behåller original.",
                  src.name)
        return None
    return out


def _compress_with_pillow(
    src:       Path,
    out_path:  Path,
    ext:       str,
    orig_size: int,
    cfg:       Dict[str, Any],
) -> Optional[Path]:
    """Komprimera med Pillow (fallback om PyQt6 saknas)."""
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return None

    jpeg_quality = int(cfg.get("jpeg_quality", IMAGE_JPEG_QUALITY))
    png_level    = int(cfg.get("png_level", IMAGE_PNG_LEVEL))
    webp_quality = int(cfg.get("webp_quality", IMAGE_WEBP_QUALITY))
    preserve_dim = bool(cfg.get("preserve_dimensions", True))
    sharp        = bool(cfg.get("sharp", True))

    fmt, suffix, _ = _pick_output_format(ext)
    out = out_path.with_name(f"{src.stem}_c{suffix}")

    try:
        with Image.open(src) as im:
            # Skala ner endast om dimensioner INTE ska bevaras
            if not preserve_dim:
                longest = max(im.size)
                if longest > MAX_IMAGE_DIMENSION:
                    scale = MAX_IMAGE_DIMENSION / float(longest)
                    new_size = (
                        max(1, int(im.size[0] * scale)),
                        max(1, int(im.size[1] * scale)),
                    )
                    resample = (
                        Image.Resampling.LANCZOS
                        if sharp
                        else Image.Resampling.BILINEAR
                    )
                    im = im.resize(new_size, resample)

            if fmt == "JPG":
                # Platta ut transparens mot vit bakgrund
                if im.mode in ("RGBA", "LA", "P"):
                    rgba = im.convert("RGBA")
                    bg = Image.new("RGB", rgba.size, (255, 255, 255))
                    bg.paste(rgba, mask=rgba.getchannel("A"))
                    im = bg
                else:
                    im = im.convert("RGB")
                im.save(out, "JPEG", quality=jpeg_quality, optimize=True)
            elif fmt == "PNG":
                im.save(out, "PNG", optimize=True, compress_level=png_level)
            else:  # WEBP
                im.save(out, "WEBP", quality=webp_quality)
    except Exception as exc:
        log.warning("Pillow-komprimering av '%s' misslyckades: %s – "
                    "behåller original.", src.name, exc)
        return None

    if not out.exists() or out.stat().st_size >= orig_size:
        log.debug("Komprimerad '%s' är inte mindre – behåller original.",
                  src.name)
        return None
    return out


def _compress_single_image(
    src:      Path,
    tmp_dir:  Path,
    cfg:      Dict[str, Any],
) -> Optional[Path]:
    """
    Komprimera en enskild bildfil.

    Returns:
        Sökväg till komprimerad fil, eller None om original ska behållas.
    """
    try:
        if not src.is_file():
            return None
        ext = src.suffix.lower()
        if ext not in IMAGE_EXTENSIONS:
            return None
        # Animerade GIF:er rörs aldrig (tappar animation)
        if ext == ".gif":
            return None
        orig_size = src.stat().st_size
        # Små bilder rörs inte – inget att vinna
        if orig_size < MIN_IMAGE_SIZE_TO_COMPRESS:
            return None

        # 1) Primär: PyQt6 QImage (finns i appen, ingen ny dependency)
        out = _compress_with_qimage(src, tmp_dir, ext, orig_size, cfg)
        if out is not None:
            log.info("Bild komprimerad (QImage): %s (%.0f KB → %.0f KB)",
                     src.name, orig_size / 1024, out.stat().st_size / 1024)
            return out

        # 2) Fallback: Pillow (om installerat)
        out = _compress_with_pillow(src, tmp_dir, ext, orig_size, cfg)
        if out is not None:
            log.info("Bild komprimerad (Pillow): %s (%.0f KB → %.0f KB)",
                     src.name, orig_size / 1024, out.stat().st_size / 1024)
            return out

        log.debug("Ingen komprimering gjordes av '%s' – behåller original.",
                  src.name)
        return None
    except Exception as exc:
        log.warning("Fel vid bildkomprimering av '%s': %s – behåller original.",
                    getattr(src, "name", src), exc)
        return None


def _compress_attachments(
    attachments: List[str],
    compress_settings: Optional[Dict[str, Any]] = None,
) -> Tuple[List[str], Optional[tempfile.TemporaryDirectory], int]:
    """
    Komprimera bildbilagor i listan.

    Gör INGET (returnerar oförändrad lista, inget tmpdir) om:
      - listan är tom
      - inga bildfiler finns
      - ingen bild kunde komprimeras (alla behåller original)

    compress_settings (v3.7) – samma nycklar som
    SettingsManager.image_compression_settings():
      - image_jpeg_quality (int)
      - image_png_compress_level (int)
      - preserve_image_dimensions (bool)
      - preserve_image_sharpness (bool)

    Returns:
        (ny lista med sökvägar, tmpdir-objekt eller None, antal komprimerade)
    """
    cfg: Dict[str, Any] = {
        "jpeg_quality": int(
            (compress_settings or {}).get("image_jpeg_quality", IMAGE_JPEG_QUALITY)
        ),
        "png_level": int(
            (compress_settings or {}).get("image_png_compress_level", IMAGE_PNG_LEVEL)
        ),
        "webp_quality": IMAGE_WEBP_QUALITY,
        "preserve_dimensions": bool(
            (compress_settings or {}).get("preserve_image_dimensions", True)
        ),
        "sharp": bool(
            (compress_settings or {}).get("preserve_image_sharpness", True)
        ),
    }

    # (v3.7.1) Inga bildfiler alls → returnera direkt utan temp-katalog.
    if not any(
        Path(attach).suffix.lower() in IMAGE_EXTENSIONS
        for attach in attachments
    ):
        return list(attachments), None, 0

    tmp = tempfile.TemporaryDirectory(prefix="emailapp_img_")
    # Säkerhetsnät: om något oväntat avbryter sändningen rensas katalogen
    # ändå vid processens slut.
    atexit.register(tmp.cleanup)
    tmp_path = Path(tmp.name)

    image_count = 0
    compressed  = 0
    new_list: List[str] = []

    try:
        for attach in attachments:
            src = Path(attach)
            if src.suffix.lower() in IMAGE_EXTENSIONS:
                image_count += 1
                out = _compress_single_image(src, tmp_path, cfg)
                if out is not None:
                    new_list.append(str(out))
                    compressed += 1
                    continue
            new_list.append(attach)
    except Exception as exc:
        log.warning("Bildkomprimering avbröts: %s – skickar originalfiler.",
                    exc)
        tmp.cleanup()
        return list(attachments), None, 0

    if compressed == 0:
        tmp.cleanup()
        return list(attachments), None, 0

    log.info("Bildkomprimering klar: %d/%d bilder komprimerades.",
             compressed, image_count)
    return new_list, tmp, compressed


# ═══════════════════════════════════════════════════════════════════════════
# SMTP-anslutning
# ═══════════════════════════════════════════════════════════════════════════
def validate_smtp_params(
    smtp_server:  str,
    smtp_port:    int,
    sender_email: str,
) -> None:
    """Grundläggande validering av SMTP-parametrar."""
    if not smtp_server or not str(smtp_server).strip():
        raise EmailSendConfigError(
            "SMTP-server är inte angiven."
        )
    try:
        port = int(smtp_port)
    except (TypeError, ValueError) as exc:
        raise EmailSendConfigError(
            f"Ogiltig SMTP-port: {smtp_port!r}"
        ) from exc
    if not (1 <= port <= 65535):
        raise EmailSendConfigError(
            f"SMTP-port utanför giltigt intervall (1-65535): {port}"
        )
    if not sender_email or "@" not in sender_email:
        raise EmailSendConfigError(
            "Avsändarens e-postadress saknas eller är ogiltig."
        )


def connect_smtp(
    smtp_server:  str,
    smtp_port:    int,
    username:     str,
    password:     str,
    *,
    timeout:      int            = 30,
    use_ssl:      Optional[bool] = None,
    disable_tls:  bool           = False,
    smtp_debug:   bool           = False,
) -> smtplib.SMTP:
    """
    Öppna SMTP-anslutning.

    ``use_ssl``:
      - ``True``  → SMTP_SSL
      - ``False`` → SMTP + ev. STARTTLS
      - ``None``  → auto (port 465 → SSL, annars STARTTLS)

    Raises:
        EmailSendError: vid anslutningsfel.
    """
    context = ssl.create_default_context()
    if use_ssl is None:
        use_ssl = smtp_port == 465

    try:
        if use_ssl:
            log.info(
                "Ansluter till %s:%s med SSL (SMTP_SSL).",
                smtp_server, smtp_port,
            )
            server: smtplib.SMTP = smtplib.SMTP_SSL(
                smtp_server, smtp_port,
                timeout=timeout, context=context,
            )
        else:
            log.info(
                "Ansluter till %s:%s (STARTTLS=%s).",
                smtp_server, smtp_port, not disable_tls,
            )
            server = smtplib.SMTP(
                smtp_server, smtp_port, timeout=timeout
            )
            server.ehlo()
            if not disable_tls:
                server.starttls(context=context)
                server.ehlo()
            else:
                log.warning(
                    "STARTTLS inaktiverat – "
                    "anslutningen är okrypterad!"
                )

        if smtp_debug:
            server.set_debuglevel(1)

        if username and password:
            log.info("Loggar in på SMTP som %r.", username)
            server.login(username, password)
        else:
            log.info(
                "SMTP utan autentisering "
                "(ingen username/password)."
            )
        return server

    except smtplib.SMTPAuthenticationError as exc:
        log.error("SMTP-autentisering misslyckades: %s", exc)
        raise EmailSendError(
            "Felaktigt användarnamn eller lösenord. "
            "Kontrollera SMTP-inställningarna."
        ) from exc
    except smtplib.SMTPException as exc:
        log.error("SMTP-anslutningsfel: %s", exc)
        raise EmailSendError(
            "Kunde inte ansluta till SMTP-servern. "
            "Kontrollera server, port och nätverksanslutning."
        ) from exc
    except OSError as exc:
        log.error("Nätverksfel vid SMTP-anslutning: %s", exc)
        raise EmailSendError(
            "Nätverksfel. Kontrollera internetanslutning "
            "och servernamn."
        ) from exc


def close_smtp(server: Optional[smtplib.SMTP]) -> None:
    """Stäng SMTP-anslutning säkert."""
    if server is None:
        return
    try:
        server.quit()
    except Exception:
        try:
            server.close()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# MIME-meddelande
# ═══════════════════════════════════════════════════════════════════════════
def build_message(
    sender_email:  str,
    sender_name:   str,
    to_header:     str,
    subject:       str,
    body_plain:    str,
    body_html:     Optional[str],
    attachments:   List[str],
    *,
    reply_to:      Optional[str]       = None,
    extra_headers: Optional[Dict[str, str]] = None,
    request_receipts: bool             = False,
) -> MIMEMultipart:
    """
    Bygg ett MIME-meddelande.

    Struktur:
      multipart/mixed
        ├── multipart/alternative
        │   ├── text/plain
        │   └── text/html
        ├── bilaga 1
        └── ...

    request_receipts (v3.8): True → lägg till
      Disposition-Notification-To (läskvitto, RFC 3798) och
      Return-Receipt-To (många servrar/klienter tolkar som
      leverans-/läskvitto).
    """
    outer = MIMEMultipart("mixed")
    outer["From"] = formataddr(
        (str(Header(sender_name or "", "utf-8")), sender_email)
    )
    outer["To"]         = to_header
    outer["Date"]       = formatdate(localtime=True)
    outer["Subject"]    = Header(subject or "", "utf-8")
    outer["Message-ID"] = make_msgid()
    outer["X-Mailer"]   = USER_AGENT
    outer["MIME-Version"] = "1.0"

    # Reply-To: defaulta till sender_email om ej satt
    if reply_to and reply_to.strip():
        outer["Reply-To"] = reply_to.strip()
    else:
        outer["Reply-To"] = sender_email

    # Leverans-/läskvitto (v3.8) – headers som mottagarens klient tolkar
    if request_receipts:
        outer["Disposition-Notification-To"] = sender_email
        outer["Return-Receipt-To"] = sender_email

    if extra_headers:
        for k, v in extra_headers.items():
            if k and v is not None:
                outer[k] = str(v)

    # Text/HTML-del
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(body_plain or "", "plain", "utf-8"))
    if body_html:
        alt.attach(MIMEText(body_html, "html", "utf-8"))
    outer.attach(alt)

    # Bilagor
    total_size = 0
    for fpath_str in attachments or []:
        fpath = Path(fpath_str)
        err   = validate_attachment(fpath)
        if err:
            log.warning("Bilaga hoppas över: %s", err)
            continue

        file_size   = fpath.stat().st_size
        total_size += file_size
        if total_size > MAX_TOTAL_ATTACHMENTS_MB * 1024 * 1024:
            log.warning(
                "Total bilagestorlek överstiger %d MB – "
                "hoppar över '%s' och resterande.",
                MAX_TOTAL_ATTACHMENTS_MB, fpath.name,
            )
            break

        try:
            ctype, _ = mimetypes.guess_type(str(fpath))
            if ctype is None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            with open(fpath, "rb") as f:
                payload = f.read()

            if maintype == "image":
                part: MIMEBase = MIMEImage(
                    payload, _subtype=subtype
                )
            else:
                part = MIMEBase(maintype, subtype)
                part.set_payload(payload)
                encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=fpath.name,
            )
            outer.attach(part)
            log.debug(
                "Bifogade: %s (%.1f KB)",
                fpath.name, file_size / 1024,
            )
        except Exception as exc:
            log.warning(
                "Kunde inte bifoga '%s': %s", fpath.name, exc
            )

    return outer


# ═══════════════════════════════════════════════════════════════════════════
# Sändningsfunktion
# ═══════════════════════════════════════════════════════════════════════════
def send_email(
    smtp_server:    str,
    smtp_port:      int,
    sender_email:   str,
    sender_name:    str,
    username:       str,
    password:       str,
    word_file_path: str,
    replacements:   Dict[str, str],
    include_english: bool,
    recipients_to:  List[str],
    recipients_bcc: List[str],
    attachments:    List[str],
    comment:        str  = "",
    free_text:      str  = "",
    *,
    # Formatering
    body_is_html:             bool          = False,
    generate_html_from_plain: bool          = True,
    # Validering
    validate_recipients:      bool          = False,
    skip_invalid_recipients:  bool          = True,
    # Anslutning
    use_ssl:                  Optional[bool] = None,
    disable_tls:              bool          = False,
    timeout:                  int           = 30,
    # Retry
    max_retries:              int           = 2,
    retry_backoff_factor:     float         = 2.0,
    # Batchning
    bcc_batch_size:           Optional[int] = None,
    delay_between_batches:    float         = 0.5,
    # Extra
    reply_to:                 Optional[str] = None,
    extra_headers:            Optional[Dict[str, str]] = None,
    smtp_debug:               bool          = False,
    dry_run:                  bool          = False,
    log_recipient_details:    bool          = False,
    # Egen e-post (spec §4.5)
    own_email:                Optional[str] = None,
    default_bcc:              Optional[List[str]] = None,
    # Placeholder AI-översättning (spec §9.1)
    translate_placeholders:   bool          = True,
    # Bildkomprimering (v3.6)
    compress_images:          bool          = False,
    # Bildkomprimeringsinställningar (v3.7 – matchar SettingsManager v24)
    preserve_image_dimensions: bool         = True,
    preserve_image_sharpness:  bool         = True,
    image_jpeg_quality:        int          = 92,
    image_png_compress_level:  int          = 6,
    # Leverans-/läskvitto (v3.8)
    request_receipts:         bool          = False,
    # Språkgrupperade mottagare (v3.9) – e-post → "sv"/"en"
    recipients_to_lang:       Optional[Dict[str, str]] = None,
    recipients_bcc_lang:      Optional[Dict[str, str]] = None,
    # Progress
    on_progress:              ProgressCallback = None,
) -> SendResult:
    """
    Skicka e-post baserat på en mall.

    Parametrar:
        free_text: Valfri fritext som appendas sist i brödtexten.
        own_email: Egen e-postadress – alltid först i TO-listan.
        default_bcc: Standard Bcc-mottagare från settings.
        translate_placeholders: AI-översätt placeholder-värden
            när include_english=True.
        compress_images: Komprimera bildbilagor innan sändning.
            Gör INGET om False eller om inga bilder finns.
            Komprimerade bilder som inte blir mindre behåller originalet.
        preserve_image_dimensions: Bevara bildens pixelstorlek
            (komprimera enbart filstorleken). Om False skalas bilder
            vars längsta sida överstiger MAX_IMAGE_DIMENSION ner.
        preserve_image_sharpness: Välj högkvalitets-omsampling
            (SmoothTransformation/LANCZOS) när nerskalning sker.
        image_jpeg_quality: JPEG-kvalitet 0-100 (v3.7).
        image_png_compress_level: PNG-komprimeringsnivå 0-9 (v3.7).
        request_receipts: Begär leverans- och läskvitto (v3.8).
            - Headers: Disposition-Notification-To + Return-Receipt-To
            - SMTP-DSN (NOTIFY=SUCCESS,FAILURE) om servern stödjer det
            - Fail-safe: skickar ALDRIG misslyckat p.g.a. kvitto – om
              servern nekar DSN skickas mailet ändå utan kvitto
        recipients_to_lang / recipients_bcc_lang (v3.9):
            Dict {e-post: "sv"|"en"} – språk PER mottagare.
            - "sv"-mottagare får ENBART svensk version av mailet
            - "en"-mottagare får ENBART engelsk version
            - Gäller även om include_english=True (SV får aldrig engelsk)
            - include_english=False → alla får svensk version (som förut)
            - Saknad nyckel/annat värde → "sv"
            - Utan dessa dicts är beteendet exakt som tidigare

    Se övriga parametrar i modulens docstring.

    Returns:
        SendResult med detaljerad statistik.
    """
    start_time = time.monotonic()
    result     = SendResult(dry_run=dry_run)
    result.receipts_requested = bool(request_receipts)

    # ── Normalisera input ──────────────────────────────────────────
    recipients_to  = dedupe_preserve_order(recipients_to  or [])
    recipients_bcc = dedupe_preserve_order(recipients_bcc or [])
    attachments    = list(attachments or [])
    replacements   = dict(replacements) if replacements else {}
    free_text      = (free_text or "").strip()
    comment        = (comment   or "").strip()
    own_email      = (own_email or "").strip()
    default_bcc    = list(default_bcc or [])

    # ── Validera SMTP-parametrar ───────────────────────────────────
    try:
        validate_smtp_params(smtp_server, smtp_port, sender_email)
    except EmailSendConfigError as exc:
        result.errors.append(str(exc))
        raise

    # ── Bildkomprimering (v3.6/v3.7.1) ─────────────────────────────
    # Gör INGET om:
    #   - compress_images=False
    #   - inga bilagor finns
    #   - INGEN bilaga är en bild (v3.7.1 – komprimering startas
    #     inte ens när bara PDF/dokument bifogats)
    _img_tmp_dir: Optional[tempfile.TemporaryDirectory] = None
    if compress_images and attachments:
        has_images = any(
            Path(attach).suffix.lower() in IMAGE_EXTENSIONS
            for attach in attachments
        )
        if has_images:
            attachments, _img_tmp_dir, _n_compressed = _compress_attachments(
                attachments,
                compress_settings={
                    "image_jpeg_quality": image_jpeg_quality,
                    "image_png_compress_level": image_png_compress_level,
                    "preserve_image_dimensions": preserve_image_dimensions,
                    "preserve_image_sharpness": preserve_image_sharpness,
                },
            )
            result.images_compressed = _n_compressed

    # ── Slå ihop mottagare (own_email först i TO + default_bcc) ───
    recipients_to, recipients_bcc = merge_recipients(
        manual_to=recipients_to,
        manual_bcc=recipients_bcc,
        default_bcc=default_bcc,
        own_email=own_email if own_email else None,
    )

    # ── Validera mottagare ─────────────────────────────────────────
    if validate_recipients:
        recipients_to, inv_to = validate_email_list(
            recipients_to,
            validate=True,
            skip_invalid=skip_invalid_recipients,
        )
        recipients_bcc, inv_bcc = validate_email_list(
            recipients_bcc,
            validate=True,
            skip_invalid=skip_invalid_recipients,
        )
        result.invalid_emails = inv_to + inv_bcc
        if result.invalid_emails:
            result.warnings.append(
                f"{len(result.invalid_emails)} ogiltiga adresser "
                f"filtrerades"
            )
    else:
        recipients_to = [
            e.strip() for e in recipients_to  if e and e.strip()
        ]
        recipients_bcc = [
            e.strip() for e in recipients_bcc if e and e.strip()
        ]

    if not recipients_to and not recipients_bcc:
        msg = "Inga mottagare angivna (To eller Bcc)."
        result.errors.append(msg)
        raise EmailSendConfigError(msg)

    # ── Språkgrupper (v3.9) ────────────────────────────────────────
    # "sv"-mottagare får ENBART svensk version, "en"-mottagare ENBART
    # engelsk – även när include_english=True (checkbox ikryssad).
    # include_english=False → alla får svensk version (som förut).
    to_lang   = _normalize_lang_map(recipients_to_lang)
    bcc_lang  = _normalize_lang_map(recipients_bcc_lang)

    if include_english:
        sv_to = [
            e for e in recipients_to
            if to_lang.get(e.lower(), "sv") != "en"
        ]
        en_to = [
            e for e in recipients_to
            if to_lang.get(e.lower(), "sv") == "en"
        ]
        sv_bcc = [
            e for e in recipients_bcc
            if bcc_lang.get(e.lower(), "sv") != "en"
        ]
        en_bcc = [
            e for e in recipients_bcc
            if bcc_lang.get(e.lower(), "sv") == "en"
        ]
    else:
        sv_to, en_to = recipients_to, []
        sv_bcc, en_bcc = recipients_bcc, []

    split_active = bool((sv_to or sv_bcc) and (en_to or en_bcc))

    # ── Placeholder-uppsättningar per språk (v3.9) ─────────────────
    replacements_sv = dict(replacements)
    replacements_en = dict(replacements)
    if include_english and translate_placeholders and replacements:
        replacements_en = _translate_placeholder_values(
            replacements, True, translate_placeholders,
        )
        if en_to or en_bcc:
            result.had_translation = True
            result.had_placeholder_translation = True
            log.debug("Placeholder-värden översatta: %d fält (EN)",
                      len(replacements_en))

    # ── Kommentar → platshållare ::kommentar:: ─────────────────────
    if comment:
        replacements_sv.setdefault("kommentar", comment)
        replacements_en.setdefault("kommentar", comment)

    # ── Parsa mall per språk (endast språk som används) ────────────
    prepared: Dict[str, Tuple[str, str, Optional[str]]] = {}

    def _prepare_lang(
        lang: str, repl: Dict[str, str]
    ) -> Tuple[str, str, Optional[str]]:
        """Parsa mall + fritext + HTML för ETT språk."""
        use_en = lang == "en"
        subject_l, body_raw = parse_subject_and_body(
            word_file_path, repl, use_en
        )
        if not use_en:
            body_raw = _strip_vin_from_swedish(body_raw)
        else:
            body_raw = _strip_empty_vin_line(
                body_raw, str(repl.get("vin") or repl.get("VIN") or "")
            )
        if free_text:
            body_raw = append_free_text(body_raw, free_text, use_en)
            result.had_free_text = True
        if body_is_html:
            body_html_l: Optional[str] = body_raw
            try:
                import bs4  # type: ignore
                soup = bs4.BeautifulSoup(body_html_l, "html.parser")
                body_plain_l = soup.get_text("\n")
            except Exception:
                body_plain_l = re.sub(
                    r"<br\s*/?>", "\n", body_raw, flags=re.I
                )
                body_plain_l = re.sub(r"<[^>]+>", "", body_plain_l)
        else:
            body_plain_l = body_raw
            if generate_html_from_plain:
                if free_text and body_raw.endswith(free_text):
                    main_body = body_raw[:-len(free_text)].rstrip()
                    body_html_l = text_to_html(main_body, free_text)
                else:
                    body_html_l = text_to_html(body_plain_l)
            else:
                body_html_l = None
        return subject_l, body_plain_l, body_html_l

    try:
        if sv_to or sv_bcc:
            prepared["sv"] = _prepare_lang("sv", replacements_sv)
        if en_to or en_bcc:
            prepared["en"] = _prepare_lang("en", replacements_en)
    except FileNotFoundError as exc:
        msg = f"Mallfilen hittades inte: {word_file_path}"
        log.error(msg)
        result.errors.append(msg)
        raise EmailSendConfigError(msg) from exc
    except ValueError as exc:
        msg = f"Fel i mallen '{word_file_path}': {exc}"
        log.error(msg)
        result.errors.append(msg)
        raise EmailSendConfigError(msg) from exc
    except Exception as exc:
        msg = f"Oväntat fel vid mallparsning: {exc}"
        log.error(msg)
        result.errors.append(msg)
        raise EmailSendConfigError(msg) from exc

    subject = prepared.get("sv", prepared.get("en", ("", "", None)))[0]
    result.subject = subject

    # ── Bygg batchar (kind, lang, rcpts) ──────────────────────────
    batches: List[Tuple[str, str, List[str]]] = []
    if split_active:
        if sv_to:
            batches.append(("to_sv", "sv", list(sv_to)))
        if en_to:
            batches.append(("to_en", "en", list(en_to)))
        for batch_kind, batch_lang, group in (
            ("bcc_sv", "sv", sv_bcc),
            ("bcc_en", "en", en_bcc),
        ):
            if not group:
                continue
            if bcc_batch_size and bcc_batch_size > 0:
                for chunk in chunk_list(group, bcc_batch_size):
                    batches.append((batch_kind, batch_lang, chunk))
            else:
                batches.append((batch_kind, batch_lang, group))
    else:
        # (v3.9) En enda språkgrupp – språket kan vara EN även när
        # alla mottagare är EN-markerade (då finns ingen SV-grupp)
        batch_lang = "en" if (en_to or en_bcc) else "sv"
        if recipients_to:
            batches.append(("to", batch_lang, list(recipients_to)))
        if recipients_bcc:
            if bcc_batch_size and bcc_batch_size > 0:
                for chunk in chunk_list(recipients_bcc, bcc_batch_size):
                    batches.append(("bcc", batch_lang, chunk))
            else:
                batches.append(("bcc", batch_lang, recipients_bcc))

    result.recipients_to     = len(recipients_to)
    result.recipients_bcc    = len(recipients_bcc)
    result.recipients_sv     = len(sv_to) + len(sv_bcc)
    result.recipients_en     = len(en_to) + len(en_bcc)
    result.had_language_split = split_active
    result.total_recipients  = result.recipients_to + result.recipients_bcc
    result.batches_total     = len(batches)
    result.attachments_count = len(attachments)
    result.had_bcc           = bool(recipients_bcc)

    log.info(
        "Förbereder sändning – ämne: %r, mottagare: %d "
        "(To=%d, Bcc=%d), språk SV=%d EN=%d, bilagor=%d, "
        "batchar=%d, fritext=%s",
        subject,
        result.total_recipients,
        result.recipients_to,
        result.recipients_bcc,
        result.recipients_sv,
        result.recipients_en,
        result.attachments_count,
        result.batches_total,
        "ja" if free_text else "nej",
    )
    if log_recipient_details:
        log.debug("To-SV:  %s", sv_to)
        log.debug("To-EN:  %s", en_to)
        log.debug("Bcc-SV: %s", sv_bcc)
        log.debug("Bcc-EN: %s", en_bcc)

    def _to_header_for(kind: str, lang: str, rcpts: List[str]) -> str:
        """To-header för en batch (synliga To-mottagare i rätt språk)."""
        if kind.startswith("bcc"):
            visible = sv_to if lang == "sv" else en_to
            return (
                ", ".join(visible)
                if visible
                else "Undisclosed recipients:;"
            )
        return (
            ", ".join(rcpts)
            if rcpts
            else "Undisclosed recipients:;"
        )

    # ── DRY RUN ────────────────────────────────────────────────────
    if dry_run:
        for kind, lang, rcpts in batches:
            subject_l, body_plain_l, body_html_l = prepared[lang]
            msg_obj = build_message(
                sender_email, sender_name,
                to_header     = _to_header_for(kind, lang, rcpts),
                subject       = subject_l,
                body_plain    = body_plain_l,
                body_html     = body_html_l,
                attachments   = attachments,
                reply_to      = reply_to or sender_email,
                extra_headers = extra_headers,
                request_receipts = request_receipts,
            )
            log.debug(
                "[DRY RUN] Batch %s (%s):\n%s",
                kind, ", ".join(rcpts), msg_obj.as_string()[:2000],
            )
        log.info(
            "[DRY RUN] Skulle skickat till %d mottagare "
            "(SV=%d, EN=%d). Ämne: %s",
            result.total_recipients,
            result.recipients_sv, result.recipients_en, subject,
        )
        if _img_tmp_dir is not None:
            _img_tmp_dir.cleanup()
        result.success      = True
        result.batches_sent = result.batches_total
        result.elapsed_seconds = time.monotonic() - start_time
        return result

    # ── Sändning ──────────────────────────────────────────────────
    server: Optional[smtplib.SMTP] = None
    try:
        server = connect_smtp(
            smtp_server, smtp_port, username, password,
            timeout=timeout, use_ssl=use_ssl,
            disable_tls=disable_tls, smtp_debug=smtp_debug,
        )
        for idx, (kind, lang, rcpts) in enumerate(batches, start=1):
            subject_l, body_plain_l, body_html_l = prepared[lang]
            label = _BATCH_LABELS.get(kind, kind.upper())

            if on_progress:
                try:
                    on_progress(
                        idx,
                        len(batches),
                        f"Skickar batch {idx}/{len(batches)} "
                        f"({label}, {len(rcpts)} mottagare)…",
                    )
                except Exception:
                    pass

            msg_obj = build_message(
                sender_email, sender_name,
                to_header     = _to_header_for(kind, lang, rcpts),
                subject       = subject_l,
                body_plain    = body_plain_l,
                body_html     = body_html_l,
                attachments   = attachments,
                reply_to      = reply_to or sender_email,
                extra_headers = extra_headers,
                request_receipts = request_receipts,
            )
            message_str = msg_obj.as_string()

            server = send_with_retry(
                server               = server,
                mail_from            = sender_email,
                rcpt_to              = rcpts,
                message_str          = message_str,
                max_retries          = max_retries,
                retry_backoff_factor = retry_backoff_factor,
                smtp_server          = smtp_server,
                smtp_port            = smtp_port,
                username             = username,
                password             = password,
                timeout              = timeout,
                use_ssl              = use_ssl,
                disable_tls          = disable_tls,
                smtp_debug           = smtp_debug,
                request_delivery_receipt = request_receipts,
            )
            result.batches_sent += 1
            log.info(
                "Batch %d/%d skickad (%s, %d mottagare).",
                idx, len(batches), label, len(rcpts),
            )
            if delay_between_batches > 0 and idx < len(batches):
                time.sleep(delay_between_batches)

        result.success = True
        log.info(
            "Sändning klar. Batchar: %d, Mottagare: %d "
            "(SV=%d, EN=%d), Ämne: %r",
            result.batches_sent, result.total_recipients,
            result.recipients_sv, result.recipients_en, subject,
        )
    except EmailSendError:
        raise
    except smtplib.SMTPException as exc:
        msg = f"SMTP-fel: {exc}"
        log.error(msg)
        result.errors.append(msg)
        raise EmailSendError(msg) from exc
    except Exception as exc:
        msg = f"Oväntat fel vid sändning: {exc}"
        log.error(msg)
        result.errors.append(msg)
        raise EmailSendError(msg) from exc
    finally:
        close_smtp(server)
        # Rensa temporära komprimerade bilder
        if _img_tmp_dir is not None:
            _img_tmp_dir.cleanup()
        result.elapsed_seconds = time.monotonic() - start_time

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Retry-logik
# ═══════════════════════════════════════════════════════════════════════════
def send_with_retry(
    server:               smtplib.SMTP,
    mail_from:            str,
    rcpt_to:              List[str],
    message_str:          str,
    max_retries:          int,
    retry_backoff_factor: float,
    *,
    smtp_server:  str,
    smtp_port:    int,
    username:     str,
    password:     str,
    timeout:      int,
    use_ssl:      Optional[bool],
    disable_tls:  bool,
    smtp_debug:   bool,
    request_delivery_receipt: bool = False,
) -> smtplib.SMTP:
    """
    Skicka med retry och automatisk reconnect.

    request_delivery_receipt (v3.8): försök med SMTP-DSN
    (NOTIFY=SUCCESS,FAILURE, RFC 3461) när servern annonserar DSN i
    EHLO (esmtp_features). Fail-safe:
      - Om servern saknar DSN-stöd → skickas utan (inga options)
      - Om servern trots allt nekar RCPT med DSN-optionen → nytt försök
        UTAN DSN i samma anslutning
      - Ett kvitto är ALDRIG ett skäl att misslyckas med sändningen

    Returns:
        Serverobjektet (kan vara ny anslutning efter reconnect).

    Raises:
        EmailSendError: efter alla retries är uttömda.
    """
    for attempt in range(max_retries + 1):
        # DSN endast om servern annonserar stöd i EHLO-svaret
        dsn_ok = (
            request_delivery_receipt
            and "dsn" in getattr(server, "esmtp_features", {})
        )
        try:
            if dsn_ok:
                try:
                    server.sendmail(
                        mail_from, rcpt_to, message_str,
                        rcpt_options=["NOTIFY=SUCCESS,FAILURE"],
                    )
                    return server
                except smtplib.SMTPRecipientsRefused as exc:
                    # Servern annonserade DSN men nekade RCPT med
                    # optionen – försök en gång UTAN DSN innan vi ger
                    # upp (mailet ska alltid fram, kvittot är bonus).
                    log.warning(
                        "RCPT nekades med DSN-optionen – försöker "
                        "utan DSN: %s", exc,
                    )
            server.sendmail(mail_from, rcpt_to, message_str)
            return server
        except smtplib.SMTPServerDisconnected as exc:
            log.warning(
                "Server-disconnect vid försök %d/%d: %s",
                attempt + 1, max_retries + 1, exc,
            )
        except smtplib.SMTPRecipientsRefused as exc:
            refused = list(exc.recipients.keys())
            log.error("Mottagare nekades: %s", refused)
            raise EmailSendError(
                f"Mottagare nekades av servern: {refused}"
            ) from exc
        except smtplib.SMTPException as exc:
            log.warning(
                "SMTP-fel vid försök %d/%d: %s",
                attempt + 1, max_retries + 1, exc,
            )

        if attempt >= max_retries:
            raise EmailSendError(
                f"Sändning misslyckades efter "
                f"{max_retries + 1} försök."
            )

        delay = max(0.5, retry_backoff_factor ** attempt)
        log.info(
            "Väntar %.1fs innan retry %d/%d…",
            delay, attempt + 2, max_retries + 1,
        )
        time.sleep(delay)
        close_smtp(server)
        server = connect_smtp(
            smtp_server, smtp_port, username, password,
            timeout=timeout, use_ssl=use_ssl,
            disable_tls=disable_tls, smtp_debug=smtp_debug,
        )

    raise EmailSendError(
        "Sändning misslyckades (oväntat tillstånd)."
    )


# ═══════════════════════════════════════════════════════════════════════════
# Testfunktion
# ═══════════════════════════════════════════════════════════════════════════
def test_smtp_connection(
    smtp_server: str,
    smtp_port:   int,
    username:    str,
    password:    str,
    *,
    use_ssl:     Optional[bool] = None,
    timeout:     int            = 15,
) -> Tuple[bool, str]:
    """
    Testa SMTP-anslutning utan att skicka e-post.

    Returns:
        (ok: bool, meddelande: str)
    """
    try:
        validate_smtp_params(smtp_server, smtp_port, username)
    except EmailSendConfigError as exc:
        return False, str(exc)

    server: Optional[smtplib.SMTP] = None
    try:
        server = connect_smtp(
            smtp_server, smtp_port, username, password,
            timeout=timeout, use_ssl=use_ssl,
            disable_tls=False, smtp_debug=False,
        )
        return True, (
            f"Anslutning till {smtp_server}:{smtp_port} lyckades! "
            f"Inloggad som {username}."
        )
    except EmailSendError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"Oväntat fel: {exc}"
    finally:
        close_smtp(server)


# ═══════════════════════════════════════════════════════════════════════════
# Publikt API
# ═══════════════════════════════════════════════════════════════════════════
__all__ = [
    "send_email",
    "test_smtp_connection",
    "merge_recipients",
    "SendResult",
    "EmailSendConfigError",
    "EmailSendError",
    "EmailValidationError",
    "validate_email_address",
    "MAX_ATTACHMENT_SIZE_MB",
    "MAX_TOTAL_ATTACHMENTS_MB",
    "GLASS_TYPE_MAP",
    "_translate_placeholder_values",
]
