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
    "templates_tab.edit_btn": "✏️ Redigera vald mall…",
    "templates_tab.versions_btn": "🕘 Versioner…",
    "templates_tab.pack_btn": "📦 Mallpaket…",
    "templates_tab.select_first": "Välj en mall i listan först.",
    # E-postlistor
    "emaillist.import_btn": "📥 Importera e-postlista",
    "emaillist.paste_btn": "📋 Klistra in lista",
    "emaillist.paste_contacts_title": "📋 Klistra in e-postlista",
    "emaillist.paste_recipients_title": "📋 Klistra in mottagare i {target}",
    "emaillist.list_name_label": "Listnamn/kategori:",
    "emaillist.list_name_placeholder": "t.ex. Bilglas Stockholm",
    "emaillist.language_label": "Språk för nya kontakter:",
    "emaillist.text_label": "E-postadresser/kontakter:",
    "emaillist.text_placeholder": "anna@example.se\nNamn <namn@example.se>\neller kopiera rader från Excel/CSV…",
    "emaillist.hint": "En adress per rad eller avgränsade med komma/semikolon. CSV med rubriker och kopierade Excel-celler fungerar också.",
    "emaillist.import_action": "Importera",
    "emaillist.empty_text": "Klistra in minst en e-postadress.",
    "emaillist.file_title": "Importera e-postlista",
    "emaillist.file_filter": "E-postlistor (*.csv *.txt *.tsv);;CSV-filer (*.csv);;Textfiler (*.txt *.tsv);;Alla filer (*.*)",
    "emaillist.category_prompt": "Alla adresser i filen sparas i denna kategori/lista (lämna tomt = filnamnet):",
    "emaillist.default_category": "Importerad lista",
    "emaillist.done_title": "✅ Import klar",
    "emaillist.contacts_stats": "Tillagda: {added}\nUppdaterade: {updated}\nDubbletter/utan ändring: {duplicates}\nOgiltiga rader: {invalid}",
    "emaillist.failed_title": "❌ Import misslyckades",
    "emaillist.no_valid": "Inga giltiga e-postadresser hittades.",
    "emaillist.save_contacts": "Spara adresserna i adressboken också",
    "emaillist.added_status": "📋 {added} adress(er) lades till i {target} · {duplicates} dubbletter · {invalid} ogiltiga",
    "emaillist.no_new_status": "ℹ️ Inga nya adresser att lägga till i {target} · {duplicates} dubbletter · {invalid} ogiltiga",
    "emaillist.many_placeholder": "namn@example.se eller flera med ; eller ,",
    "emaillist.export_category_btn": "📄 Exportera kategori (.txt)",
    "emaillist.export_category_title": "Exportera kategori till textfil",
    "emaillist.export_category_label": "Välj kategori:",
    "emaillist.export_all_categories": "📁 Alla kategorier (en fil per kategori)",
    "emaillist.export_txt_filter": "Textfiler (*.txt);;Alla filer (*.*)",
    "emaillist.export_folder_title": "Välj mapp för kategorifiler",
    "emaillist.no_categories": "Det finns inga kategorier att exportera ännu. Importera en e-postlista eller lägg en kategori på en kontakt först.",
    "emaillist.export_category_saved": "{count} e-postadress(er) i kategorin '{category}' exporterades till {filename}. Adresserna är separerade med semikolon.",
    "emaillist.export_categories_saved": "{files} kategorifil(er) med totalt {count} adresser exporterades till mappen {folder}.",
    "emaillist.export_failed_title": "❌ Export misslyckades",
    "emaillist.export_done_title": "✅ Export klar",
    # Avsändarprofiler + testläge/förhandskontroll (v5.5)
    "profile.label": "Avsändarprofil:",
    "smtp.provider_label": "E-postleverantör:",
    "smtp.provider_manual": "Annan / egen server (manuellt)",
    "smtp.provider_applied": "SMTP-inställningar ifyllda för {provider}",
    "smtp.app_password_btn": "🔑 Öppna sidan för applösenord",
    "smtp.preset_note.gmail": "Gmail kräver ett applösenord (vid tvåstegsverifiering) – skapa ett via knappen nedan och använd det som lösenord här.",
    "smtp.preset_note.outlook": "Microsoft kan kräva ett applösenord eller modern inloggning. Om vanlig inloggning nekas: skapa ett applösenord via knappen nedan.",
    "smtp.preset_note.office365": "Microsoft 365: SMTP-inloggning måste vara aktiverad för kontot av administratören (SMTP AUTH). Använd hela e-postadressen som användarnamn.",
    "smtp.preset_note.yahoo": "Yahoo kräver ett applösenord – skapa ett under Kontosäkerhet via knappen nedan och använd det som lösenord här.",
    "smtp.preset_note.icloud": "iCloud kräver ett appspecifikt lösenord – skapa ett under Inloggning och säkerhet via knappen nedan.",
    "smtp.preset_note.webhotel": "Webbhotell: använd hela e-postadressen som användarnamn och samma lösenord som till webbmailen/kontrollpanelen.",
    "smtp.preset_note.websupport": "WebSupport: använd hela e-postadressen som användarnamn. Om kontrollpanelen visar en nodserver, t.ex. smtp.m101.websupport.se, använd exakt det namnet i stället för smtp.websupport.se. Port 465 kräver SSL; port 587 används med SSL av (STARTTLS).",
    "smtp.preset_note.webhotel_generic": "De flesta webbhotell använder mail.dindomän.se med port 465 (SSL) – servern fylls i från din avsändaradress. Fungerar inte SMTP-testet: prova port 587 och bocka ur SSL, eller hämta exakt servernamn i webbhotellets kontrollpanel. Användarnamn är nästan alltid hela e-postadressen.",
    "smtp.dns_btn": "🌐 Kontrollera SPF/DKIM/DMARC för avsändardomänen",
    "smtp.dns_running": "Kontrollerar DNS för {domain} …",
    "smtp.dns_no_domain": "Fyll först i en avsändaradress med giltig domän under 📡 SMTP & Avsändare.",
    "smtp.dns_ok": "✅ hittad",
    "smtp.dns_missing": "⚠️ saknas",
    "smtp.dns_error_status": "❌ kunde inte kontrolleras",
    "smtp.dns_result": "DNS för {domain}:\n• SPF: {spf}\n• DMARC: {dmarc}\n• DKIM: {dkim}",
    "smtp.dns_dmarc_policy": " (policy: {policy})",
    "smtp.dns_dkim_selectors": " (selektor: {selectors})",
    "smtp.dns_hint": "Saknade poster minskar leveranssäkerheten – se leveransbarhets-guiden ovan för färdiga DNS-poster att kopiera.",
    "smtp.dns_failed": "DNS-kontrollen misslyckades: {error}",
    'tb.title': 'Thunderbird-koppling',
    'tb.unknown': 'Inte testad. Thunderbird-tilläggets installationsstatus är okänd.',
    'tb.register': 'Registrera kopplingen',
    'tb.xpi': 'Installera Thunderbird-tillägg …',
    'tb.test': 'Testa lokal brygga',
    'tb.help': 'Installera XPI i Thunderbird via Tillägg och teman → kugghjulet → Installera tillägg från fil. Högerklicka sedan på en e-postlänk. Kontakter uppdateras automatiskt medan appen är öppen.',
    'tb.registered': 'Kopplingen registrerad: {path}. Installera även XPI i Thunderbird.',
    'tb.failed': 'Kunde inte hitta eller registrera Thunderbird-kopplingen.',
    'tb.install': 'Välj denna fil i Thunderbirds tilläggshanterare:\n{path}\n\nRegistrera kopplingen med knappen i appen först.',
    'tb.test_ok': 'Lokal brygga fungerar. XPI-installationen i Thunderbird kan inte verifieras här; prova att skicka en adress med högerklick.',
    'tb.test_error': 'Test misslyckades: {error}',
    'tb.received': 'Kontaktfilen ändrades och kontaktlistan har uppdaterats. Källa kan vara Thunderbird eller en annan lokal ändring.',
    'tb.path_mismatch': 'Bryggan fungerar men skriver till en annan kontaktmapp än appens valda adressmapp. Thunderbird använder adresslistor i appmappen.',
    'signature.preview': 'Signaturförhandsvisning',
    'signature.empty': 'Ingen profilsignatur.',
    'signature.error': 'Kan inte visa signaturen: {error}',
    'safety.templates': 'Tillåtna profiler för vald mall …',
    'safety.all_profiles': 'Tillåt alla profiler (även framtida)',
    'safety.forbidden': 'Mallen är inte tillåten för den valda avsändarprofilen. Välj en annan mall eller profil.',
    'safety.save_failed': 'Kunde inte spara mallens profilregler.',
    'safety.duplicate_title': 'Risk för dubbelt utskick',
    'safety.duplicate': 'Samma innehåll har skickats de senaste 24 timmarna till: {emails}. Vill du verkligen skicka igen?',
    'safety.tls': 'WebSupport: använd port 465 med SSL eller port 587 med STARTTLS.',
    'safety.sender': 'WebSupport: avsändaradressen skiljer sig från inloggningen. Kontrollera att kontot får skicka för adressen och att domänerna är autentiserade.',
    'safety.dns': 'WebSupport: kör DNS-kontroll under Inställningar och verifiera SPF, DKIM och DMARC i ett mottaget testmejls Authentication-Results. Ingen kontroll garanterar att mejlet inte hamnar i skräppost.',
    "safety.dns_limit": "DNS-kontrollen bekräftar inte faktisk signering eller leverans. DKIM kan använda en annan selektor än de provade. Kontrollera Authentication-Results i mottaget testmejl.",
    "safety.choose_template": "Välj mall att hantera (alla mallar visas här):",
    'profile.color': 'Profilfärg',
    'profile.choose_color': 'Välj färg …',
    'keys.title': 'Tangentbord och genvägar',
    'keys.template': 'Välj mall (Ctrl+M)',
    'keys.subject': 'Ämne',
    'keys.body': 'Mejltext',
    'keys.free': 'Fritext',
    'keys.help': 'Ctrl+L: välj avsändarprofil\nCtrl+M: välj mall\nCtrl+K: sök kontakter\nCtrl+1–4: gå till utskickets steg\nF5: förhandsvisa\nCtrl+Shift+T: testmejl (frågar efter adress)\nCtrl+Enter: öppna sändbekräftelse\nCtrl+S: spara mall\nCtrl+Q: avsluta\nTab/Shift+Tab: nästa/föregående fält\nF1: visa denna hjälp',
    "backup.group": "💾 Säkerhetskopiering",
    "backup.info": "Säkerhetskopian är en ZIP med kontakter/kategorier, mallar, sändhistorik och inställningar (inkl. avsändarprofiler). Lösenord följer ALDRIG med – de måste fyllas i igen efter återställning.",
    "backup.create_btn": "💾 Skapa säkerhetskopia …",
    "backup.restore_btn": "♻️ Återställ säkerhetskopia …",
    "backup.create_title": "Spara säkerhetskopia",
    "backup.create_done": "Säkerhetskopian är sparad:\n{path}\n\nFiler: {files} ({sections})\n\nKom ihåg: SMTP-lösenord ingår inte.",
    "backup.restore_title": "Välj säkerhetskopia att återställa",
    "backup.invalid": "Filen kunde inte läsas som en säkerhetskopia:\n{error}",
    "backup.confirm": "Säkerhetskopia skapad {created} (appversion {version}).\nInnehåll: {sections}\n\nNuvarande kontakter, mallar, historik och inställningar ersätts. En automatisk säkerhetskopia av nuvarande data sparas först.\n\nSMTP-lösenord måste fyllas i igen efteråt.\n\nVill du återställa?",
    "backup.restored": "Säkerhetskopian är återställd.\n\nSäkerhetskopia av tidigare data:\n{safety}\n\nAppen behöver startas om för att läsa in återställda inställningar.",
    "backup.restart_now": "🔄 Starta om nu",
    "backup.later": "Senare",
    "backup.failed": "Det gick inte att slutföra åtgärden:\n{error}",
    "backup.section_settings": "inställningar",
    "backup.section_adresslistor": "kontakter",
    "backup.section_mallar": "mallar",
    "backup.section_history": "historik",
    "profile.save_btn": "💾 Spara profil",
    "profile.new_btn": "➕ Ny profil",
    "profile.delete_btn": "🗑️ Ta bort",
    "profile.name_prompt": "Profilnamn:",
    "profile.new_title": "Ny avsändarprofil",
    "profile.save_title": "Spara avsändarprofil",
    "profile.saved_status": "👤 Avsändarprofil sparad: {name}",
    "profile.deleted_status": "🗑️ Avsändarprofil borttagen: {name}",
    "profile.delete_confirm": "Ta bort avsändarprofilen '{name}'?",
    "profile.loaded_status": "👤 Avsändarprofil vald: {name}",
    "profile.summary": "Avsändare: {name} <{email}>",
    "send.preflight_btn": "🔎 Förhandskontroll",
    "send.test_btn": "🧪 Skicka testmail",
    "send.preflight_title": "🔎 Förhandskontroll",
    "send.test_title": "🧪 Skicka testmail",
    "send.test_prompt": "Testadress (bara denna adress får mailet):",
    "send.test_invalid": "Ange en giltig testadress.",
    "send.test_done_title": "🧪 Testmail skickat",
    "send.test_done_text": "Testmailet skickades bara till {email}. De vanliga mottagarna, standard-Bcc och arkivkopian användes inte.",
    "send.test_banner": "🧪 TESTUTSKICK – detta mail har bara skickats till testadressen.",
    "send.preflight.sender": "Avsändare: {name} <{email}>",
    "send.preflight.smtp": "SMTP: {server}:{port}",
    "send.preflight.recipients": "Mottagare: {total} (Till {to}, Bcc {bcc})",
    "send.preflight.languages": "Språk: SV {sv} · EN {en}",
    "send.preflight.attachments": "Bilagor: {count} ({size})",
    "send.preflight.no_blockers": "✅ Inga stoppande fel hittades.",
    "send.preflight.blockers": "⛔ Måste åtgärdas:",
    "send.preflight.warnings": "⚠️ Varningar:",
    "send.preflight.blocked_title": "Förhandskontrollen stoppar sändningen",
    "send.issue.no_recipients": "Inga mottagare.",
    "send.issue.missing_smtp_server": "SMTP-server saknas i avsändarprofilen.",
    "send.issue.invalid_smtp_port": "SMTP-porten är ogiltig: {port}.",
    "send.issue.invalid_sender": "Avsändaradressen ser ogiltig ut: {email}.",
    "send.issue.missing_template": "Mallfilen saknas: {template}.",
    "send.issue.invalid_recipients": "Ogiltiga mottagare: {emails}.",
    "send.issue.missing_attachments": "Bilagor som saknas: {files}.",
    "send.issue.overlap": "Samma adress i både Till och Bcc: {emails}. Bcc-versionen tas bort vid sändning.",
    "send.issue.invalid_recipients_skipped": "Ogiltiga adresser hoppas över: {emails}.",
    "send.issue.missing_subject": "Ämnesraden är tom.",
    "send.issue.missing_placeholders": "Uppgifter utan värde: {keys}.",
    "send.issue.many_recipients": "Stort utskick: {total} mottagare. Kontrollera leverantörens gränser.",
    "send.issue.bcc_no_batch": "{count} Bcc-mottagare utan batchstorlek satt. Överväg BCC batch size i Inställningar.",
    "send.issue.missing_username": "SMTP-användarnamn saknas i profilen.",
    "send.issue.missing_password": "SMTP-lösenord saknas i profilen.",
    "send.issue.domain_mismatch": "Avsändardomänen ({sender_domain}) skiljer sig från inloggningens domän ({username_domain}). Kontrollera att kontot får skicka som avsändaren.",
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
    "wizard.edit_title": "✏️ Redigera mall",
    "wizard.btn_finish_edit": "💾 Spara ändringar",
    "wizard.start.pack": "Färdig mall från mallpaket:",
    "wizard.editing_info": "Du redigerar en befintlig mall. Filnamnet behålls, och tidigare innehåll sparas automatiskt som en version innan ändringarna skrivs.",
    "wizard.version_saved_note": "🕘 Tidigare version sparas automatiskt och kan återställas via Mallar → Versioner.",
    "wizard.updated_status": "✏️ Mall uppdaterad: {name}",
    "wizard.error.load_failed": "Kunde inte läsa den befintliga mallen:\n{error}",
    "template_versions.title": "🕘 Mallversioner – {name}",
    "template_versions.text": "Välj en tidigare version för att förhandsgranska eller återställa den. Nuvarande mall sparas automatiskt först.",
    "template_versions.empty": "Inga tidigare versioner ännu. En version sparas automatiskt när mallen redigeras och sparas.",
    "template_versions.snapshot_btn": "📌 Spara nuvarande som version",
    "template_versions.restore_btn": "♻️ Återställ vald version",
    "template_versions.delete_btn": "🗑️ Ta bort vald version",
    "template_versions.close": "Stäng",
    "template_versions.preview_title": "Förhandsgranskning",
    "template_versions.confirm_restore": "Återställ mallen till versionen från {when}?\n\nNuvarande mall sparas först som en ny version.",
    "template_versions.confirm_delete": "Ta bort versionen från {when} permanent?",
    "template_versions.restored_status": "🕘 Mall återställd: {name}",
    "template_versions.saved_status": "📌 Mallversion sparad: {name}",
    "template_versions.deleted_status": "🗑️ Mallversion borttagen",
    "template_versions.error": "Det gick inte att hantera mallversionen:\n{error}",
    "template_packs.title": "📦 Färdiga mallpaket",
    "template_packs.text": "Välj mallar att kopiera till din mallmapp. Mallar som redan finns skrivs aldrig över.",
    "template_packs.install_btn": "📥 Kopiera valda mallar",
    "template_packs.cancel": "Avbryt",
    "template_packs.select_none": "Välj minst en mall.",
    "template_packs.result": "Kopierade {created} mall(ar). {skipped} hoppades över eftersom de redan fanns.",
    "template_packs.installed_status": "📦 {count} paketmall(ar) kopierade",
    "template_packs.error": "Kunde inte installera mallpaketet:\n{error}",
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
        "GitHub-releasen kunde inte nås (HTTP 404).\n\n"
        "Det kan bero på en saknad release eller ett privat repo. Appen har ingen GitHub-inloggning. Kontrollera åtkomsten "
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
    "update.files_changed_title": "Uppdaterade filer finns! 🎉",
    "update.files_changed_text": (
        "Filerna i version {latest} har uppdaterats på GitHub (du har samma version, {current}).\n\n{notes}\n\n"
        "Ladda ner och installera de uppdaterade filerna nu? Dina mallar, "
        "adresslistor och inställningar rörs aldrig."
    ),
    "update.status_files_changed": "⬇️ Uppdaterade filer för version {latest} finns på GitHub",
    "update.tray_files_changed_text": "Filerna i version {latest} har uppdaterats på GitHub. Öppna appen för att installera.",
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
    "templates_tab.edit_btn": "✏️ Edit selected template…",
    "templates_tab.versions_btn": "🕘 Versions…",
    "templates_tab.pack_btn": "📦 Template packs…",
    "templates_tab.select_first": "Select a template in the list first.",
    # Email lists
    "emaillist.import_btn": "📥 Import email list",
    "emaillist.paste_btn": "📋 Paste list",
    "emaillist.paste_contacts_title": "📋 Paste email list",
    "emaillist.paste_recipients_title": "📋 Paste recipients into {target}",
    "emaillist.list_name_label": "List name/category:",
    "emaillist.list_name_placeholder": "e.g. Car glass Stockholm",
    "emaillist.language_label": "Language for new contacts:",
    "emaillist.text_label": "Email addresses/contacts:",
    "emaillist.text_placeholder": "anna@example.com\nName <name@example.com>\nor copy rows from Excel/CSV…",
    "emaillist.hint": "One address per line or separated by commas/semicolons. Headed CSV files and copied Excel cells work too.",
    "emaillist.import_action": "Import",
    "emaillist.empty_text": "Paste at least one email address.",
    "emaillist.file_title": "Import email list",
    "emaillist.file_filter": "Email lists (*.csv *.txt *.tsv);;CSV files (*.csv);;Text files (*.txt *.tsv);;All files (*.*)",
    "emaillist.category_prompt": "All addresses in the file will be saved in this category/list (leave empty = file name):",
    "emaillist.default_category": "Imported list",
    "emaillist.done_title": "✅ Import complete",
    "emaillist.contacts_stats": "Added: {added}\nUpdated: {updated}\nDuplicates/unchanged: {duplicates}\nInvalid rows: {invalid}",
    "emaillist.failed_title": "❌ Import failed",
    "emaillist.no_valid": "No valid email addresses were found.",
    "emaillist.save_contacts": "Also save the addresses in the address book",
    "emaillist.added_status": "📋 {added} address(es) added to {target} · {duplicates} duplicates · {invalid} invalid",
    "emaillist.no_new_status": "ℹ️ No new addresses to add to {target} · {duplicates} duplicates · {invalid} invalid",
    "emaillist.many_placeholder": "name@example.com or several separated by ; or ,",
    "emaillist.export_category_btn": "📄 Export category (.txt)",
    "emaillist.export_category_title": "Export category to a text file",
    "emaillist.export_category_label": "Choose a category:",
    "emaillist.export_all_categories": "📁 All categories (one file per category)",
    "emaillist.export_txt_filter": "Text files (*.txt);;All files (*.*)",
    "emaillist.export_folder_title": "Choose a folder for the category files",
    "emaillist.no_categories": "There are no categories to export yet. Import an email list or add a category to a contact first.",
    "emaillist.export_category_saved": "{count} email address(es) in category '{category}' were exported to {filename}. The addresses are separated by semicolons.",
    "emaillist.export_categories_saved": "{files} category file(s) with {count} addresses in total were exported to the folder {folder}.",
    "emaillist.export_failed_title": "❌ Export failed",
    "emaillist.export_done_title": "✅ Export complete",
    # Sender profiles + test mode/preflight (v5.5)
    "profile.label": "Sender profile:",
    "smtp.provider_label": "Email provider:",
    "smtp.provider_manual": "Other / custom server (manual)",
    "smtp.provider_applied": "SMTP settings filled in for {provider}",
    "smtp.app_password_btn": "🔑 Open the app password page",
    "smtp.preset_note.gmail": "Gmail requires an app password (with two-step verification) – create one via the button below and use it as the password here.",
    "smtp.preset_note.outlook": "Microsoft may require an app password or modern sign-in. If a normal login is refused, create an app password via the button below.",
    "smtp.preset_note.office365": "Microsoft 365: SMTP login must be enabled for the account by the administrator (SMTP AUTH). Use the full email address as the username.",
    "smtp.preset_note.yahoo": "Yahoo requires an app password – create one under Account security via the button below and use it as the password here.",
    "smtp.preset_note.icloud": "iCloud requires an app-specific password – create one under Sign-In and Security via the button below.",
    "smtp.preset_note.webhotel": "Web hosting: use the full email address as the username and the same password as for webmail/the control panel.",
    "smtp.preset_note.websupport": "WebSupport: use the full email address as the username. If the control panel shows a node server, e.g. smtp.m101.websupport.se, use that exact name instead of smtp.websupport.se. Port 465 requires SSL; port 587 is used with SSL off (STARTTLS).",
    "smtp.preset_note.webhotel_generic": "Most web hosts use mail.yourdomain.com with port 465 (SSL) – the server is filled in from your sender address. If the SMTP test fails, try port 587 with SSL unchecked, or look up the exact server name in your host's control panel. The username is almost always the full email address.",
    "smtp.dns_btn": "🌐 Check SPF/DKIM/DMARC for the sender domain",
    "smtp.dns_running": "Checking DNS for {domain} …",
    "smtp.dns_no_domain": "First enter a sender address with a valid domain under 📡 SMTP & Sender.",
    "smtp.dns_ok": "✅ found",
    "smtp.dns_missing": "⚠️ missing",
    "smtp.dns_error_status": "❌ could not be checked",
    "smtp.dns_result": "DNS for {domain}:\n• SPF: {spf}\n• DMARC: {dmarc}\n• DKIM: {dkim}",
    "smtp.dns_dmarc_policy": " (policy: {policy})",
    "smtp.dns_dkim_selectors": " (selector: {selectors})",
    "smtp.dns_hint": "Missing records reduce deliverability – see the deliverability guide above for ready-to-copy DNS records.",
    "smtp.dns_failed": "The DNS check failed: {error}",
    'tb.title': 'Thunderbird connection',
    'tb.unknown': 'Not tested. Thunderbird extension installation status is unknown.',
    'tb.register': 'Register connection',
    'tb.xpi': 'Install Thunderbird extension …',
    'tb.test': 'Test local bridge',
    'tb.help': 'Install the XPI in Thunderbird via Add-ons and Themes → gear → Install Add-on From File. Then right-click an email link. Contacts refresh automatically while the app is open.',
    'tb.registered': 'Connection registered: {path}. Also install the XPI in Thunderbird.',
    'tb.failed': 'Could not find or register the Thunderbird connection.',
    'tb.install': 'Select this file in Thunderbird’s add-on manager:\n{path}\n\nRegister the connection using the app button first.',
    'tb.test_ok': 'Local bridge works. Thunderbird XPI installation cannot be verified here; try sending an address using right-click.',
    'tb.test_error': 'Test failed: {error}',
    'tb.received': 'Contact file changed and contacts have refreshed. The source may be Thunderbird or another local change.',
    'tb.path_mismatch': 'Bridge works but writes to a different contact folder than the app. Thunderbird uses adresslistor in the app folder.',
    'signature.preview': 'Signature preview',
    'signature.empty': 'No profile signature.',
    'signature.error': 'Cannot preview signature: {error}',
    'safety.templates': 'Allowed profiles for selected template …',
    'safety.all_profiles': 'Allow all profiles (including future profiles)',
    'safety.forbidden': 'This template is not allowed for the selected sender profile. Choose another template or profile.',
    'safety.save_failed': 'Could not save template profile rules.',
    'safety.duplicate_title': 'Possible duplicate send',
    'safety.duplicate': 'The same content was sent in the last 24 hours to: {emails}. Do you really want to send again?',
    'safety.tls': 'WebSupport: use port 465 with SSL or port 587 with STARTTLS.',
    'safety.sender': 'WebSupport: sender differs from login. Check that the account is authorized to send for this address and the domains are authenticated.',
    'safety.dns': 'WebSupport: run the DNS check in Settings and verify SPF, DKIM and DMARC in a received test message’s Authentication-Results. No check can guarantee inbox placement.',
    "safety.dns_limit": "DNS checks do not verify actual signing or delivery. DKIM may use a selector not tested here. Check Authentication-Results in a received test message.",
    "safety.choose_template": "Choose template to manage (all templates are shown here):",
    'profile.color': 'Profile colour',
    'profile.choose_color': 'Choose colour …',
    'keys.title': 'Keyboard shortcuts',
    'keys.template': 'Choose template (Ctrl+M)',
    'keys.subject': 'Subject',
    'keys.body': 'Message body',
    'keys.free': 'Additional text',
    'keys.help': 'Ctrl+L: choose sender profile\nCtrl+M: choose template\nCtrl+K: search contacts\nCtrl+1–4: jump to send steps\nF5: preview\nCtrl+Shift+T: test email (asks for address)\nCtrl+Enter: open send confirmation\nCtrl+S: save template\nCtrl+Q: quit\nTab/Shift+Tab: next/previous field\nF1: show this help',
    "backup.group": "💾 Backup",
    "backup.info": "The backup is a ZIP containing contacts/categories, templates, send history and settings (incl. sender profiles). Passwords are NEVER included – they must be entered again after a restore.",
    "backup.create_btn": "💾 Create backup …",
    "backup.restore_btn": "♻️ Restore backup …",
    "backup.create_title": "Save backup",
    "backup.create_done": "The backup was saved:\n{path}\n\nFiles: {files} ({sections})\n\nRemember: SMTP passwords are not included.",
    "backup.restore_title": "Choose a backup to restore",
    "backup.invalid": "The file could not be read as a backup:\n{error}",
    "backup.confirm": "Backup created {created} (app version {version}).\nContents: {sections}\n\nYour current contacts, templates, history and settings will be replaced. An automatic backup of your current data is saved first.\n\nSMTP passwords must be entered again afterwards.\n\nDo you want to restore?",
    "backup.restored": "The backup has been restored.\n\nBackup of your previous data:\n{safety}\n\nThe app needs to restart to load the restored settings.",
    "backup.restart_now": "🔄 Restart now",
    "backup.later": "Later",
    "backup.failed": "The operation could not be completed:\n{error}",
    "backup.section_settings": "settings",
    "backup.section_adresslistor": "contacts",
    "backup.section_mallar": "templates",
    "backup.section_history": "history",
    "profile.save_btn": "💾 Save profile",
    "profile.new_btn": "➕ New profile",
    "profile.delete_btn": "🗑️ Delete",
    "profile.name_prompt": "Profile name:",
    "profile.new_title": "New sender profile",
    "profile.save_title": "Save sender profile",
    "profile.saved_status": "👤 Sender profile saved: {name}",
    "profile.deleted_status": "🗑️ Sender profile deleted: {name}",
    "profile.delete_confirm": "Delete the sender profile '{name}'?",
    "profile.loaded_status": "👤 Sender profile selected: {name}",
    "profile.summary": "Sender: {name} <{email}>",
    "send.preflight_btn": "🔎 Preflight check",
    "send.test_btn": "🧪 Send test email",
    "send.preflight_title": "🔎 Preflight check",
    "send.test_title": "🧪 Send test email",
    "send.test_prompt": "Test address (only this address will receive the email):",
    "send.test_invalid": "Enter a valid test address.",
    "send.test_done_title": "🧪 Test email sent",
    "send.test_done_text": "The test email was sent only to {email}. The normal recipients, default Bcc and archive copy were not used.",
    "send.test_banner": "🧪 TEST SEND – this email was sent only to the test address.",
    "send.preflight.sender": "Sender: {name} <{email}>",
    "send.preflight.smtp": "SMTP: {server}:{port}",
    "send.preflight.recipients": "Recipients: {total} (To {to}, Bcc {bcc})",
    "send.preflight.languages": "Languages: SV {sv} · EN {en}",
    "send.preflight.attachments": "Attachments: {count} ({size})",
    "send.preflight.no_blockers": "✅ No blocking problems were found.",
    "send.preflight.blockers": "⛔ Must be fixed:",
    "send.preflight.warnings": "⚠️ Warnings:",
    "send.preflight.blocked_title": "The preflight check blocks sending",
    "send.issue.no_recipients": "No recipients.",
    "send.issue.missing_smtp_server": "The SMTP server is missing in the sender profile.",
    "send.issue.invalid_smtp_port": "The SMTP port is invalid: {port}.",
    "send.issue.invalid_sender": "The sender address looks invalid: {email}.",
    "send.issue.missing_template": "The template file is missing: {template}.",
    "send.issue.invalid_recipients": "Invalid recipients: {emails}.",
    "send.issue.missing_attachments": "Missing attachments: {files}.",
    "send.issue.overlap": "Same address in both To and Bcc: {emails}. The Bcc copy will be removed when sending.",
    "send.issue.invalid_recipients_skipped": "Invalid addresses will be skipped: {emails}.",
    "send.issue.missing_subject": "The subject line is empty.",
    "send.issue.missing_placeholders": "Fields without a value: {keys}.",
    "send.issue.many_recipients": "Large send: {total} recipients. Check your provider limits.",
    "send.issue.bcc_no_batch": "{count} Bcc recipients with no batch size set. Consider BCC batch size in Settings.",
    "send.issue.missing_username": "The SMTP username is missing in the profile.",
    "send.issue.missing_password": "The SMTP password is missing in the profile.",
    "send.issue.domain_mismatch": "The sender domain ({sender_domain}) differs from the login domain ({username_domain}). Check that the account may send as this sender.",
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
    "wizard.edit_title": "✏️ Edit template",
    "wizard.btn_finish_edit": "💾 Save changes",
    "wizard.start.pack": "Ready-made template from a pack:",
    "wizard.editing_info": "You are editing an existing template. The file name is kept, and the previous contents are automatically saved as a version before your changes are written.",
    "wizard.version_saved_note": "🕘 The previous version is saved automatically and can be restored via Templates → Versions.",
    "wizard.updated_status": "✏️ Template updated: {name}",
    "wizard.error.load_failed": "Could not read the existing template:\n{error}",
    "template_versions.title": "🕘 Template versions – {name}",
    "template_versions.text": "Select a previous version to preview or restore it. The current template is saved automatically first.",
    "template_versions.empty": "No previous versions yet. A version is saved automatically when the template is edited and saved.",
    "template_versions.snapshot_btn": "📌 Save current as a version",
    "template_versions.restore_btn": "♻️ Restore selected version",
    "template_versions.delete_btn": "🗑️ Delete selected version",
    "template_versions.close": "Close",
    "template_versions.preview_title": "Preview",
    "template_versions.confirm_restore": "Restore the template to the version from {when}?\n\nThe current template will first be saved as a new version.",
    "template_versions.confirm_delete": "Permanently delete the version from {when}?",
    "template_versions.restored_status": "🕘 Template restored: {name}",
    "template_versions.saved_status": "📌 Template version saved: {name}",
    "template_versions.deleted_status": "🗑️ Template version deleted",
    "template_versions.error": "Could not manage the template version:\n{error}",
    "template_packs.title": "📦 Ready-made template packs",
    "template_packs.text": "Choose templates to copy to your template folder. Existing templates are never overwritten.",
    "template_packs.install_btn": "📥 Copy selected templates",
    "template_packs.cancel": "Cancel",
    "template_packs.select_none": "Select at least one template.",
    "template_packs.result": "Copied {created} template(s). {skipped} were skipped because they already existed.",
    "template_packs.installed_status": "📦 {count} pack template(s) copied",
    "template_packs.error": "Could not install the template pack:\n{error}",
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
        "The GitHub release could not be accessed (HTTP 404).\n\n"
        "The release may be missing or the repository private. The app has no GitHub authentication. Check access "
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
    "update.files_changed_title": "Updated files are available! 🎉",
    "update.files_changed_text": (
        "The files in version {latest} have been updated on GitHub (you have the same version, {current}).\n\n{notes}\n\n"
        "Download and install the updated files now? Your templates, "
        "address lists and settings are never touched."
    ),
    "update.status_files_changed": "⬇️ Updated files for version {latest} are available on GitHub",
    "update.tray_files_changed_text": "The files in version {latest} have been updated on GitHub. Open the app to install.",
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
