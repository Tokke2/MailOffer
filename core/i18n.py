#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tvåspråkigt UI (svenska/engelska) för E-postofferten.

Lättviktigt i18n-system utan beroenden:

- ``tr("menu.file")`` ger texten på valt språk.
- Språket styrs av inställningen ``language`` ("sv"/"en") och sätts
  vid start via ``set_language()`` (main.pyw + MainWindow).
- Fallback-kedja: valt språk → svenska → själva nyckeln (så att en
  saknad översättning aldrig ger tom/kraschad text).
- Formatparametrar: ``tr("update.current_version", version="5.4.0")``.

OBS: Översättningen införs stegvis. Huvudskalet (verktygsrad, menyer,
flikar, steg-rubriker), mall-wizarden, uppdateringen och donationen
går via ``tr()``. Äldre dialoger med hårdkodad svenska migreras
successivt – lägg nya strängar HÄR, aldrig hårdkodade i UI-kod.

FIL: core/i18n.py
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "sv"
SUPPORTED_LANGUAGES: Tuple[str, ...] = ("sv", "en")

_current_language = DEFAULT_LANGUAGE


def normalize_language(value: object) -> str:
    """Normalisera ett språkvärde till ``"sv"`` eller ``"en"``.

    Accepterar t.ex. "en", "EN", "en_GB", "english", "svenska".
    Okända/tomma värden → svenska (appens standardspråk).
    """
    text = str(value or "").strip().lower().replace("-", "_")
    if text.startswith("en") or text == "english":
        return "en"
    if text.startswith("sv") or text in ("swedish", "svenska"):
        return "sv"
    return DEFAULT_LANGUAGE


def set_language(language: object) -> str:
    """Sätt aktuellt UI-språk. Returnerar det normaliserade språket."""
    global _current_language
    _current_language = normalize_language(language)
    return _current_language


def get_language() -> str:
    """Returnera aktuellt UI-språk ("sv"/"en")."""
    return _current_language


def available_languages() -> List[Tuple[str, str]]:
    """(kod, visningsnamn) för språkmenyer."""
    return [("sv", "Svenska"), ("en", "English")]


# ───────────────────────────────────────────────────────────────────────
# Översättningstabeller. SV är kanonisk (fallback) – varje nyckel som
# används i koden MÅSTE finnas i SV; EN bör ha samma nycklar.
# ───────────────────────────────────────────────────────────────────────

_SV: Dict[str, str] = {
    # App-skal
    "app.window_title": "📧 E-postofferten – Skicka steg för steg",
    "app.tagline_steps": "1. Mall  →  2. Bilagor/Bilder  →  3. Mottagare  →  4. Skicka mail",
    "app.ready": "✅ Redo",
    "toolbar.send": "📤 Skicka",
    "toolbar.settings": "⚙️ Inställningar",
    "toolbar.new_template": "🧙 Ny mall",
    "toolbar.donate": "❤️ Donera",
    # Menyer
    "menu.file": "Arkiv",
    "menu.view": "Visa",
    "menu.theme": "Tema",
    "menu.language": "Språk",
    "menu.help": "Hjälp",
    "menu.send_mail": "📤 Skicka e-post",
    "menu.new_template_wizard": "🧙 Skapa ny mall (wizard)…",
    "menu.save_template": "💾 Spara mall",
    "menu.backup_lists": "📦 Säkerhetskopiera adresslistor…",
    "menu.update_from_folder": "⬇️ Uppdatera app från mapp…",
    "menu.check_updates": "🔄 Sök efter uppdateringar…",
    "menu.quit": "❌ Avsluta",
    "menu.theme_dark": "🌙 Mörkt",
    "menu.theme_light": "☀️ Ljust",
    "menu.theme_system": "💻 System",
    "menu.deliverability": "📖 Leveransbarhets-guide",
    "menu.donate": "❤️ Donera – stöd projektet",
    "menu.about": "ℹ️ Om E-postofferten",
    "menu.show_all_tabs": "↩️ Visa alla",
    "menu.hide_tab": "🙈 Dölj denna tab",
    "language.sv": "🇸🇪 Svenska",
    "language.en": "🇬🇧 Engelska",
    "language.changed_title": "Språk ändrat",
    "language.changed_text": (
        "Språket är ändrat till {language}.\n\n"
        "Starta om appen för att allt ska visas på det nya språket.\n"
        "Starta om nu?"
    ),
    "restart.failed": "Kunde inte starta om automatiskt – starta appen manuellt.",
    # Flikar
    "tab.send": "📤 Skicka",
    "tab.contacts": "👥 Kontakter",
    "tab.templates": "📝 Mallar",
    "tab.preview": "👁️ Preview",
    "tab.history": "📨 Historik",
    "tab.logs": "📜 Loggar",
    "tab.settings": "⚙️ Inställningar",
    # Sänd-wizardens steg
    "step1.title": "Mall",
    "step1.hint": "Välj mall och fyll i uppgifter.",
    "step2.title": "Bilagor/Bilder",
    "step2.hint": "Lägg till bilder, PDF:er eller andra filer. Drag & drop stöds här.",
    "step3.title": "Mottagare",
    "step3.hint": "Lägg till To och Bcc. Ingen CC används.",
    "step4.title": "Skicka mail",
    "step4.hint": "Förhandsgranska, bekräfta och skicka.",
    # Mall-fliken
    "templates_tab.heading": "Mallar",
    "templates_tab.text": (
        "Skapa nya mallar med wizarden – steg för steg, på svenska och "
        "engelska. Befintliga mallar redigeras i Skicka-flödet eller "
        "direkt i mallmappen."
    ),
    "templates_tab.wizard_btn": "🧙 Skapa ny mall med wizard…",
    "templates_tab.open_folder": "📂 Öppna mallmapp",
    "templates_tab.refresh": "🔄 Uppdatera lista",
    "templates_tab.count": "{count} mall(ar) i {folder}",
    "templates_tab.empty": "Inga mallar ännu – skapa din första med wizarden!",
    "templates_tab.use_hint": "Dubbelklicka på en mall för att använda den i Skicka-fliken.",
    # Mall-wizard
    "wizard.title": "🧙 Skapa ny mall",
    "wizard.btn_back": "< Tillbaka",
    "wizard.btn_next": "Nästa >",
    "wizard.btn_finish": "💾 Skapa mall",
    "wizard.btn_cancel": "Avbryt",
    "wizard.page_start.title": "Steg 1 – Namn & format",
    "wizard.page_start.subtitle": "Ge mallen ett namn och välj hur du vill börja.",
    "wizard.name.label": "Mallens namn:",
    "wizard.name.placeholder": "t.ex. Offertförfrågan Bilglas",
    "wizard.format.label": "Filformat:",
    "wizard.format.txt": "TXT – enklast (rekommenderas)",
    "wizard.format.html": "HTML – formaterat mail",
    "wizard.format.docx": "DOCX – Word-fil",
    "wizard.start_from.label": "Börja från:",
    "wizard.start.example": "Exempel: offertförfrågan Bilglas (SV + EN)",
    "wizard.start.blank": "Tom mall",
    "wizard.start.copy": "Kopia av befintlig mall:",
    "wizard.filename.preview": "Filnamn: {filename}",
    "wizard.page_sv.title": "Steg 2 – Svensk text",
    "wizard.page_sv.subtitle": "Ämne och brödtext på svenska. Uppgifter som ::modell:: blir ifyllnadsfält vid sändning.",
    "wizard.subject.label": "Ämne:",
    "wizard.body.label": "Brödtext:",
    "wizard.insert.label": "Infoga uppgift:",
    "wizard.insert.custom_btn": "➕ Egen…",
    "wizard.insert.custom_prompt": "Namn på uppgiften (t.ex. pris):",
    "wizard.page_en.title": "Steg 3 – Engelsk text (valfritt)",
    "wizard.page_en.subtitle": "EN-mottagare får den engelska versionen automatiskt.",
    "wizard.include_en": "Lägg till engelsk version ([en]-block)",
    "wizard.en_body.label": "Brödtext på engelska:",
    "wizard.translate_btn": "🌐 Översätt svenska texten automatiskt",
    "wizard.en.hint": (
        "Ämnesraden är gemensam – uppgiftsvärden översätts automatiskt "
        "vid sändning. Tips: ::vin:: visas bara i det engelska mailet."
    ),
    "wizard.translate.failed": "Automatisk översättning misslyckades – skriv texten manuellt.",
    "wizard.page_preview.title": "Steg 4 – Uppgifter & förhandsgranskning",
    "wizard.page_preview.subtitle": "Kontrollera att mallen ser rätt ut med testvärden.",
    "wizard.detected": "Hittade uppgifter: {placeholders}",
    "wizard.detected.none": "Inga uppgifter (placeholders) hittades – mallen skickas som den är.",
    "wizard.test_values.label": "Testvärden:",
    "wizard.preview.sv": "🇸🇪 Svensk version",
    "wizard.preview.en": "🇬🇧 Engelsk version",
    "wizard.page_save.title": "Steg 5 – Spara mallen",
    "wizard.page_save.subtitle": "Sista kollen innan mallen sparas i mallmappen.",
    "wizard.summary": "Fil: {filename}\nMapp: {folder}\nUppgifter: {placeholders}",
    "wizard.exists_warning": "⚠️ Filen finns redan och skrivs över när du skapar mallen.",
    "wizard.set_default": "Använd som standardmall vid start",
    "wizard.select_after": "Välj mallen i Skicka-fliken direkt",
    "wizard.error.title": "Kontrollera mallen",
    "wizard.error.name_required": "Ge mallen ett namn.",
    "wizard.error.subject_required": "Fyll i ett ämne (svenska).",
    "wizard.error.body_required": "Fyll i brödtext (svenska).",
    "wizard.error.en_body_required": "Fyll i engelsk brödtext – eller avmarkera engelsk version i steg 3.",
    "wizard.error.save_failed": "Kunde inte spara mallen:\n{error}",
    "wizard.created_status": "🧙 Mall skapad: {name}",
    # Uppdatering (GitHub Releases)
    "update.title": "Uppdatering",
    "update.checking": "Söker efter uppdateringar på GitHub…",
    "update.available_title": "Ny version finns! 🎉",
    "update.available_text": (
        "Version {latest} finns på GitHub (du har {current}).\n\n{notes}\n\n"
        "Ladda ner och installera nu? Dina mallar, adresslistor och "
        "inställningar rörs aldrig."
    ),
    "update.install": "⬇️ Installera nu",
    "update.later": "Senare",
    "update.release_page": "🌐 Releasesida",
    "update.up_to_date": "Du har redan senaste versionen ({current}). ✅",
    "update.no_releases": (
        "Det finns ingen publicerad release på GitHub ännu.\n\n"
        "Appen kan autouppdateras först när en release har publicerats "
        "på {repo_url}/releases."
    ),
    "update.check_failed": "Kunde inte söka efter uppdateringar:\n{error}",
    "update.downloading": "Laddar ner och installerar version {latest}…",
    "update.installed_title": "Uppdatering klar ✅",
    "update.installed": (
        "Uppdateringen är installerad ({count} filer uppdaterade).\n\n"
        "Starta om appen för att använda den nya versionen. Starta om nu?"
    ),
    "update.install_failed": "Uppdateringen misslyckades:\n{error}",
    "update.status_available": "⬇️ Ny version {latest} finns på GitHub",
    "update.group": "🔄 Uppdateringar (GitHub)",
    "update.auto_check": "Sök automatiskt efter uppdateringar vid start (högst 1 gång per dygn)",
    "update.current_version": "Installerad version: {version}",
    "update.last_check": "Senaste sökning: {when}",
    "update.last_check_never": "Senaste sökning: aldrig",
    "update.check_now_btn": "🔄 Sök efter uppdateringar nu",
    "update.from_folder_btn": "⬇️ Uppdatera app från mapp…",
    "update.folder_hint": (
        "Uppdatering kopierar bara kod. Mallar, JSON, adresslistor och "
        "inställningar lämnas orörda."
    ),
    # Donation
    "donate.title": "❤️ Donera",
    "donate.heading": "Stöd E-postofferten ❤️",
    "donate.text": (
        "E-postofferten är gratis att använda. Om appen sparar tid åt "
        "dig får du gärna bjuda på en kaffe – det hjälper till att "
        "hålla appen uppdaterad och fri från reklam. Tack! 🙏"
    ),
    "donate.open_btn": "☕ Öppna Ko-fi",
    "donate.copy_btn": "📋 Kopiera länk",
    "donate.copied": "Länken kopierad! 📋",
    "donate.not_configured": (
        "Ingen donationslänk är inlagd ännu.\n"
        "Ägaren kan klistra in sin Ko-fi-länk under "
        "Inställningar → ❤️ Stöd & om."
    ),
    "donate.group": "❤️ Stöd & om",
    "donate.url_label": "Donationslänk (Ko-fi)",
    "donate.url_placeholder": "https://ko-fi.com/dittnamn",
    "donate.open_settings_btn": "❤️ Öppna donationssidan",
    "donate.github_btn": "🐙 GitHub-projektet",
    "donate.invalid_url": "Donationslänken ser inte giltig ut – kontrollera den i Inställningar.",
    # Om-dialog
    "about.title": "Om E-postofferten",
    "about.text": (
        "📧 E-postofferten v{version}\nPyQt6 + Python 3.10+\n\n"
        "4-stegs wizard utan CC.\nMallar, offertförfrågan, To/Bcc.\n\n🐙 {repo_url}"
    ),
    # Inställningar (nya/ändrade rader)
    "settings.language_row": "Språk / Language",
    "settings.ui_group": "🎨 UI & Beteende",
    "donate.badges": "✨ GRATIS • UTAN REKLAM • PORTABEL",
    "donate.secure_line": "🔒 Säker betalning via PayPal, Ko-fi & Swish • ingen inloggning i appen",
    "donate.intro": (
        "E-postofferten gör offertmailen åt dig — välj mall, fyll i "
        "modell/reg/ruta och skicka på svenska och engelska. Inga "
        "prenumerationer. Ingen reklam. Din donation är det som gör "
        "att appen kan fortsätta — och bli ännu bättre."
    ),
    "donate.paypal_btn": "💙 Stöd via PayPal →",
    "donate.kofi_btn": "☕ Bjud på en kaffe (Ko-fi)",
    "donate.monthly_hint": "På Ko-fi kan du även bli månadsgivare — valfritt belopp, avsluta när du vill.",
    "donate.swish_title": "📱 Swish",
    "donate.swish_scan_hint": "Öppna Swish-appen, tryck Skanna och rikta kameran mot koden — fyll sedan i valfritt belopp.",
    "donate.swish_missing_lib": "QR-koden kunde inte ritas (paketet qrcode saknas) — swisha till numret ovan i stället.",
    "donate.swish_not_configured": "Inget Swish-nummer är inlagt ännu. Lägg in det under Inställningar → ❤️ Stöd & om så ritas QR-koden här direkt.",
    "donate.swish_number_copied": "Swish-numret kopierat! 📋",
    "donate.why1_title": "🧲 Rätt uppgifter varje gång",
    "donate.why1_body": "Modell, reg.nr och glastyp blir rätt ifyllda — offerten går iväg utan handpåläggning.",
    "donate.why2_title": "🛡️ Alltid uppdaterad",
    "donate.why2_body": "Buggfixar och nya funktioner löpande. Din donation = tid för underhåll.",
    "donate.why3_title": "💝 För alla — gratis",
    "donate.why3_body": "Ingen betalvägg. Donationer håller appen gratis för småföretag, verkstäder och kontor.",
    "donate.faq_title": "Vanliga frågor — lugnt & tryggt",
    "donate.faq1_q": "💳 Hur betalar jag säkert?",
    "donate.faq1_a": "Knapparna går direkt till paypal.me, ko-fi.com och Swish (HTTPS, krypterat). Varken appen eller utvecklaren ser ditt kortnummer. Kvitto kommer direkt från betaltjänsten.",
    "donate.faq2_q": "🔁 Kan jag bli månadsgivare?",
    "donate.faq2_a": "Ja! På Ko-fi kan du välja månadsvis (valfritt belopp, avsluta när du vill). På PayPal och Swish skickar du valfritt belopp när du vill — ingen bindning.",
    "donate.faq3_q": "🇸🇪 Fungerar Swish?",
    "donate.faq3_a": "Ja — när ett Swish-nummer är inlagt i appen (Inställningar → ❤️ Stöd & om) ritas QR-koden här direkt. Skanna den i Swish-appen och välj belopp själv.",
    "donate.faq4_q": "🎁 Vad får jag som tack?",
    "donate.faq4_a": "Evig tacksamhet, prioriterad återkoppling och känslan av att hålla appen gratis för alla. Ingen funktion låses bakom donation.",
    "donate.footer": "Byggd med ♥ i Sverige • Portabel • Ingen spårning",
    "donate.paypal_label": "Donationslänk (PayPal)",
    "donate.paypal_placeholder": "https://paypal.me/dittnamn",
    "donate.swish_label": "Swish-nummer (för QR-kod)",
    "donate.swish_placeholder": "070-123 45 67",
    "donate.defaults_hint": "Tomt fält = projektets standardlänk används.",
    "update.tray_title": "⬇️ Ny version av E-postofferten",
    "update.tray_text": "Version {latest} finns på GitHub. Öppna appen för att installera.",
}

_EN: Dict[str, str] = {
    # App shell
    "app.window_title": "📧 E-postofferten – Send step by step",
    "app.tagline_steps": "1. Template  →  2. Attachments/Images  →  3. Recipients  →  4. Send mail",
    "app.ready": "✅ Ready",
    "toolbar.send": "📤 Send",
    "toolbar.settings": "⚙️ Settings",
    "toolbar.new_template": "🧙 New template",
    "toolbar.donate": "❤️ Donate",
    # Menus
    "menu.file": "File",
    "menu.view": "View",
    "menu.theme": "Theme",
    "menu.language": "Language",
    "menu.help": "Help",
    "menu.send_mail": "📤 Send e-mail",
    "menu.new_template_wizard": "🧙 Create new template (wizard)…",
    "menu.save_template": "💾 Save template",
    "menu.backup_lists": "📦 Back up address lists…",
    "menu.update_from_folder": "⬇️ Update app from folder…",
    "menu.check_updates": "🔄 Check for updates…",
    "menu.quit": "❌ Quit",
    "menu.theme_dark": "🌙 Dark",
    "menu.theme_light": "☀️ Light",
    "menu.theme_system": "💻 System",
    "menu.deliverability": "📖 Deliverability guide",
    "menu.donate": "❤️ Donate – support the project",
    "menu.about": "ℹ️ About E-postofferten",
    "menu.show_all_tabs": "↩️ Show all",
    "menu.hide_tab": "🙈 Hide this tab",
    "language.sv": "🇸🇪 Swedish",
    "language.en": "🇬🇧 English",
    "language.changed_title": "Language changed",
    "language.changed_text": (
        "The language has been changed to {language}.\n\n"
        "Restart the app to show everything in the new language.\n"
        "Restart now?"
    ),
    "restart.failed": "Could not restart automatically – please start the app manually.",
    # Tabs
    "tab.send": "📤 Send",
    "tab.contacts": "👥 Contacts",
    "tab.templates": "📝 Templates",
    "tab.preview": "👁️ Preview",
    "tab.history": "📨 History",
    "tab.logs": "📜 Logs",
    "tab.settings": "⚙️ Settings",
    # Send-wizard steps
    "step1.title": "Template",
    "step1.hint": "Choose a template and fill in the details.",
    "step2.title": "Attachments/Images",
    "step2.hint": "Add images, PDFs or other files. Drag & drop is supported here.",
    "step3.title": "Recipients",
    "step3.hint": "Add To and Bcc. CC is not used.",
    "step4.title": "Send mail",
    "step4.hint": "Preview, confirm and send.",
    # Templates tab
    "templates_tab.heading": "Templates",
    "templates_tab.text": (
        "Create new templates with the wizard – step by step, in Swedish "
        "and English. Existing templates are edited in the Send flow or "
        "directly in the template folder."
    ),
    "templates_tab.wizard_btn": "🧙 Create new template with wizard…",
    "templates_tab.open_folder": "📂 Open template folder",
    "templates_tab.refresh": "🔄 Refresh list",
    "templates_tab.count": "{count} template(s) in {folder}",
    "templates_tab.empty": "No templates yet – create your first one with the wizard!",
    "templates_tab.use_hint": "Double-click a template to use it in the Send tab.",
    # Template wizard
    "wizard.title": "🧙 Create new template",
    "wizard.btn_back": "< Back",
    "wizard.btn_next": "Next >",
    "wizard.btn_finish": "💾 Create template",
    "wizard.btn_cancel": "Cancel",
    "wizard.page_start.title": "Step 1 – Name & format",
    "wizard.page_start.subtitle": "Name the template and choose how to start.",
    "wizard.name.label": "Template name:",
    "wizard.name.placeholder": "e.g. Car glass quote request",
    "wizard.format.label": "File format:",
    "wizard.format.txt": "TXT – simplest (recommended)",
    "wizard.format.html": "HTML – formatted mail",
    "wizard.format.docx": "DOCX – Word file",
    "wizard.start_from.label": "Start from:",
    "wizard.start.example": "Example: car glass quote request (SV + EN)",
    "wizard.start.blank": "Blank template",
    "wizard.start.copy": "Copy of existing template:",
    "wizard.filename.preview": "File name: {filename}",
    "wizard.page_sv.title": "Step 2 – Swedish text",
    "wizard.page_sv.subtitle": "Subject and body in Swedish. Fields like ::modell:: become input fields when sending.",
    "wizard.subject.label": "Subject:",
    "wizard.body.label": "Body:",
    "wizard.insert.label": "Insert field:",
    "wizard.insert.custom_btn": "➕ Custom…",
    "wizard.insert.custom_prompt": "Field name (e.g. price):",
    "wizard.page_en.title": "Step 3 – English text (optional)",
    "wizard.page_en.subtitle": "EN recipients automatically receive the English version.",
    "wizard.include_en": "Add English version ([en] block)",
    "wizard.en_body.label": "Body in English:",
    "wizard.translate_btn": "🌐 Auto-translate the Swedish text",
    "wizard.en.hint": (
        "The subject line is shared – field values are translated "
        "automatically when sending. Tip: ::vin:: is only shown in "
        "the English mail."
    ),
    "wizard.translate.failed": "Auto-translation failed – please write the text manually.",
    "wizard.page_preview.title": "Step 4 – Fields & preview",
    "wizard.page_preview.subtitle": "Check that the template looks right with test values.",
    "wizard.detected": "Fields found: {placeholders}",
    "wizard.detected.none": "No fields (placeholders) found – the template is sent as-is.",
    "wizard.test_values.label": "Test values:",
    "wizard.preview.sv": "🇸🇪 Swedish version",
    "wizard.preview.en": "🇬🇧 English version",
    "wizard.page_save.title": "Step 5 – Save the template",
    "wizard.page_save.subtitle": "Final check before saving to the template folder.",
    "wizard.summary": "File: {filename}\nFolder: {folder}\nFields: {placeholders}",
    "wizard.exists_warning": "⚠️ The file already exists and will be overwritten.",
    "wizard.set_default": "Use as default template at startup",
    "wizard.select_after": "Select the template in the Send tab right away",
    "wizard.error.title": "Check the template",
    "wizard.error.name_required": "Give the template a name.",
    "wizard.error.subject_required": "Enter a subject (Swedish).",
    "wizard.error.body_required": "Enter body text (Swedish).",
    "wizard.error.en_body_required": "Enter English body text – or uncheck the English version in step 3.",
    "wizard.error.save_failed": "Could not save the template:\n{error}",
    "wizard.created_status": "🧙 Template created: {name}",
    # Update (GitHub Releases)
    "update.title": "Update",
    "update.checking": "Checking GitHub for updates…",
    "update.available_title": "New version available! 🎉",
    "update.available_text": (
        "Version {latest} is available on GitHub (you have {current}).\n\n{notes}\n\n"
        "Download and install now? Your templates, address lists and "
        "settings are never touched."
    ),
    "update.install": "⬇️ Install now",
    "update.later": "Later",
    "update.release_page": "🌐 Release page",
    "update.up_to_date": "You already have the latest version ({current}). ✅",
    "update.no_releases": (
        "There is no published release on GitHub yet.\n\n"
        "The app can auto-update once a release has been published "
        "at {repo_url}/releases."
    ),
    "update.check_failed": "Could not check for updates:\n{error}",
    "update.downloading": "Downloading and installing version {latest}…",
    "update.installed_title": "Update complete ✅",
    "update.installed": (
        "The update has been installed ({count} files updated).\n\n"
        "Restart the app to use the new version. Restart now?"
    ),
    "update.install_failed": "The update failed:\n{error}",
    "update.status_available": "⬇️ New version {latest} is available on GitHub",
    "update.group": "🔄 Updates (GitHub)",
    "update.auto_check": "Automatically check for updates at startup (max once a day)",
    "update.current_version": "Installed version: {version}",
    "update.last_check": "Last check: {when}",
    "update.last_check_never": "Last check: never",
    "update.check_now_btn": "🔄 Check for updates now",
    "update.from_folder_btn": "⬇️ Update app from folder…",
    "update.folder_hint": (
        "Updating only copies code. Templates, JSON, address lists and "
        "settings are left untouched."
    ),
    # Donate
    "donate.title": "❤️ Donate",
    "donate.heading": "Support E-postofferten ❤️",
    "donate.text": (
        "E-postofferten is free to use. If the app saves you time, "
        "feel free to buy me a coffee – it helps keep the app updated "
        "and ad-free. Thank you! 🙏"
    ),
    "donate.open_btn": "☕ Open Ko-fi",
    "donate.copy_btn": "📋 Copy link",
    "donate.copied": "Link copied! 📋",
    "donate.not_configured": (
        "No donation link has been added yet.\n"
        "The owner can paste their Ko-fi link under "
        "Settings → ❤️ Support & about."
    ),
    "donate.group": "❤️ Support & about",
    "donate.url_label": "Donation link (Ko-fi)",
    "donate.url_placeholder": "https://ko-fi.com/yourname",
    "donate.open_settings_btn": "❤️ Open donation page",
    "donate.github_btn": "🐙 GitHub project",
    "donate.invalid_url": "The donation link does not look valid – check it in Settings.",
    # About dialog
    "about.title": "About E-postofferten",
    "about.text": (
        "📧 E-postofferten v{version}\nPyQt6 + Python 3.10+\n\n"
        "4-step wizard without CC.\nTemplates, quote requests, To/Bcc.\n\n🐙 {repo_url}"
    ),
    # Settings (new/changed rows)
    "settings.language_row": "Språk / Language",
    "settings.ui_group": "🎨 UI & behaviour",
    "donate.badges": "✨ FREE • NO ADS • PORTABLE",
    "donate.secure_line": "🔒 Secure payment via PayPal, Ko-fi & Swish • no login in the app",
    "donate.intro": (
        "E-postofferten writes your quote e-mails for you — pick a "
        "template, fill in model/reg/glass and send in Swedish and "
        "English. No subscriptions. No ads. Your donation keeps the "
        "app going — and makes it even better."
    ),
    "donate.paypal_btn": "💙 Support via PayPal →",
    "donate.kofi_btn": "☕ Buy me a coffee (Ko-fi)",
    "donate.monthly_hint": "On Ko-fi you can also give monthly — any amount, cancel anytime.",
    "donate.swish_title": "📱 Swish",
    "donate.swish_scan_hint": "Open the Swish app, tap Scan and point the camera at the code — then enter any amount.",
    "donate.swish_missing_lib": "The QR code could not be drawn (package qrcode missing) — please Swish the number above instead.",
    "donate.swish_not_configured": "No Swish number has been added yet. Add it under Settings → ❤️ Support & about and the QR code will appear here.",
    "donate.swish_number_copied": "Swish number copied! 📋",
    "donate.why1_title": "🧲 Right details every time",
    "donate.why1_body": "Model, reg no. and glass type filled in correctly — the quote goes out with no manual fiddling.",
    "donate.why2_title": "🛡️ Always up to date",
    "donate.why2_body": "Bug fixes and new features on a rolling basis. Your donation = maintenance time.",
    "donate.why3_title": "💝 For everyone — free",
    "donate.why3_body": "No paywall. Donations keep the app free for small businesses, workshops and offices.",
    "donate.faq_title": "FAQ — safe & simple",
    "donate.faq1_q": "💳 How do I pay securely?",
    "donate.faq1_a": "The buttons go straight to paypal.me, ko-fi.com and Swish (HTTPS, encrypted). Neither the app nor the developer sees your card number. The receipt comes directly from the payment service.",
    "donate.faq2_q": "🔁 Can I give monthly?",
    "donate.faq2_a": "Yes! On Ko-fi you can choose monthly (any amount, cancel anytime). With PayPal and Swish you send any amount whenever you like — no commitment.",
    "donate.faq3_q": "🇸🇪 Does Swish work?",
    "donate.faq3_a": "Yes — once a Swish number is added in the app (Settings → ❤️ Support & about) the QR code is drawn right here. Scan it in the Swish app and choose the amount yourself.",
    "donate.faq4_q": "🎁 What do I get in return?",
    "donate.faq4_a": "Eternal gratitude, priority feedback, and the feeling of keeping the app free for everyone. No feature is locked behind a donation.",
    "donate.footer": "Built with ♥ in Sweden • Portable • No tracking",
    "donate.paypal_label": "Donation link (PayPal)",
    "donate.paypal_placeholder": "https://paypal.me/yourname",
    "donate.swish_label": "Swish number (for QR code)",
    "donate.swish_placeholder": "070-123 45 67",
    "donate.defaults_hint": "Empty field = the project's default link is used.",
    "update.tray_title": "⬇️ New E-postofferten version",
    "update.tray_text": "Version {latest} is on GitHub. Open the app to install.",
}

STRINGS: Dict[str, Dict[str, str]] = {"sv": _SV, "en": _EN}


def tr(key: str, **kwargs: object) -> str:
    """Översätt ``key`` till aktuellt språk.

    Fallback: aktuellt språk → svenska → nyckeln själv. Extra
    nyckelordsargument formateras in med ``str.format``; saknade
    parametrar ger originaltexten (aldrig exception).
    """
    table = STRINGS.get(_current_language, _SV)
    text = table.get(key)
    if text is None:
        text = _SV.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)  # type: ignore[arg-type]
        except (KeyError, IndexError, ValueError):
            log.debug("i18n: formatfel för nyckel %r", key)
            return text
    return text


def missing_keys(language: str = "en") -> List[str]:
    """Nycklar som finns i SV men saknas i ``language`` (för tester)."""
    lang = normalize_language(language)
    return sorted(set(_SV) - set(STRINGS.get(lang, {})))


__all__ = [
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "STRINGS",
    "available_languages",
    "get_language",
    "missing_keys",
    "normalize_language",
    "set_language",
    "tr",
]
