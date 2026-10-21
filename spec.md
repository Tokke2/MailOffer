# ═══════════════════════════════════════════════════════════════════════════════
# PROJEKT: Cross-platform Email & Template Manager
# VERSION: 6.2 (WORKSPACE-AKTUELL)
# SPEC-VERSION: MASTER SPEC FULL – KOMPLETT RENSRIVNING (INGET BORTTAGET)
# STATUS: PRODUKTIONSARKITEKTUR (PyQt6 / FÄRGGLAD 4-STEGS WIZARD / INGEN CC)
# V5.0: LÄSKVITTO + LEVERANSBARHETS-GUIDE + ANTISPAM-MALL
# V5.1: STANDARDMALL (default_template) – väljs vid start, manuella val vinner
# V5.1 (IKONRUNDA): app-ikonen används överallt (icons/ + core/app_icon.py)
# V5.1 (WINDOWS-START): dubbelklick utan terminal + autostart via registret (pythonw)
# V5.2: SPRÅKGRUPPERADE MOTTAGARE – SV får svensk version, EN får engelsk
# V5.3: KONTAKTER MED SPRÅK – adressboken styr SV/EN per kontakt
# V5.4: ENGELSKA SKICKAS ALLTID TILL EN-MOTTAGARE – "Inkludera engelsk"-knappen borttagen
# V5.5: SMARTARE KONTAKTSLISTA – naturlig sortering, kolumnklick, språkfilter
# V5.6: GRUPPER I ADRESSBOKEN – lägg till hela grupper i To/Bcc + gruppsortering
# V5.7: MUSHJULSSKYDD – mushjulet skrollar sidan, ändrar aldrig fältvärden
# V5.7: 100%-TESTREGEL – all kod testas till 100% innan leverans (§33.10)
# V5.8: GLASTYP FÖRINSTÄLLD PÅ VINDRUTA EFTER RENSNING (formulärrensning)
# V5.8: OMGÅNG 5 – 25 nya förslag sparade (presenteras efter 10 koduppdateringar)
# V5.9: REGEL – skriv aldrig om hela koden, uppdatera befintlig (minimala riktade ändringar)
# V5.9: REGEL – 50000% bättre på BÅDE kod och design
# V5.9: OMGÅNG 6 – 15 forskningsbaserade förslag (liknande appar)
# V6.0: AUTOSTART v2 – stale_console-reparation, verify-after-write, --background, bättre dubbelklick
# V6.3 (APP 5.4.0): MALL-WIZARD (ui/template_wizard) – skapa TXT/HTML/DOCX steg för steg, SV + [en]
# V6.3: APPEN PÅ SV/EN (core/i18n tr()) – skal/menyer/flikar/wizard/update/donation; resten migreras stegvis
# V6.3: AUTOUPDATE GITHUB RELEASES (core/github_update) – auto 1/dygn + manuell knapp; endast Releases (aldrig main)
#       Mallar/ + JSON + settings skyddade användardata (update_protect); version i core/version.py; omstart via EMAILAPP_RELAUNCH
# V6.3: DONATION KO-FI (core/donate + ui/donate) – ❤️-knapp/dialog, redigerbar länk i Inställningar
# V6.3: KÄNDA LUCKOR samlade i docs/VAD-SAKNAS.md (första release, Ko-fi-länk, LICENSE, klartextlösenord …)
# V6.4 (5.4-uppföljning): DONATIONSSIDA I APPEN – Ko-fi + PayPal (inbyggda standardlänkar, bytbara i Inställningar) + Swish-QR (legacy C-format); qrcode OPTIONAL
# V6.4: START UTAN KONSOL – Starta EmailApp.vbs (hittar pythonw, kör annars Installera_Python.bat /silent dolt = senaste Python 3.12) + Python-vakt i main.pyw (MIN 3.10)
# V6.4: UPDATE TRAY – tray-notis direkt, installationsfrågan när fönstret öppnas; NY IKON överallt med transparens (tools/make_icon.py); HTML-mall escape-fix
# V6.5: E-POSTLISTOR (core/email_lists) – importera TXT/CSV/TSV eller klistra in (även Excel-rader) i Kontakter och direkt i To/Bcc; listnamn = kategori, dubbletter/ogiltiga rapporteras; exportera en eller alla kategorier till semikolonseparerad .txt
# V7.1 (APP 1.1.0): ENKLARE SMTP (core/smtp_presets: leverantörsförval Gmail/Outlook/M365/Yahoo/iCloud + applösenordslänk; core/dns_checks: SPF/DKIM/DMARC-koll via DNS-over-HTTPS) + KOMPLETT SÄKERHETSKOPIA (core/user_backup.create/inspect/restore_full_backup: ZIP med kontakter/mallar/historik/inställningar, lösenord ALLTID borttagna, auto-säkerhetskopia före återställning, zip-slip-skydd)
# V7.0 (APP 1.0.0): PUBLIK RELEASE 1.0.0 – versionsnumreringen nystartad för GitHub (5.x var interna utvecklingsnummer); samma kod som 5.5.1. OBS: autouppdateraren jämför numeriskt så 5.5.1-installationer måste hämta 1.0.0 manuellt EN gång
# V6.7 (APP 5.5.1): MINIMERA TILL TRAY – changeEvent fångar minimering och döljer till trayen när minimize_to_tray=true (kryssruta i Inställningar bredvid Stäng till tray) och en synlig tray-ikon finns; show() avminimerar (showNormal) så tray-klick återställer minimerat fönster
# V6.6 (APP 5.5.0): AVSÄNDARPROFILER (core/sender_profiles) – flera SMTP/avsändarkonton (server/port/avsändare/inlogg/svar-till/egen/arkiv/SSL), hanteras i Inställningar och väljs per sändning i steg 4; plana SMTP-inställningar = spegel av aktiv profil. TESTLÄGE+FÖRHANDSKONTROLL (core/send_preflight): slutantal/överlapp/ogiltiga/SV-EN/bilagestorlek + blockerare/varningar före sändning; testmail går ENDAST till testadress (ingen egen kopia, standard-Bcc, arkiv eller kvitton)
# V6.2: VIN ENDAST I [en] – fält syns/skickas bara till EN-mottagare
# V6.1: KOMMANDE VALDA (2026-09-16) – To/Bcc-dubblett, historik öppna, bild-thumbnails,
#       bättre autostart, saknade tillägg vid dubbelklick → fråga om installera
# ARKITEKTURTYP: ENTERPRISE / MODULÄR / CROSS-PLATFORM / PyQt6
# ═══════════════════════════════════════════════════════════════════════════════

---

# ⚠️⚠️⚠️ OBLIGATORISK REGEL – 100 % TESTNING AV ALL KOD ⚠️⚠️⚠️
#
# ALL kod som skrivs i detta projekt MÅSTE testas till 100 % INNAN den
# levereras till användaren. INGA UNDANTAG.
#
# Krav per leverans:
#   1. py_compile – varje ändrad fil kompilerar utan fel/varningar
#   2. Enhetstester – varje ny funktion/ändring testas (alla grenar som
#      går att nå) med grönt resultat
#   3. Regression – berörda moduler + hela appen (22 moduler) importerar
#      och fungerar tillsammans (stubbad PyQt6)
#   4. End-to-end – sändflödet (SendWorker → send_email → SMTP) verifieras
#      där det är tillämpligt
#   5. Redovisning – testresultatet redovisas ALLTID i svaret till
#      användaren ("Allt grönt ✅")
#
# En ändring räknas INTE som klar förrän dess testpaket är grönt.
# Regeln gäller: bugfixar, nya funktioner, refaktorering, versionsbumpar
# och spec-uppdateringar. (Se även §33.10 och §36.2.)
#
# ═══════════════════════════════════════════════════════════════════════════════

---

## 0. PRODUKTVISION / SYSTEMMÅL

Programmet är ett komplett professionellt desktop-system byggt på **PyQt6**.

**Ny huvudprincip (gäller):**
> **Mall → Bilagor/Bilder → Mottagare → Skicka mail**

Programmet ska vara enkelt, färgglatt och guidat – användaren ska inte behöva förstå tekniska delar. All befintlig funktionalitet ska behållas, förbättras, moderniseras, optimeras och modulariseras. **INGEN funktion får tas bort.**

### Funktioner (komplett lista)

- [X] Hantering av kontakter, mottagarlistor, grupper, To/Bcc-listor
- [X] Hantering av mallar (DOCX, HTML, TXT, Placeholder-system, Preview)
- [X] SMTP-email med Batch-sändning, Retry-system, Progress-system
- [X] Systray-drift, Autostart, Cross-platform drift
- [X] Plugin-kompatibilitet
- [X] Dynamiska teman: ENDAST dark / light / system
- [X] Responsivt GUI, Dynamisk layout
- [X] Single-instance-lock (inbyggt, alltid aktivt)
- [X] Recovery-system (3-strike disable), Modulär arkitektur
- [X] Event-driven kommunikation (EventBus)
- [X] Smart Runtime Mode (dev/prod), Global Cache Policy
- [X] Schema-versionerad settings (migration)
- [X] Bilagor (bifoga filer till mail, max 25 MB/fil, 50 MB totalt)
- [X] Fritext (fri text appendas till mailbody, ovan signatur)
- [X] Auto-översättning till engelska (deep_translator → googletrans → fallback)
- [X] Adressbok-dialog (välj kontakter från contacts.json)
- [X] Dropdown-meny för mottagarfiler (alla JSON/TXT i adresslistor/)
- [X] Dynamiska placeholder-fält per mall (dropdown för kända, textfält för övriga)
- [X] Dropdown för ::ruta:: (13 glastyper för bilindustrin)
- [X] Stöd för .docx, .html, .htm, .txt mallar
- [X] Visa/dölj tabbar individuellt via Visa-menyn och högerklick
- [X] Dynamisk canvas-höjd för placeholder-fält (min 60 px, max 220 px)
- [X] ContactsTab on_add_to callback (lägg till kontakter i To/Bcc)
- [X] CacheManager (dev/prod cache cleanup)
- [X] contacts.json {"contacts":[...]} format (unified)
- [X] grouped_by_category() i ContactStore
- [X] AddressBookDialog med lägg till/redigera/ta bort kontakter
- [X] AddContactDialog med kategori-checkboxar
- [X] _StoreAdapter för kompatibilitet mellan ContactStore-versioner
- [X] LIVE PREVIEW: mallinnehåll uppdateras i realtid när placeholder-värden fylls i
- [X] FORMULÄRRENSNING: efter skickat mail rensas alla fält (placeholders, fritext, bilagor, mottagare) – rensning sker INNAN "✅ Klart"-dialogen
- [X] STANDARDMOTTAGARE: fasta e-postadresser (Standard-To + Standard-Bcc) som alltid fylls i
- [X] ARKIVKOPIA: fast e-postadress som alltid får kopia (dold Bcc)
- [X] SENASTE MOTTAGARE: senaste använda mottagare sparas och kan återanvändas (max 50, FIFO)
- [X] PLACEHOLDER-ÖVERSÄTTNING: när engelsk version inkluderas översätts även placeholder-ETIKETTER (UI-labels) till engelska
- [X] SPRÅKREGEL: svenska delen står på svenska inkl. platshållarvärden (Vindruta = Vindruta); engelska delen översätter allt inkl. platshållarvärden (Vindruta = Windshield)
- [X] MODERNT UI: färgglatt, senaste Python-kompatibelt, dynamiskt anpassat för alla fönster/skärmar, DPI-aware
- [X] HÖGERKLIKKONTEXTMENY PÅ TABB: dölj vald tab via högerklick
- [X] VISA-MENY I MENYRAD: menyval för att visa/dölja varje tab individuellt
- [X] DRAG & DROP för bilagor (steg ②) – tydlig drop-yta, markeras vid drag, dubbletter ignoreras
- [X] ADRESSBOKEN STÄNGS INTE vid "Lägg till" – statusfeedback, "Klar"-knapp, fortsätt lägga till
- [X] ADRESSBOKEN: lägg till/redigera/ta bort kontakter direkt i adressboken
- [X] ADRESSBOKEN: sortera (Namn/E-post/Företag/Kategori, A-Ö/Ö-A) och gruppera per kategori
- [X] ADRESSBOKEN: avatarer, tom-state, kontextmeny (Lägg till To/Bcc, Redigera, Ta bort, Kopiera e-post)
- [X] KONTAKTER-FLIKEN: adressboken laddas in när fliken öppnas (med mtime-cache – endast om filen ändrats)
- [X] INSTÄLLNINGAR-FLIKEN: visar en sammanställning av alla inställningar, redigerbar + spara
- [X] HISTORIK: högerklick visar mottagare; dubbelklick/högerklick → "Öppna för redigering / Skicka om"
- [X] HÖGERKLICK I HISTORIKEN: visa vilka man skickade till (To + Bcc + totalt)
- [X] QSystemTrayIcon (inbyggt – ingen pystray/Pillow)
- [X] Tray-first startup, enkelklick på trayikon öppnar fönster
- [X] Ingen profiles-skapande (ej efterfrågat, app-till-app)

### Programmet ska
- [X] Fungera identiskt på Windows / Linux / macOS
- [X] Fungera utan terminal (även om filen heter .py)
- [X] Alltid kunna köras stabilt och aldrig krascha totalt
- [X] Kunna utökas, stödja plugins/moduler, vara production-ready och framtidssäkert
- [X] Alltid starta minimerat i systray, öppnas via enkelklick på trayikonen

---

## 1. ARKITEKTUR / RAMVERK (PyQt6 MIGRATION KOMPLETT)

- [X] **PyQt6 som UI-ramverk** (ersätter Tkinter helt – ingen Tkinter-kod kvar)
- [X] `ui/styles.py` ersätter `ui/theme_engine.py` (Tkinter) – QSS + StyleEngine
- [X] QSystemTrayIcon ersätter pystray; QPainter/QIcon ersätter Pillow
- [X] QThread + pyqtSignal för trådsäkerhet (ersätter threading + root.after)
- [X] QDialog.exec() / setModal (ersätter grab_set/wait_window)
- [X] QTimer.singleShot (ersätter root.after)
- [X] QMessageBox / QFileDialog / QInputDialog (ersätter messagebox/filedialog/simpledialog)
- [X] Scroll hanteras av Qt automatiskt (ingen bind_mousewheel)
- [X] DPI hanteras av Qt6 själv (ingen ctypes-DPI-hack – undviker "SetProcessDpiAwarenessContext() failed: Åtkomst nekad")
- [X] Qt-runtime-env sätts före QApplication: `QT_ENABLE_HIGHDPI_SCALING=1`, `QT_AUTO_SCREEN_SCALE_FACTOR=1`
- [X] PyQt6-fix: `QAction.setDefault()` finns ej → `QMenu.setDefaultAction()` (förhindrar startup-krasch)

### Migrationshistorik (för referens)
| # | Fil | Från → Till |
|---|-----|-------------|
| 1 | main.pyw | Tkinter v3.5 → PyQt6 v4.0 → v4.6 |
| 2 | ui/styles.py | NY v1.0 (ersätter theme_engine) → v1.3 |
| 3 | ui/main_window.py | v3.6 → v4.0 PyQt6 → v4.9 |
| 4 | ui/tray.py | v3.2 pystray → v4.0 QSystemTrayIcon → v4.4 |
| 5 | ui/dialogs.py | v3.4 → v4.0 PyQt6 → v4.6 |
| 6 | ui/editors.py | v3.3 → v4.0 PyQt6 → v4.2 |
| 7 | ui/preview.py | v3.4 → v4.0 PyQt6 → v4.3 |
| 8 | script/recipients.py | v3.8 → v4.0 PyQt6 → v5.4 |
| 9 | script/contacts_ui.py | v3.4 → v4.0 PyQt6 → v4.3 |
| 10 | script/templates.py | v3.3 → v3.4 (Any-fix) → v3.6 |
| 11 | core/single_instance.py | v3.2 → v3.3 (ctypes-mutex, socket-fokus) |
| 12 | core/settings_manager.py | v20/v21 → v24.3 |
| 13 | core/recovery_manager.py | v3.2/v3.3 → v3.5 |
| 14 | core/logger.py | v3.2/v3.3 → v3.5 |
| 15 | core/event_bus.py | v3.2/v3.3 → v3.5.1 |
| 16 | core/cache_manager.py | v1.0/v1.1 → v1.2 |
| 17 | core/email_sender.py | v3.2/v3.3 → v3.7.1 |
| – | ui/theme_engine.py | BORTTAGEN (ersatt av ui/styles.py) |

---

## 2. MAPPSTRUKTUR (KOMPLETT – WORKSPACE)

```
Email/
├── main.pyw                          ← Bootstrapper v5.0 (pythonw + --background)
├── Starta EmailApp.vbs               ← Dubbelklick-lanserare v5.2 (ingen terminal)
├── spec.md                           ← DENNA SPEC
├── requirements.txt                  ← (att skapa – pinnade == versioner)
├── icons/
│   ├── app_icon.png                  ← 512x512 RGBA (rundade hörn) – app-ikonen
│   └── app_icon.ico                  ← Windows-ikon (16–256 px)
├── core/
│   ├── __init__.py
│   ├── settings_manager.py           ← v24.6 (pythonw + robust skriptväg)
│   ├── email_sender.py               ← v3.9 (språkgrupper SV/EN)
│   ├── event_bus.py                  ← v3.5.1
│   ├── logger.py                     ← v3.5
│   ├── single_instance.py            ← v3.3
│   ├── recovery_manager.py           ← v3.5
│   ├── cache_manager.py              ← v1.2
│   └── app_icon.py                   ← v1.0 (central ikonladdning + fallback)
├── script/
│   ├── __init__.py
│   ├── templates.py                  ← v3.6
│   ├── contacts_ui.py                ← v4.6 (smart sortering + lägg alla visade)
│   └── recipients.py                 ← v5.5 (grupper i adressboken)
├── ui/
│   ├── __init__.py
│   ├── main_window.py                ← v5.5 (engelska automatiskt, ingen knapp)
│   ├── dialogs.py                    ← v4.9 (språkfördelning i bekräftelsen)
│   ├── editors.py                    ← v4.2
│   ├── preview.py                    ← v4.3
│   ├── styles.py                     ← v1.3
│   ├── tray.py                       ← v4.5 (app-ikon + status-badge)
│   └── wheel_guard.py                ← v1.0 (mushjul skrollar sidan, ändrar ej fält)
├── plugins/                          ← EJ IMPLEMENTERAT (FAS 3)
│   ├── __init__.py
│   └── example_plugin/
│       ├── __init__.py
│       └── plugin.py
├── adresslistor/
│   ├── contacts.json                 ← {"contacts":[...]} (UNIFIED)
│   ├── email_content.json
│   ├── Epostlista.txt
│   ├── Frakt.txt
│   ├── Fraktoffert.json
│   ├── Förfrågning.json
│   └── Vindruta.json
├── logs/
│   └── email_app.log                 ← Roterande, 5 MB x 5 backup
├── Mallar/
│   ├── Vindruta.docx                 ← ::ruta::, ::modell::, ::reg::, ::kommentar::
│   ├── Fraktoffert.docx
│   ├── Torkarblad.docx
│   ├── Förfrågning.docx
│   ├── email_content.docx
│   ├── Offertförfrågan – anti-spam.txt   ← v5.0 (ny)
│   ├── Offertförfrågan – original.txt    ← v5.0 (sparad klistring)
│   └── (~$*-filer ignoreras alltid)
└── .data/
    ├── settings.json                 ← ALL config, atomic write, schema v24
    └── sent_history.json             ← Sändhistorik (max 500 poster)
```

**Viktiga strukturregler:**
- `ui/theme_engine.py` används inte längre (ersatt av `ui/styles.py`)
- pystray/Pillow används inte (QSystemTrayIcon + QPainter)
- Word-tempfiler `~$*` ignoreras alltid vid mallskanning (även i projektroten)
- Mallskanning hoppar över: `~$*`, `*.bak`, `*.tmp`
- Aktiva mallar: `.docx`, `.html`, `.htm`, `.txt` som inte börjar med `~$`
- Importer använder faktiska modulnamn (`core.email_sender`, `ui.main_window`, `script.contacts_ui`)
- Markdown-länkade filnamn (`main_[window.py](...)`) får ALDRIG hamna i Python-kod
- Alla Python-filer UTF-8 utan BOM

---

## 3. KRITISKA GLOBALA REGLER

### FÖRBJUDET
- Hårdkodade paths
- Hårdkodade färger (ALL styling via `ui/styles.py` – QSS)
- Blockerande UI-anrop (QThread + pyqtSignal)
- Multipla instanser (single_instance alltid aktiv)
- Silent exceptions (logging.exception() alltid)
- Tight coupling (EventBus för all kommunikation)
- Settings utanför JSON (atomic write)
- Mail utan bekräftelse (SendConfirmDialog OBLIGATORISK)
- Terminalfönster (pythonw.exe / subprocess utan PIPE)
- Copyrighttext i kod
- Hårdkodade hex-färger i UI-koden (använd `StyleEngine.get_colors()`)
- `>=` eller `~=` i dependencies (använd `==`)
- Profiles-skapande (ej efterfrågat, app-till-app)
- AI byter språk utan användarens godkännande
- Tkinter-kod / `root.after()` / `bind_all()` / `grab_set()` / `wait_window()` / `messagebox.*` / `filedialog.*` / `simpledialog.*` / `ttk.*` / `tk.*`
- pystray / Pillow
- `QAction.setDefault()` (finns ej i PyQt6 → `QMenu.setDefaultAction()`)
- `import re` (eller liknande) längst ner i fil – ska vara överst
- `settings.save()` anropas dubbelt (main.pyw finally + on_shutdown)
- Placeholder-värden sparas vid formulärrensning (rensas – `replacements_values` töms)

### KRAV
- Alla exceptions loggas med stacktrace
- Alla moduler kan disable:as (RecoveryManager)
- UI får aldrig frysa (async alltid)
- Alla plugins laddas dynamiskt
- Alla moduler kommunicerar via EventBus
- Alla settings valideras och auto-repareras
- All UI läsbar i alla teman (WCAG AA)
- Tabbar visa/dölja via Visa-menyn OCH högerklick
- Fönstrets geometri sparas i settings.json (window_geometry, "WxH+X+Y")
- Startup alltid minimerat i tray
- Enkelklick på trayikonen öppnar fönster
- [X]-knapp minimerar till tray (close_to_tray=true default)
- "Avsluta" i traymeny = full shutdown
- `main_window.set_tray(tray)` kallas från main.pyw
- `on_close()` delegerar till `tray._do_quit()` vid full shutdown
- `on_shutdown()` sparar ENBART till minnet (inte till disk)
- import-ordning: stdlib → third-party → local, alltid överst
- Formulärrensning sker ENBART efter lyckad sändning (`result.success`)
- Standardmottagare läses in vid tab-init och fylls i automatiskt
- Senaste mottagare sparas automatiskt efter varje sändning
- Placeholder-labels översätts dynamiskt utan omstart
- Visa-meny syncas med aktuell tab-visibility-status
- Bundna metoder vid EventBus-subscribe (ALDRIG lambdas – GC:as av weakrefs)
- `result.success` (INTE `result.ok`)

---

## 4. TEMA-SYSTEM

### 4.1 ENDAST DESSA TEMAN ÄR TILLÅTNA
- [X] dark
- [X] light
- [X] system (synkar med OS via darkdetect)

`CANONICAL_THEMES = {"light", "dark", "system"}`
`VALID_THEMES = {"light", "dark", "system", "auto"}` (auto = legacy → mappas till system vid migration)
ANDRA TEMAN ÄR STRÄNGT FÖRBJUDNA.

### 4.2 ALLA färger styrs ENBART av `ui/styles.py` (v1.3)
`StyleEngine.get_colors()` returnerar dict med ALLA nycklar:
- Bakgrund: background, surface, surface_alt, bg_secondary, panel_bg, card_bg, card_hover, input_bg
- Alias: bg (=background), fg (=text)
- Text: text, text_secondary, fg_secondary, muted, disabled_fg, disabled_bg, inverse_text, dark_text
- Knappar: button_bg, button_fg, button_hover, button_active
- Tabbar: tab_bg, tab_fg, tab_active_bg, tab_active_fg
- Accent: accent, accent_hover, accent_active, accent_soft, link
- Status: success(+hover/soft), warning(+hover/soft), error(+hover/soft)
- Extra färger: purple(+hover/soft), pink(+hover/soft), cyan(+hover/soft), orange(+hover/soft)
- Indata: entry_bg, entry_fg
- Övrigt: border, border_soft, scrollbar_bg, scrollbar_fg
- Meny: menu_bg, menu_fg, menu_active_bg, menu_active_fg
- Tooltip: tooltip_bg, tooltip_fg

### 4.3 LIGHT THEME – krav
- Mörkgrå knappar (#555555) med vit text (#FFFFFF)
- Vit/ljusgrå bakgrund (#F5F5F5), mörk text (#111111 / bold)
- Hög kontrast (WCAG AA), tydliga borders (#BBBBBB)
- Hover: mörkare grå (#444444), Active: accent (#1565C0), Focus: accent ring
- Disabled: ljusgrå (#CCCCCC) med mörkgrå text (#888888)
- Alias: bg=#F5F5F5, fg=#111111, fg_secondary=#444444, Link: #1565C0
- Menu: bg=#FFFFFF, fg=#111111, active_bg=#E3F2FD, active_fg=#1565C0

### 4.4 DARK THEME – krav
- Medelgrå/blågrå knappar (#5A5A7A) med vit text (#FFFFFF)
- Mörk bakgrund (#1E1E2E), vit text (#FFFFFF / bold)
- Hög kontrast (WCAG AA), tydliga borders (#4A4A6A)
- Hover: ljusare grå (#6A6A8A), Active: accent (#5C9EFF), Focus: accent ring
- Disabled: mörkgrå (#2E2E40) med grå text (#666677)
- Alias: bg=#1E1E2E, fg=#FFFFFF, fg_secondary=#BBBBCC, Link: #5C9EFF
- Menu: bg=#2A2A3E, fg=#FFFFFF, active_bg=#3A3A5A, active_fg=#5C9EFF

### 4.5 KNAPPAR & TABBAR – krav
- Alltid tydliga (WCAG AA), lättlästa (min 10pt bold, Segoe UI/SF Pro/Helvetica)
- Fet text (bold), hover-effekter, disabled-state, focus-state
- Accent-knapp: Skicka/Spara · Danger-knapp: Ta bort/Rensa
- Tabbar har rundade hörn, aktiv tab har accent-färg + fet text
- Inaktiv tab har lägre kontrast

### 4.6 QSS-klasser (styles.py v1.3)
card, cardHover, softPanel, hero, successPanel, warningPanel, errorPanel,
wizardHeader, wizardStep(+Active/Done), stepNumber/stepTitle/stepHint,
step-blue/purple/green/orange/red, onColor, pill/pillGreen/pillOrange/pillPurple,
heading/title/subtitle/subtext/muted/success/warning/error/accent/purple,
accent/primary/next/back/danger/success/send/warning/purple (knappar),
separator, appRoot.

### 4.7 StyleEngine (v1.3)
- `build_qss(c)` → komplett QSS
- `get_cached_qss(mode)` → **cachad QSS** (byggs en gång per läge – 1000 anrop ≈ 0,14 ms)
- `StyleEngine(settings, event_bus)`: get_theme, get_colors, get_color, apply, set_theme, toggle, is_os_dark, current_mode, _resolve_mode
- Publicerar `ui.theme_changed` {theme, was} vid byte

---

## 5. GUI / UI SYSTEM

### 5.1 Allmänt
- Modernt (PyQt6-widgets), professionellt, färgglatt (accent-färger)
- Responsivt (auto-resize, dynamisk layout – grid/pack weight)
- Framtidssäkert (plugin-tabs, EventBus-driven)
- Modulärt (varje tab är en separat Frame/QWidget-klass)
- Dynamiskt (inga fasta pixelstorlekar – grid/pack weight)
- Lättläst (min 10pt font, word-wrap, scrollbars)
- DPI-aware (Qt6 inbyggt), multi-monitor, touchpad/mus

### 5.2 Fönsterkrav
- Dynamisk resize (minsize 1080x760 satt, maxsize obegränsad)
- Auto-layout (columnconfigure/rowconfigure med weight)
- Scrollbars där det behövs (Treeview, Text, Canvas, Listbox, Preview, plugin-tabs, settings-paneler)
- Word-wrap (wrap=WORD)
- Minimum readable font 10pt
- Fönstergeometri sparas i settings.json vid close ("WxH+X+Y")
- Dialoger centreras över huvudfönster (transient/exec), skalar med innehåll

### 5.3 Scroll (cross-platform)
- Windows: `<MouseWheel>` event.delta/120 · Linux: `<Button-4>`/`<Button-5>` · macOS: `<MouseWheel>` faktor 1
- **PyQt6: Qt hanterar mushjul automatiskt – ingen bind_mousewheel behövs**
- ALDRIG `bind_all()` – per-widget-bindning (Tkinter-kvarleva förbjuden)

### 5.4 Tab-system (7 tabbar)
STANDARD-TABBAR:
- [X] 📤 Skicka (4-stegs wizard) – `_build_send_wizard_tab`
- [X] 👥 Kontakter – `script/contacts_ui.py` → ContactsTab
- [X] 📝 Mallar – `_build_template_tools_tab`
- [X] 👁️ Preview – `ui/preview.py` → PreviewTab
- [X] 📨 Historik – `_build_history_tab`
- [X] 📜 Loggar – `_build_log_tab`
- [X] ⚙️ Inställningar – `_build_settings_tab`

KRAV:
- Visa/dölj via "Visa"-menyn (checkboxar per tab) + högerklick på tab ("🙈 Dölj denna tab")
- "↩️ Visa alla" återställer alla tabbar
- Minst en tab synlig (validering)
- `ui.tab_visibility_changed` {tab_key, visible} publiceras
- Visa-meny syncas direkt (`_sync_view_menu` med blockSignals)

---

## 6. 4-STEGS WIZARD (HUVUDFLÖDET)

### Steg 1 – ① 📝 Mall (`step-blue`)
- Mall-dropdown (Combobox – alla filtyper)
- Knappar: 🔄 Sök (uppdatera mallar) + 📂 Öppna mapp
- Mall-badge (⏳/✅/⚠️)
- Ämnesrad (QLineEdit) – textChanged → refresh preview
- Mallinnehåll/editor (QTextEdit) – textChanged → debounce 220 ms → rebuild placeholders
- Dynamiska placeholder-fält (dropdown för kända – t.ex. ::ruta:: med 13 glastyper; textfält för övriga)
- Statusrad: "🔑 Fyll i mallens uppgifter här: ..." + "✅ Alla N uppgifter ifyllda – redo!"
- Engelsk checkbox: "Inkludera engelsk version" (+ status "✅ Engelska aktiverat")
- 💾 Spara mall-knapp
- Live preview uppdateras när något ändras

### Steg 2 – ② 🖼️ Bilagor/Bilder (`step-orange`)
- Eget tydligt steg med rubrik "② 🖼️ Bilagor/Bilder"
- **Drag & drop-yta** (AttachmentDropListWidget): "Dra filer hit eller klicka på 'Lägg till bilder/filer'"
  - Drop-yta markeras visuellt vid drag (accent-färgad ram)
  - Flera filer samtidigt, dubbletter ignoreras
  - Samma validering som vanlig filuppladdning
  - Både drag & drop OCH vanlig filväljare finns
- Knappar: ➕ Lägg till bilder/filer · 🗑️ Ta bort · 🧹 Rensa
- Bildfiler markeras med 🖼️, övriga med 📎
- Räknare: "3 bilagor · 2 bilder · 1 fil"
- Filfilter: Alla filer (*) · Bilder (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tif *.tiff) · PDF (*.pdf) · Dokument (*.docx *.xlsx *.txt)
- 💬 Fritext (QPlainTextEdit) – "Fritext skickas med ovan signaturen i mailet"
- Bilagor skickas vidare i `attachments`; maxstorlek valideras i email_sender (25 MB/fil, 50 MB totalt)

### Steg 3 – ③ 📬 Mottagare (`step-green`)
- To-lista + Bcc-lista (INGEN CC)
- Lägg till e-postfält + ➕ Lägg till (Enter fungerar)
- 🗑️ Ta bort markerade · 🧹 Rensa
- 📒 Öppna adressbok-knapp (accent)
- Standard-To + Standard-Bcc + Arkivkopia fylls i automatiskt (vid start + efter rensning)
- E-post valideras innan tillägg/sändning; dubbletter ignoreras
- Minst en mottagare krävs för sändning
- Tips-rad: "Standard-Bcc fylls i automatiskt från inställningar. CC används inte."

### Steg 4 – ④ 🚀 Skicka mail (`step-red`)
- Förhandsgranskning (👁️ Visa preview-tab)
- Sammanfattning: To-antal · Bcc-antal · totalt · ämne · mallnamn · antal bilagor · antal bilder
- Knapp: 📤 Skicka mail
- **OBLIGATORISK SendConfirmDialog** – mail får aldrig skickas direkt
  - Användaren måste explicit klicka "✅ Skicka nu"
  - Avbryt/stäng dialog = inget skickas
- `result.success` används efter sändning
- Formulär rensas endast efter lyckad sändning (INNAN "✅ Klart"-dialogen)

---

## 7. SYSTEM TRAY (`ui/tray.py` v4.5)

### Krav
- Starta minimerat (root.withdraw() vid init – PyQt6: main_window.hide())
- Starta i tray (QSystemTrayIcon – inbyggt)
- Aktiv trayikon (QIcon ritad via QPainter – kuvert + status-badge)
- Öppnas via enkelklick (+ dubbelklick)
- `main_window.set_tray(tray)` kallas från main.pyw

### 7.1 TRAY-BETEENDE
[X]-KNAPP (close_to_tray=true): → minimera till tray (hide) – trayikonen förblir aktiv
"Avsluta" i tray-meny: → full shutdown (`app.shutdown` → `tray.shutdown()` → `app.quit()`)

TRAY-MENY:
- 👁️ Visa fönster (default-action via `QMenu.setDefaultAction()` – PyQt6-fix)
- 🙈 Dölj fönster
- ─── separator ───
- ⚙️ Inställningar (öppnar Inställningar-tab)
- 🔌 Testa SMTP (bakgrundstråd, visar notis)
- ─── separator ───
- ❌ Avsluta helt

NOTISER (showMessage, 3500 ms):
- "✅ E-post skickad" – Skickad till N mottagare. Ämne: ...
- "❌ Sändning misslyckades" – Ämne: ... – feltext
- "⚠️ Modul inaktiverad" – 'modul' inaktiverades: anledning
- "Email Manager är igång och redo." (startup)
- "🧹 Formulär rensat" – Formuläret rensades efter lyckad sändning
- "📌 Standardmottagare" – N standard-Bcc tillagda

IKONLÄGEN (ICON_COLORS):
- idle: #2563EB (blå) · sending: #F59E0B (orange) · error: #DC2626 (röd) · success: #16A34A (grön, 3 s → idle)
- **Ikoner cachas per läge** (v4.4 – ritas en gång)

TRÅDSÄKERHET:
- `_TraySignals(QObject)` med pyqtSignal per event
- EventBus-callbacks emit():ar signals; Qt levererar till main thread
- **Handlers sparas i `self._handlers`** (v4.4) – unsubscribe fungerar (kräver EventBus v3.5.1-fix)
- ALDRIG root.after direkt från callbacks

---

## 8. EMAIL-SYSTEM (`core/email_sender.py` v3.9)

### Funktioner
- [X] SMTP (SSL/STARTTLS auto-detect, port 465 = SSL, annars STARTTLS)
- [X] Batch sending (To-batch + Bcc-batchar; CC finns ej i v4.3+)
- [X] Retry-system (exponentiell backoff, auto-reconnect)
- [X] Async sending (QThread i MainWindow – aldrig UI-block)
- [X] Progress callback (root.after → pyqtSignal)
- [X] MIME support (text/plain + text/html multipart/alternative)
- [X] HTML auto-generering från plain-text (`text_to_html`)
- [X] DOCX, HTML, TXT mall-stöd (via `script/templates.py`)
- [X] Preview-system (via `ui/preview.py`)
- [X] Placeholders ({NAME}, {EMAIL}, ((key)), ::key::)
- [X] Attachments (MIME, max 25 MB/fil, 50 MB totalt)
- [X] Statistik (SendResult dataclass)
- [X] Validation (email-validator + regex fallback)
- [X] free_text parameter (appendas till brödtext, eget HTML-block, ovan signatur)
- [X] had_free_text / had_translation i SendResult
- [X] dry_run-läge för testning utan sändning
- [X] STANDARDMOTTAGARE: default_bcc-listor som alltid bifogas
- [X] ARKIVKOPIA: archive_copy_email som alltid bifogas (dold Bcc)
- [X] SENASTE MOTTAGARE: sparas i settings (recent_recipients)
- [X] FORMULÄRRENSNING: efter lyckad sändning anropas "ui.form_reset"
- [X] Egen e-post alltid med som TO (own_email)
- [X] Reply-To (default = sender_email)
- [X] Placeholder AI-översättning vid include_english (fast mappning GLASS_TYPE_MAP + deep_translator)
- [X] LEVERANS-/LÄSKVITTO (v3.8): request_receipts – headers Disposition-Notification-To + Return-Receipt-To samt SMTP-DSN (NOTIFY=SUCCESS,FAILURE) när servern annonserar DSN (esmtp_features). Fail-safe: DSN-nekad RCPT → nytt försök utan DSN (mail skickas alltid). SendResult.receipts_requested.
- [X] SPRÅKGRUPPER (v3.9): recipients_to_lang/recipients_bcc_lang – Dict {e-post: "sv"/"en"}.
  SV-mottagare får ENBART svensk version, EN-mottagare ENBART engelsk – ÄVEN när
  include_english=True. include_english=False → alla svensk. Mallen parsas per språk
  (endast språk som används); placeholder-översättning bara för EN-gruppen;
  batchar to_sv/to_en/bcc_sv/bcc_en med tydliga etiketter; SendResult får
  recipients_sv, recipients_en, had_language_split + "🌐 Språk"-rad i summary().

### Bildkomprimering (v3.6/v3.7/v3.7.1)
- `compress_images` + `preserve_image_dimensions` + `preserve_image_sharpness` + `image_jpeg_quality` + `image_png_compress_level`
- **v3.7.1: Gör INGET om inga bilder finns** (guard på två nivåer – ingen temp-katalog skapas)
- Max 1920 px längsta sida (om preserve_image_dimensions=False)
- JPEG-kvalitet 92 default, PNG compress level 6, WEBP 80
- QImage (PyQt6) primär, Pillow fallback
- Transparent → vit bakgrund vid JPEG
- GIF rörs aldrig; <100 KB rörs inte; blir inte mindre → original
- Temp-katalog rensas efter sändning + atexit-säkerhet
- `SendResult.images_compressed`

### SendResult FÄLT (v3.9)
`success, subject, total_recipients, batches_sent, batches_total, recipients_to, recipients_bcc, attachments_count, elapsed_seconds, errors, warnings, invalid_emails, dry_run, had_free_text, had_translation, had_bcc, had_placeholder_translation, images_compressed, receipts_requested (v3.8), recipients_sv, recipients_en, had_language_split (v3.9)`

**OBS:** Använd `result.success` (EJ `result.ok`) i MainWindow! `build_send_summary()` är fallback om `summary()` saknas.

### Signatur (komplett)
smtp_server, smtp_port, sender_email, sender_name, username, password,
word_file_path, replacements, include_english, recipients_to, recipients_bcc,
attachments, comment, free_text, body_is_html, generate_html_from_plain,
validate_recipients, skip_invalid_recipients, use_ssl, disable_tls, timeout,
max_retries, retry_backoff_factor, bcc_batch_size, delay_between_batches,
reply_to, extra_headers, smtp_debug, dry_run, log_recipient_details,
own_email, default_bcc, translate_placeholders,
compress_images, preserve_image_dimensions, preserve_image_sharpness,
image_jpeg_quality, image_png_compress_level, request_receipts (v3.8),
recipients_to_lang, recipients_bcc_lang (v3.9), on_progress.

### 8.1 ABSOLUT REGEL – MAILBEKRÄFTELSE
MAIL FÅR ALDRIG SKICKAS DIREKT. OAVSETT hur sändning triggas
(Skicka-knapp i toolbar, "Skicka med denna mall", Ctrl+Enter, tray-meny testmail):
→ SendConfirmDialog VISAS OBLIGATORISKT → användaren måste explicit klicka "✅ Skicka nu"
→ Dialog stängd på annat sätt = mail skickas EJ.

### 8.2 SENDCONFIRMDIALOG (obligatorisk)
Dialogen MÅSTE visa:
- Antal To-mottagare med förhandsgranskning (3 st)
- Antal Bcc-mottagare med förhandsgranskning
- Standard-Bcc-info ("N st alltid inkluderade")
- Totalt antal (färgkodat: rött om 0, grönt om OK) – `self._total` instansvariabel
- Ämne (varning om tomt) · Mallnamn · Språk (sv/en/both)
- Bilagor (antal + namn) · Bilder/Filer-räkning (N bilder · N övriga filer)
- Saknade platshållare (max 6 visas + "…+N till") · Generella varningar
- Inga mottagare → Skicka-knapp inaktiveras
- INGEN CC visas (v4.3+)
- (v4.7) CHECKBOX "📨 Begär leverans- och läskvitto" – standardvärde från
  settings request_receipts (v24.4); hämtas via dialog.result_params()
  av MainWindow vid bekräftelse → skickas till send_email() som
  request_receipts (email_sender v3.8)

KNAPPAR: ❌ Avbryt (vänster) · 👁️ Förhandsgranska (mitten) · ✅ Skicka nu (höger, send-cssClass)
TANGENTER: Enter = Skicka (om mottagare finns) · Escape = Avbryt · F5 = Förhandsgranska

---

## 9. TEMPLATE SYSTEM (`script/templates.py` v3.6)

### Stöd
- DOCX (python-docx – lazy/valfri), HTML (auto-detekt via filändelse), TXT (ÄMNE:/INNEHÅLL:-format)
- Placeholder-system (tre format) · Preview (via ui/preview.py)
- Versionshantering (TemplateVersion dataclass + .bak)
- Import/export (export_template() med backup)
- Validering (validate_template() för alla filtyper)
- Scanning (scan_templates_dir() för .docx/.html/.htm/.txt) – hoppar över ~$-, .bak, .tmp
- **scan-cache** (v3.6: filantal + mtime – skannar endast om något ändrats)
- **apply_placeholders early-return** (v3.6 – ingen placeholder-grammatik → direkt return)
- Språkstöd: [sv]...[/sv], [en]...[/en], [comment]...[/comment] (kommentarer tas bort)
- keep_unknown, remove_lines_with_missing (default FALSE – spec §9.2:
  saknad platshållare → tom sträng, rader tas bara bort vid opt-in),
  strip_comments
- LIVE UPDATE: PreviewTab renderar om vid varje placeholder-ändring (debounce)

### 9.1 PLACEHOLDERS
STÖDDA FORMAT: `{NAME}` (klammer) · `((NAME))` (dubbelparentes) · `::NAME (dubbelkolon)

STANDARDPLACEHOLDERS (emoji-etiketter):
- ::ruta:: → 🪟 Glastyp (DROPDOWN, 13 alternativ)
- ::modell:: → 🚗 Bilmodell · ::reg:: → 🔢 Reg.nummer · ::kommentar:: → 💬 Kommentar
- {NAME} → 👤 Namn · {EMAIL} → 📧 E-post · {COMPANY} → 🏢 Företag
- {DATE} → 📅 Datum · {ORDER_ID} → 📋 Ordernummer · price → 💰 Pris · delivery → 🚚 Leveranstid

PLACEHOLDER-ÖVERSÄTTNING (labels, när include_english=True):
"🪟 Glastyp"→"🪟 Glass type" · "🚗 Bilmodell"→"🚗 Car model" · "🔢 Registreringsnummer"→"🔢 Registration number" · "💬 Kommentar"→"💬 Comment" · "👤 Namn"→"👤 Name" · "📧 E-post"→"📧 Email" · "🏢 Företag"→"🏢 Company" · "📅 Datum"→"📅 Date" · "📋 Ordernummer"→"📋 Order number" · "💰 Pris"→"💰 Price" · "🚚 Leveranstid"→"🚚 Delivery time"
(Maps: `_PH_SV` / `_PH_EN` i main_window)

PLACEHOLDER-VÄRDE-ÖVERSÄTTNING (värden, när include_english=True):
Fast mappning via `_PLACEHOLDER_VALUE_EN` + GLASS_TYPE_MAP:
Vindruta → Windshield · Bakruta → Rear window · Höger sidoruta fram → Front right door glass · etc.
**SPRÅKREGEL:** svenska delen behåller svenska värden (Vindruta = Vindruta); engelska delen översätter allt (Vindruta = Windshield).

GLASTYPER (PLACEHOLDER_DROPDOWNS["ruta"]) – 13 st:
Vindruta · Bakruta · Höger sidoruta fram · Vänster sidoruta fram · Höger sidoruta bak · Vänster sidoruta bak · Höger ventilationsruta · Vänster ventilationsruta · Höger kvarts-/hörn-ruta · Vänster kvarts-/hörn-ruta · Taklucka / Panoramatak · Vindruteglas (laminerad) · Vindruteglas (härdad)

### 9.2 KRAV
- Highlight placeholders i TemplateEditor (blå = känd, röd = saknas)
- Validate placeholders (lista saknade) · Fallback om saknas (tom sträng + varning i logg)
- Preview rendering (ersätt med inmatade värden)
- LIVE UPDATE: PreviewTab renderar om vid varje KeyRelease/FocusOut i placeholder-fält
- Spara värden i settings.json (replacements_values)
- Rensa värden efter skickat mail (om clear_form_after_send=true)

---

## 10. SETTINGS SYSTEM (`core/settings_manager.py` v24.7)

### Schema (v24.6 – komplett)
```json
{
  "settings_version": 24,
  "mode": "prod", "smart_cache": true,
  "startup": false, "autostart": false,
  "start_minimized": true, "close_to_tray": true, "minimize_to_tray": true,
  "theme": "system", "language": "sv",
  "window_geometry": "",
  "visible_tabs": { "tab_contacts": true, "tab_recipients": true, "tab_templates": true,
                    "tab_preview": true, "tab_logs": true, "tab_settings": true,
                    "tab_history": true },
  "smtp_server": "", "smtp_port": 587, "sender_email": "", "sender_name": "",
  "username": "", "password": "", "use_ssl": false,
  "own_email": "", "reply_to": "",
  "archive_copy_email": "",
  "template_dir": "Mallar", "address_dir": "adresslistor", "word_file_path": "",
  "default_template": "",
  "include_english": false, "translate_placeholders": true,
  "replacements_values": {}, "recent_files": [],
  "validate_recipients": false, "skip_invalid_recipients": true,
  "bcc_batch_size": 0, "delay_between_batches": 0.5, "max_retries": 2,
  "smtp_timeout": 30, "generate_html_from_plain": true,
  "request_receipts": false,
  "compress_images": true, "preserve_image_dimensions": true,
  "preserve_image_sharpness": true, "image_jpeg_quality": 92,
  "image_png_compress_level": 6,
  "default_to": [], "default_bcc": [],
  "recent_recipients": [],
  "clear_form_after_send": true, "save_last_recipients": true,
  "plugin_states": {}, "debug_logging": false, "log_level": "INFO"
}
```
- **request_receipts (v24.4):** bool, default false – standardvärde för
  kvittocheckboxen i sänddialogen. Schema-version förblir 24 – ny nyckel
  fylls automatiskt via defaults-merge (ingen migration krävs).
- **default_template (v24.5):** str, default "" – standardmallen som
  väljs automatiskt vid start (filnamn i Mallar/). Tom = senast valda.
  Valideras som str (str_fields). Manuella dropdown-val vinner alltid.
- **Windows-start (v24.6):** `_find_pythonw()` (pythonw bredvid
  sys.executable → sys.base_prefix → PATH) + `_script_path()`
  (argv0 giltig .pyw/.py → annars <projekt>/main.pyw). Autostart via
  registret (HKCU\...\Run) använder ALLTID pythonw.exe → ingen konsol.

### Krav
- Atomic Writes (.tmp → replace, wrote_ok-flagga) – korrupterar aldrig filen
- Backup (.bak) vid varje sparning · chmod 0o600
- Migration stegvis v1→v24 ("auto"→"system", default_cc tas bort, nya nycklar tilläggs)
- Validation + auto-repair (alla nycklar + typkorrigering)
- `default_cc` HELT borttagen (ignoreras, skrivs aldrig tillbaka, tas bort vid migration/spara)
- `default_to`/`default_bcc` valideras som listor av strängar
- `recent_recipients` max 50 (FIFO via MAX_RECENT_RECIPIENTS)
- **Lås-fri läsning** (copy-on-write, v24.1) – get() ~3,4x snabbare
- Metoder: get, set, update_from_dict, get_all(redact_secrets), save, reload,
  sync_autostart, is_autostart_enabled, set_autostart, apply_autostart_preference,
  classify_autostart, get_autostart_info,
  add_recent_recipient, get_recent_recipients, clear_recent_recipients,
  get_own_email/set_own_email, get_reply_to/set_reply_to,
  get_archive_copy_email/set_archive_copy_email,
  get_default_to/set_default_to, should_translate_placeholders,
  should_compress_images, image_compression_settings, system_info
- Properties: config_dir, settings_file_path, base_dir

---

## 11. AUTOSTART SYSTEM

- Windows: Registry `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (pythonw.exe – ingen terminal)
  (v24.7: `wscript //B "Starta EmailApp.vbs" --background` om VBS finns,
  annars `"pythonw.exe" "main.pyw" --background` – ALDRIG python.exe)
- Linux: `~/.config/autostart/EmailApp.desktop` (`Terminal=false` + `--background`)
- macOS: `~/Library/LaunchAgents/com.emailapp.launch.plist` (`--background`)
- Verify-after-write (läses tillbaka efter varje skrivning)
- Auto-repair: `stale_console` (python.exe/py.exe), `stale_path` (saknad fil),
  `stale_args` (saknar `--background`) repareras i `sync_autostart()`
- Registry-backup roterad max 10 (`autostart_run_backup.json`)
- Konflikter: andra Run-poster med emailapp/main.pyw rapporteras, rörs aldrig
- `sync_autostart()` kallas vid varje app-start
- Fungerar oavsett .py eller .pyw

---

## 12. SINGLE INSTANCE LOCK (`core/single_instance.py` v3.3 – ALLTID AKTIV)

- Windows: Named Mutex (pywin32) → **ctypes-mutex** (CreateMutexW, v3.3 – när pywin32 saknas) → lockfile-fallback
- Linux/macOS: `/tmp/<App>.lock` + fcntl.flock(LOCK_EX | LOCK_NB) → lockfile-fallback
- **POSIX-fokus (spec §12):** Unix-socket `/tmp/<App>.sock` – andra instansen skickar "focus", första visar fönster via `set_focus_callback()`
- Windows-fokus: EnumWindows (fönstertitel matchar app-namn)
- PID-koll: `PermissionError` → processen lever (v3.3-fix)
- Cleanup: atexit-hook + signaler (SIGTERM, SIGINT)
- Context manager (__enter__/__exit__), thread-safe acquire/release
- `ensure_single_instance(app_name)` → (acquired, instance) – instance returneras även när acquired=False (för focus_existing)

---

## 13. SMART RUNTIME MODE & CACHE MANAGER (`core/cache_manager.py` v1.2)

### LÄGEN
- DEV MODE (mode="dev"): cache behålls, debug logging, endast registrerade temp-filer rensas
- PROD MODE (mode="prod" eller smart_cache=false): full cache cleanup vid exit

### VID APP EXIT (PROD)
RENSA: __pycache__/ (rekursivt) · *.pyc · temporära HTML-filer (emailapp_preview_*.html i tempdir) · runtime temp-kataloger
RENSA ALDRIG: contacts.json, adresslistor/, .data/ (settings), plugin data, logs/, Mallar/, själva base_dir

### IMPLEMENTATION (v1.2)
- **EN os.walk med pruning** – skyddade kataloger genomsöks aldrig (~10x snabbare: 0,25 ms vs 2,61 ms)
- is_protected: normcase + prefix-jämförelse; base_dir exakt matchning (buggfix)
- Fail-safe: kastar ALDRIG exception; vid tveksamhet skydda
- Metoder: cleanup, register_temp_file, clear_temp_files, cleanup_pycache, cleanup_pyc_files, cleanup_preview_tmp, is_protected, remove_path (+ _-alias bakåtkompatibla)

---

## 14. EVENT SYSTEM (`core/event_bus.py` v3.5.1)

### API
subscribe(event, handler) → None · unsubscribe(event, handler) → bool
publish(event, data={}) → int · publish_async(event, data={}) → None
clear(event=None) → int · shutdown() → None · get_subscribers(event) → int · get_bus() → EventBus

### FEATURES
- Thread-safe (RLock för mutationer)
- **Snapshot-dispatch (v3.5):** publish() lock-fri – 1,9–3,3x snabbare
- Wildcard-stöd ("mail.*") – matchas endast om mönster finns
- Weak references (förhindrar minnesläckor) – periodisk rensning var 256:e publish
- Exception-loggning per handler (kraschar ej bussen)
- ThreadPoolExecutor för publish_async
- log_event lazy-once (importeras en gång, ej per publish)
- **v3.5.1 unsubscribe-fix (KRITISK):** WeakMethod.__call__() skapar ny bound method → "is" slår aldrig till → _remove_from_list() jämför även (__self__, __func__)

### 14.1 KOMPLETT EVENT-KATALOG
MAIL: mail.sent {subject,count,recipients,elapsed,had_cc,had_bcc} · mail.failed {error,recipients,subject} · mail.progress {current,total,message} · mail.test_ok {host,port} · mail.test_failed {error} · mail.send_requested {params,source} · mail.form_reset {timestamp}
TEMPLATE: template.loaded {path,name,placeholders} · template.saved {path,name} · template.error {error,path} · template.placeholder_changed {key,value,all_values}
SETTINGS: settings.changed {key,old_value,new_value} · settings.saved {path}
CONTACTS: contacts.updated {count,action}
RECIPIENTS: recipients.updated {to_count,bcc_count,total} · recipients.default_loaded {bcc_count}
UI: ui.theme_changed {theme,was} · ui.tab_changed {tab_name} · ui.window_shown {} · ui.window_hidden {} · ui.form_reset {source} · ui.tab_visibility_changed {tab_key,visible}
APP: app.startup {version,mode} · app.shutdown {reason}
MODULE: module.error {module,error,count,disable} · module.disabled {module,reason,count} · module.reset {module}

---

## 15. LOGGER SYSTEM (`core/logger.py` v3.5)

- RotatingFileHandler: 5 MB per fil, 5 backup-filer · UTF-8 encoding (explicit, alltid)
- Format: `%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s`
- StreamHandler ENBART i debug/dev-läge
- **Queue-baserad (v3.5):** QueueHandler + QueueListener – UI-tråden blockerar ALDRIG på disk (~42x snabbare anropstråd)
- `shutdown_logging()` / `flush_logging()` (anropas via atexit + i main.pyw finally)
- sys.excepthook fångar ohanterade exceptions → logg + UI-dialog
- setup_logging(log_dir, level, debug) skapar log-dir automatiskt (fallback till temp)
- get_logger(name) · get_log_file_path(log_dir) · list_log_files() → List[Path]
- LOG-FIL: logs/email_app.log
- Helpers: log_module_load/start, log_dep_check, log_startup_begin/step/complete,
  log_shutdown_begin/step/complete, log_perf, PerfTimer, log_event (dev),
  log_module_error/disabled/reset, set_ui_error_callback, set_dev_mode
- **VALD FÖRSLAG (att implementera):** automatisk loggrensning (10 dagar) – `cleanup_old_logs(log_dir, days=10)`

---

## 16. RECOVERY SYSTEM (`core/recovery_manager.py` v3.5)

- Spårar fel per modul (dict i minnet) · 3 failures → permanent disable (tills omstart/manuell reset)
- Publicerar module.error / module.disabled / module.reset via EventBus
- **is_disabled() lås-fri (v3.5)** via _disabled_cache (set-membership) – ~3,6x snabbare
- publish sker EFTER lås släppts (v3.5)
- @safe_module-dekorator (suppress, fallback)
- reset(module) / reset_all() · get_status() → {module: {errors, disabled}}
- init_recovery_manager(bus) → singleton

---

## 17. PLUGIN SYSTEM (FAS 3 – EJ IMPLEMENTERAT)

PLUGIN CONTRACT: init(settings, event_bus) → None · register_ui(parent) → Frame · shutdown() → None · config_schema() → dict
REGLER: plugins isolerade (fel påverkar ej andra) · failure → RecoveryManager disable · lazy loading · EventBus-only · varje plugin = underkatalog med __init__.py + plugin.py · states i plugin_states · ingen profiles-skapande · alla filer i samma mapp uppdateras innan ny mapp

---

## 18. CONTACTS & RECIPIENTS (UNIFIED FORMAT)

### contacts.json FORMAT (unified – ENBART detta format sparas)
```json
{"contacts": [{"email": "...", "name": "...", "company": "...", "group": "...", "language": "en", "categories": ["..."]}]}
```
- Läser även gammalt email-keyed-format och auto-konverterar till unified
- `favorite`: true (framtida, bakåtkompatibelt – ej obligatoriskt)
- `language` (v4.4): "sv"/"en" – mail-språk för kontakten. Skrivs bara
  när avvikande (default "sv"), bakåtkompatibelt med äldre filer.

### script/contacts_ui.py (v4.5)
- Contact dataclass (normalisering: email lowercase, language sv/en,
  group→categories-sync, ==/hash på email)
- ContactStore: load/save (atomic), add/upsert/update/delete/get/all/count/search/by_group/by_category/categories/grouped_by_category/import_csv/export_csv/clear/reload
- **reload med mtime-cache (v4.3)** – kontaktfliken laddar om när fliken öppnas, men läser disk endast om filen ändrats
- **Kategori-dropdown-cache** (byggs endast om kategorierna ändrats)
- **SMART SORTERING (v4.5):**
  * **Naturlig sortering** (_natural_key): "Kund 2" före "Kund 10",
    "Vindruta 3" före "Vindruta 12" – siffror numeriskt, case-insensitivt
  * **Svensk ordning**: lower-case → å/ä/ö sist (Åberg efter Zetterlund)
  * **Kolumnklick**: klicka på rubriken (Namn/E-post/Företag/Språk/
    Kategori) → stigande; igen → fallande; pil-indikator i rubriken;
    dropdownen synkas
  * **Språk (SV först)/(EN först)** ersätter Språk (A-Ö)/(Ö-A) – namn
    alltid stigande inom gruppen
- ContactsTab: sök (live), filter per kategori, **språkfilter (Alla/SV/EN)**,
  sortering (Namn/E-post/Företag/Kategori/Språk, A-Ö/Ö-A), **språkkolumn "🌐 Språk" (🇸🇪 SV/🇬🇧 EN)**, högerklicksmeny (Lägg i To/Bcc, Redigera, Ta bort, Kopiera e-post), on_add_to-callback, status/sammanfattning (med SV n · EN n)
- _ContactEditDialog: **"🌐 Språk"-dropdown (🇸🇪 Svenska / 🇬🇧 Engelska)**, kategori-checkboxar + ny kategori (kommaseparerad)
- CSV: export inkluderar "language"-kolumn, import läser den
- **EventBus med bundna metoder** (lambdas GC:as av weakrefs – v4.3-fix)
- QAbstractItemView.SelectionMode explicit · setUniformRowHeights(True)

### script/recipients.py (v5.4)
- Contact dataclass (lokal kopia) · _StoreAdapter (garanterar grouped_by_category, korskompatibel med contacts_ui-store)
- ContactStore (lokal) · RecipientStore (To/Bcc i minnet, INGEN CC)
- AddressBookDialog (v5.4):
  - **STÄNGS INTE vid "Lägg till"** – on_add-callback + statusfeedback ("✅ N adress(er) lades till i TO.") + "✅ Klar"-knapp
  - Kategorisidopanel med avatarer (deterministiska färger – sum(ord), ej hash) + tom-state
  - Sortering: Namn/E-post/Företag/Kategori + A-Ö/Ö-A
  - Kontextmeny: Lägg till To/Bcc, Redigera, Ta bort, Kopiera e-post
  - CRUD direkt i adressboken (➕ Ny kontakt, ✏️ Redigera, 🗑️ Ta bort)
  - Bevarad vald kategori vid uppdatering
  - Info: "N markerade · M synliga · T totalt"
- AddContactDialog (kategori-checkboxar, redigeringsläge låser e-post)
- RecipientsTab: 3-stegsflöde (① Importera – adressbok/fil · ② Lägg till manuellt · ③ Granska To/Bcc)
- load_defaults() för standard-Bcc · events via bundna metoder

---

## 19. STANDARDMOTTAGARE, ARKIVKOPIA & SENASTE MOTTAGARE (v4.9)

### STANDARDMOTTAGARE (Standard-To + Standard-Bcc)
- Settings: "default_to" + "default_bcc" (listor av strängar)
- Vid app-start + efter formulärrensning: fylls automatiskt i (To + Bcc-listor)
- UI: Inställningar → 📂 Sökvägar → "Standard-To (kommaseparerat)" + "Standard-Bcc (kommaseparerat)" + SettingsDialog-grupper ("📌 Standardmottagare To" + "📌 Standardmottagare Bcc")
- Validering (email-validator/regex) när de läggs till
- Event: recipients.default_loaded publiceras vid init
- `_load_default_recipients()` (v4.9) fyller To + Bcc + arkivkopia; `_load_default_bcc()` finns som alias

### ARKIVKOPIA (v4.7)
- Settings: "archive_copy_email"
- Fast e-postadress som ALLTID får en kopia (dold Bcc) på varje skickat mail
- Inkluderas i SendWorker._resolve_default_bcc() + _default_bcc_with_archive() (dedupe, case-insensitivt)
- Laddas tillbaka efter formulärrensning

### SENASTE MOTTAGARE
- Settings: "recent_recipients" (lista av dict {"email", "name", "last_used"})
- Efter lyckad sändning: unika mottagare (To+Bcc) sparas med timestamp
- Max 50 entries, FIFO-borttagning vid överflöd
- Kan nollställas via knapp i SettingsDialog (markerar flagga, sparas vid Spara)

---

## 20. HISTORIK ÖVER SKICKADE MAIL (v4.8/v4.9)

Programmet har en egen tab: **📨 Historik**

Historiken visar skickade mail med: tidpunkt · ämne · mall · antal To · antal Bcc · antal bilagor · status

Historiken sparas i: `.data/sent_history.json`

### Krav
- Historik skrivs endast efter lyckad sändning
- Max 500 senaste poster sparas
- Historik kan uppdateras via knapp (🔄 Uppdatera)
- Historikfil kan öppnas (📂 Öppna historikfil)
- Historik kan rensas via bekräftelse (🧹 Rensa historik)
- Ingen CC sparas eller visas

### Högerklick i historiken
- **👁️ Visa mottagare** – visar vilka man skickade till (To-lista + Bcc-lista + totalt, i QMessageBox)
- **📋 Kopiera mottagare** – kopierar alla mottagare (To+Bcc, dedupe) till urklipp

### Öppna för redigering / Skicka om (v4.8/v4.9)
- **Dubbelklick på rad** → öppnar mailet i formuläret för redigering/återsändning
- **Högerklick → "✏️ Öppna för redigering / Skicka om"** → samma
- Återställer: mall (om filen finns), ämne, brödtext, platshållarvärden, mottagare (To/Bcc), fritext, engelska-flagga, bilagor (via sparade fullständiga sökvägar)
- Historikposter sparar nu extra data: template_name, body, free_text, replacements, include_english, attachment_paths
- Tydlig status om mall/bilaga saknas ("⚠️ Mallen 'X' saknas · N bilaga(or) saknas")
- Visar Skicka-tabben + uppdaterar preview/sammanfattning

---

## 21. FORMULÄRRENSNING EFTER SKICKAT MAIL (v4.9)

Efter lyckad sändning ska följande tömmas:
- [X] Platshållarfält i UI (textfält + dropdowns – QComboBox töms via setCurrentText(""), ALDRIG clear() som raderar alternativen)
- [X] `settings.replacements_values` → { }
- [X] Ämnesrad
- [X] Fritext
- [X] Bilagor/bilder
- [X] To-lista
- [X] Bcc-lista, därefter laddas Standard-To + Standard-Bcc + Arkivkopia in igen
- [X] **(v5.8) GLASTYP FÖRINSTÄLLD: efter tömning sätts dropdown-
    placeholders (::ruta:: = glastyp) till FÖRSTA alternativet
    "Vindruta" – dropdownen finns kvar och är förinställd, men
    användaren kan alltid välja i menyn. Värdet sparas i
    `replacements_values` = {"ruta": "Vindruta"} så att det gäller
    även vid mallbyte. Övriga fält töms som förut.**

**Ordning (v4.9 – verifierad i test):**
`status → mail.sent → historik sparas → senaste mottagare sparas → RENSAR ALLA FÄLT → ui.form_reset → "✅ Klart"-dialog`
→ När användaren stänger dialogen är formuläret REDAN tomt.

Rensning får endast ske efter: `result.success == True`
Styrs av: `clear_form_after_send` (default true, inställning finns i UI)

---

## 22. INGEN CC – GLOBAL REGEL (v4.3+)

> **Ingen CC i ny kod. Endast To och Bcc.**

### Borttaget från UI
CC-listor · CC-knappar · CC-rader i bekräftelsedialog · Standard-CC i settings-dialog · CC i mottagarflöde · CC i senaste mottagare-dropdown

### Legacy-kompatibilitet
Gamla settings kan fortfarande innehålla `"default_cc": []` – men v4.3+ ska:
- ignorera `default_cc` i UI
- inte skriva tillbaka `default_cc` från SettingsDialog
- inte visa CC i SendConfirmDialog
- inte skicka `recipients_cc` från MainWindow
- ta bort `default_cc` vid migration/spara

### Event-payloads (v4.3+)
```python
recipients.updated = {"to_count": int, "bcc_count": int, "total": int}
recipients.default_loaded = {"bcc_count": int}
```
Gamla event med cc_count tolereras.

---

## 23. MAIN.PYW – BOOTSTRAPPER (v5.0)

TUNN BOOTSTRAPPER – ingen affärslogik.

### STARTSEKVENS (16 steg)
0.5 **`_ensure_pythonw()`** (v4.8/v5.0 – allra först): startad med
    python.exe på Windows → starta om med pythonw.exe (ingen konsol).
    CREATE_NO_WINDOW + cwd + DEVNULL + argv vidarebefordras.
    Loop-skydd via EMAILAPP_USE_PYTHONW=1. Hoppar över: icke-Windows,
    redan pythonw, frozen, pythonw saknas.
0.6 **`--background`/`--minimized`** (v5.0): tas bort från argv (Qt ska
    inte se dem) och tvingar tray-start.
1. Projektrot/sys.path + Qt-runtime env före QApplication
2. Logging setup (setup_logging, tidigast möjligt)
3. sys.excepthook (handle_uncaught_exception)
4. Single instance check (ensure_single_instance + focus_existing vid nekat)
5. SettingsManager (BASE_DIR)
6. EventBus singleton (core.event_bus.bus)
7. RecoveryManager (init_recovery_manager)
8. CacheManager (mode + smart_cache från settings)
9. QApplication (setApplicationName/Version, setQuitOnLastWindowClosed(False))
9.5 **set_app_icon(app)** (v4.7 – core/app_icon v1.0): app-ikonen på
    huvudfönster, dialoger och taskbar (ärvs via QApplication)
10. MainWindow
11. SystemTray (setup)
11.5 **main_window.set_tray(tray)**
12. sync_autostart (v24.7: reparerar stale_console/python.exe)
13. bus.publish("app.startup") {version, mode}
14. show/hide beroende på start_minimized **eller --background** (default: minimerad)
15. app.exec()
16. finally: geometri → tray.shutdown → app.shutdown → settings.save → cache.cleanup → bus.shutdown → **shutdown_logging()** → app.quit → instance.release

### SÄKERHET
- Ingen ctypes-DPI-hack (Qt6 hanterar DPI själv – undviker Windows-varningen)
- Projektroten i sys.path innan lokala imports
- Lokala imports i main() så importfel kan fångas/loggas/visas
- `_write_startup_crash_file(exc)` – sista skyddsnät för pythonw/tyst krasch → logs/startup_crash.log
- `_safe_show_critical(title, message)` – QMessageBox om Qt finns, annars stderr
- handle_uncaught_exception → logg + QTimer.singleShot-dialog
- save_window_geometry: save_geometry() → fallback geometry() → "WxH+X+Y"

---

## 24. KÄNDA FEL / BUGGAR & ÅTGÄRDSPLAN (KOMPLETT)

### Från originalspec (BUG-001 … BUG-056) – alla ✅ ÅTGÄRDADE
| ID | Beskrivning | Fix |
|---|---|---|
| BUG-001 | "auto"-tema kvar i äldre settings | migration + validate → "system" |
| BUG-002 | SyntaxError event_bus | Explicit UTF-8 |
| BUG-003 | ImportError Union/List/Dict | from typing import ... |
| BUG-004 | ImportError ttk | from tkinter import ttk |
| BUG-005 | RecipientStore/RecipientsTab ej i __all__ | Explicita __all__ |
| BUG-006 | Scroll mushjul Linux | Button-4/5 |
| BUG-007 | Tabbar ej tema-korrekta | TNotebook.Tab i theme_engine |
| BUG-008 | main.pyw startar synligt | root.withdraw() direkt efter tk.Tk() |
| BUG-009 | ProgressDialog blockerar | root.after(0,...) |
| BUG-010 | App kör ej utan pystray | try/except ImportError, fallback |
| BUG-011 | ThemeEngine saknar bind_mousewheel | Statisk metod |
| BUG-012 | CacheManager saknas | core/cache_manager.py v1.0 |
| BUG-013 | Hårdkodade färger main_window | theme.get_colors() |
| BUG-014 | on_module_disabled fel parameternamn | data: dict |
| BUG-015 | Extra tk.Tk() i editors | Borttagen |
| BUG-016 | on_template_loaded fel parameternamn | data: dict |
| BUG-017 | SystemTray saknade 'root' | SystemTray(root, ...) |
| BUG-018 | MainWindow skapade egen tk.Tk() | tk._default_root |
| BUG-019 | free_text saknades i send_email() | free_text=params.get(...) |
| BUG-020 | scan_templates_dir skannade bara .docx | Skannar .docx/.html/.htm/.txt |
| BUG-021 | contacts.json lästes ej av RecipientStore | load_from_file stödjer {"contacts":[...]} |
| BUG-022 | RecipientsTab saknade address_dir/contact_store | Parametrar tillagda |
| BUG-023 | main.pyw finally kraschade | Optional-typer + None-init |
| BUG-024 | Engelska-checkbox färger hårdkodade | theme.get_colors() |
| BUG-025 | settings "geometry" vs "window_geometry" | Konsekvent "window_geometry" |
| BUG-026 | plugins/__init__.py saknas | Skapa tom init (FAS 3) |
| BUG-027 | requirements.txt saknas | Skapa med pinnnade deps |
| BUG-028 | grouped_by_category() saknades | Tillagd i contacts_ui |
| BUG-029 | contacts.json fel format | Läser båda, sparar nytt |
| BUG-030 | AddressBookDialog grab_set före UI | build → populate → grab_set |
| BUG-031 | open_address_book 'self' som parent | winfo_toplevel() |
| BUG-032 | contact_store=None i RecipientsTab | Tidig kontroll |
| BUG-033 | result.ok AttributeError | getattr(result,"success",False) |
| BUG-034 | result.summary() AttributeError | build_send_summary() fallback |
| BUG-035 | Log-sökväg fel | base_dir/logs via get_log_path() |
| BUG-036 | theme_engine saknades i SettingsDialog | theme_engine=self.theme |
| BUG-037 | import re längst ner i main_window | Flyttat till toppen |
| BUG-038 | apply_tab_visibility matchade ej | Explicit key_map |
| BUG-039 | on_close() anropade do_quit() direkt | Delegerar till tray._do_quit() |
| BUG-040 | on_shutdown() sparade dubbelt | Sparar enbart till minnet |
| BUG-041 | ContactsTab saknade on_add_to | Callback tillagd |
| BUG-042 | Canvas-höjd fast 160px | Dynamisk: min 60, max 220 |
| BUG-043 | settings saknade nycklar | Tillagda i get_defaults + migration |
| BUG-044 | CacheManager ej integrerad | Steg 8 + finally |
| BUG-045 | main_window.set_tray() saknades | Metod + anrop steg 11.5 |
| BUG-046 | LIVE PREVIEW saknas | on_placeholder_changed → render_live |
| BUG-047 | FORMULÄRRENSNING saknas | reset_form() vid result.success |
| BUG-048 | STANDARDMOTTAGARE saknas | Settings-UI + add_default |
| BUG-049 | SENASTE MOTTAGARE saknas | recent_recipients + dropdown |
| BUG-050 | PLACEHOLDER-LABEL översättning saknas | _PH_SV/_PH_EN + translate |
| BUG-051 | VISA-MENY saknas | build_view_menu() |
| BUG-052 | HÖGERKLICK på tabb saknas | show_tab_context_menu() |
| BUG-053 | MODERNT UI saknas | ThemeEngine v3.4 |
| BUG-054 | CC-stöd saknas (dåtid) | add_to_cc/get_cc_list (sedan borttaget i v4.3 – ingen CC) |
| BUG-055 | SendConfirmDialog visar ej CC (dåtid) | CC-räkning (sedan borttaget) |
| BUG-056 | default_cc/bcc ej validerade | validate_and_coerce: list av str |

### Från PyQt6-migration (BUG-057 … BUG-084) – alla ✅ ÅTGÄRDADE
| ID | Beskrivning | Fix |
|---|---|---|
| BUG-057 | editors docstring """" SyntaxError | Enkla citattecken |
| BUG-058 | editors bind_all() i PlaceholderPanel | Per-widget binding |
| BUG-059 | editors SendConfirmDialog total=closure | self._total instansvariabel |
| BUG-060 | editors grab_set före build_ui | Efter build+center |
| BUG-061 | main_window load_default_recipients dubbel splat | Borttagen |
| BUG-062 | toggle_tab_visibility felaktig | hide/show via tab_frames |
| BUG-063 | restore_all_tabs missar dolda | Loopar tab_frames |
| BUG-064 | sync_view_menu BooleanVar-GC | view_vars dict lagrar refs |
| BUG-065 | on_placeholder_changed tom key | Korrekt key-parameter |
| BUG-066 | system_info() AttributeError | try/except |
| BUG-075 | editors docstring """" SyntaxError (igen) | v3.3 enkla citattecken |
| BUG-076 | recipients saknade QComboBox-import | Toppimport |
| BUG-077 | templates "Document" Pylance-fel | Any istället |
| BUG-078 | email_sender saknade CC-stöd (dåtid) | recipients_cc + SendResult (sedan borttaget) |
| BUG-079 | settings saknade default_cc/bcc (dåtid) | v21 schema (sedan default_cc borttagen) |
| BUG-080 | settings saknade recent_recipients | v21 + 3 metoder |
| BUG-081 | cache_manager privata metoder | v1.1 publika + alias |
| BUG-082 | logger oanvänd internal_log | v3.3 borttagen |
| BUG-083 | recovery event-payload avvikelse | v3.3 spec-kompatibel |
| BUG-084 | event_bus repr lock-race | v3.3 släpper lock |

### Från denna sessions arbete (BUG-100 … BUG-118) – alla ✅ ÅTGÄRDADE
| ID | Beskrivning | Fix |
|---|---|---|
| BUG-100 | send_email saknade compress_images → TypeError | v3.6 + parametrar |
| BUG-101 | send_email saknade preserve_image_dimensions m.fl. → TypeError | v3.7 |
| BUG-102 | EventBus-prenumeration med lambdas GC:ades | Bundna metoder i ALLA UI-filer |
| BUG-103 | event_bus.unsubscribe funkade ej för bundna metoder (WeakMethod) | v3.5.1 (__self__/__func__) |
| BUG-104 | tray QAction.setDefault() fanns ej i PyQt6 → startup-krasch | QMenu.setDefaultAction() |
| BUG-105 | editors `def *process(text*block:)` SyntaxError | Fixad |
| BUG-106 | editors Any ej importerad → "Any is not defined" | Import fixad |
| BUG-107 | email_sender Any ej importerad (cfg: Dict[str, Any]) | Import fixad (helapps-scan) |
| BUG-108 | QClipboard användes utan import i main_window | Import fixad |
| BUG-109 | cache_manager is_protected skyddade ALLT under base_dir | Exakt matchning för base_dir |
| BUG-110 | scan_templates_dir-cache kolliderade (mtime) | Filantal + mtime i nyckel |
| BUG-111 | recipients _color_for_category använde hash() | sum(ord) – stabila färger |
| BUG-112 | AddressBookDialog._selected_contacts() saknades | Tillagd |
| BUG-113 | template-scan cache: borttagen fil upptäcktes ej | Filantal i cache-nyckel |
| BUG-114 | ProgressDialog.update() överskuggade QWidget.update() | Defensiv signatur |
| BUG-115 | _load_default_bcc kraschade utan bus | bus-guard |
| BUG-116 | Formulärrensning tömde ej ämnesraden | v4.9 tömmer allt |
| BUG-117 | Rensning skedde efter "✅ Klart"-dialog | Nu FÖRE dialogen (v4.9) |
| BUG-118 | Bara PDF/dokument bifogade → komprimering startade ändå | v3.7.1 guard |

---

## 25. FILER SOM EJ SKA RÖRAS UTAN INSTRUKTION

Alla filer är uppdaterade och testade i sessionen. Ingen fil är "förbjuden" längre,
men ändringar ska alltid följa: uppdatera spec → skriv kod → testa → verifiera.

---

## 26. FILSTATUS (KOMPLETT – ALLA TESTADE)

| Fil | Version | Status |
|---|---|---|
| core/settings_manager.py | v24.7 | ✅ STABIL + testad (autostart v2: stale_console + verify) |
| core/email_sender.py | v3.9 | ✅ STABIL + testad (kvitton + språkgrupper, 6/6) |
| core/event_bus.py | v3.5.1 | ✅ STABIL + testad |
| core/logger.py | v3.5 | ✅ STABIL + testad |
| core/single_instance.py | v3.3 | ✅ STABIL + testad |
| core/recovery_manager.py | v3.5 | ✅ STABIL + testad |
| core/cache_manager.py | v1.2 | ✅ STABIL + testad |
| core/app_icon.py | v1.0 | ✅ STABIL + testad (PNG/ICO + ritad fallback) |
| icons/app_icon.png + .ico | v5.1 | ✅ NY – app-ikonen (används överallt) |
| script/templates.py | v3.6 | ✅ STABIL + testad (återskapad i workspace v5.0) |
| script/contacts_ui.py | v4.6 | ✅ STABIL + testad (smart sortering + lägg alla visade) |
| script/recipients.py | v5.5 | ✅ STABIL + testad (grupper i adressboken) |
| ui/main_window.py | v5.6 | ✅ STABIL + testad (engelska automatiskt + muskjul + glastyp Vindruta) |
| ui/wheel_guard.py | v1.0 | ✅ STABIL + testad (mushjul skrollar sidan, ändrar ej fält) |
| ui/dialogs.py | v4.9 | ✅ STABIL + testad (checkbox + guide + språkfördelning) |
| ui/editors.py | v4.2 | ✅ STABIL + testad |
| ui/preview.py | v4.3 | ✅ STABIL + testad |
| ui/styles.py | v1.3 | ✅ STABIL + testad |
| ui/tray.py | v4.5 | ✅ STABIL + testad (app-ikon + status-badge) |
| main.pyw | v4.9 | ✅ STABIL + testad (app-ikon + pythonw + muskjulsskydd) |
| Starta EmailApp.vbs | v5.1 | ✅ NY – dubbelklick utan terminal (pyw → pythonw → association) |
| Mallar/Offertförfrågan – anti-spam.txt | v5.0 | ✅ NY (levereras med appen) |
| Mallar/Offertförfrågan – original.txt | v5.0 | ✅ SPARAD (användarens klistring) |
| requirements.txt | – | ⏳ EJ SKAPAD |
| plugins/ | – | ⏳ EJ IMPLEMENTERAT (FAS 3) |

---

## 27. FILER KVAR ATT IMPLEMENTERA

- [ ] requirements.txt (pinnade == versioner)
- [ ] plugins/__init__.py + example_plugin (FAS 3)
- [ ] Integrationstest / pytest-svit (FAS 2-3)
- [ ] Hot reload plugins (FAS 3)
- [ ] VALDA FÖRSLAG: 4. Tangentbordsgenvägar · 6. Tema-knapp i verktygsraden · 7. Automatisk loggrensning (10 dagar)

---

## 28. REQUIREMENTS.TXT (att skapa)

```
PyQt6==6.7.0
python-docx==1.1.2
darkdetect==0.8.0
email-validator==2.2.0
deep-translator==1.11.4
```
Borttaget: `# pystray==0.19.5` (← QSystemTrayIcon), `# Pillow==10.4.0` (← QPainter + QIcon)
Valfritt: `PyQt6-WebEngine==6.7.0` (för QWebEngineView i preview), `googletrans==4.0.0rc1` (alternativ översättning)

---

## 29. FRAMTIDSPLAN (FAS 1-3)

### FAS 1 – STABILITET / MIGRATION (✅ KLAR)
Komplett grundarkitektur · alla core-moduler stabila · alla UI-moduler uppdaterade ·
bilagor, fritext, engelska/översättning · adressbok (CRUD) · dropdown-mall ·
dynamiska placeholder-fält · glastyp-dropdown · contacts.json unified ·
grouped_by_category · _StoreAdapter · CacheManager · set_tray · dynamisk canvas-höjd ·
on_add_to · drag & drop · adressbok stängs ej vid Lägg till · historik öppna/skicka om ·
formulärrensning före dialog · standard-To/Bcc + arkivkopia · live preview med debounce ·
QSS-teman · QSystemTrayIcon

### FAS 2 – ANVÄNDBARHET (v5.0)
- [ ] Schemalagd sändning
- [ ] Sändhistorik med export/statistik
- [ ] Signaturhantering (HTML per avsändare)
- [ ] Flera SMTP-konton
- [ ] Kontaktimport: .vcf + Google Contacts CSV
- [ ] Krypterat lösenord (keyring/Fernet)
- [ ] Mall-redigerare (WYSIWYG för HTML)
- [ ] Logg-viewer med filtrering per nivå
- [ ] Batch-progress med avbryt-knapp
- [ ] Global sök
- [ ] VALDA: Tangentbordsgenvägar · Tema-knapp · Loggrensning (10 dagar)

### FAS 3 – UTVIDGNING (v5.1+)
- [ ] Plugin-system komplett (hot reload)
- [ ] Rapporter: PDF-export (reportlab)
- [ ] OAuth2: Gmail/Outlook (google-auth, msal)
- [ ] Fullständig pytest-testsvit (P0-P3)
- [ ] Packaging: Windows (PyInstaller + NSIS) · macOS (.app + notarization) · Linux (AppImage/.deb/.rpm)

---

## 30. TESTKONTROLLPUNKTER – PRODUKTIONSVERIFIERING

- [X] Starta utan terminal (pythonw.exe / python main.pyw) – inget konsolfönster, tray-ikon aktiv
- [X] Single instance – andra instans fokuserar första
- [X] Tema-switch dark→light→system utan omstart – knappar/tabbar lättlästa
- [X] Tray-beteende – minimerar till tray, enkelklick visar, "Avsluta" = full shutdown
- [X] Mail-sändning (OBLIGATORISK DIALOG) – dialog visas, stäng = ej skickat, bekräfta = skickat
- [X] Bilagor – lägg till/ta bort/rensa, bifogas korrekt i MIME, drag & drop
- [X] Fritext – skrivs, appendas till mailbody, översätts om engelska aktivt
- [X] Engelska/översättning – checkbox aktiverar, deep_translator → googletrans → original, placeholder-labels byts
- [X] Språkregel – svensk del på svenska (Vindruta = Vindruta), engelsk del översatt (Vindruta = Windshield)
- [X] Placeholder-validering – ::ruta:: → dropdown, ::modell:: → textfält, saknat → varning
- [X] LIVE PREVIEW – ändra placeholder → preview uppdateras automatiskt, växla mall → uppdateras
- [X] FORMULÄRRENSNING – skicka mail → alla fält rensas (INNAN dialog), bilagor/fritext/mottagare töms, standardadresser laddas in igen
- [X] STANDARDMOTTAGARE – lägg till i settings → automatiskt ifyllda vid start + efter rensning
- [X] SENASTE MOTTAGARE – skicka → sparas, kan återanvändas
- [X] Adressbok-dialog – öppnas via 📒, visar kontakter per kategori, Lägg till To/Bcc utan att stängas, CRUD, sortering, gruppering
- [X] ContactsTab on_add_to – markera → "Lägg i To/Bcc" → läggs till
- [X] Dropdown-import – välj contacts.json → To: importerar e-postadresser
- [X] Tab show/hide – Visa-meny + högerklick, Återställ alla
- [X] Historik – högerklick visar mottagare, dubbelklick/högerklick öppnar för redigering/skicka om
- [X] Autostart – aktivera → starta om OS → app startar minimerat
- [X] Recovery – 3 fel → modul disabled → notis
- [X] DPI-scaling – ändra skärm-DPI → UI skalar utan overlap
- [X] Settings atomic – avbryt under sparande → .bak används
- [X] Cache cleanup – mode="prod" → __pycache__ rensas, user data bevaras
- [X] Log-rotation – >5 MB → max 5 backup-filer
- [X] Placeholder-översättning – aktivera engelska → labels byts, avaktivera → tillbaka
- [X] Menu-färger – Visa-meny + högerklick-meny tema-anpassade
- [X] Alla 17 filer kompilerar · hela appen importerar och samverkar · bootstrapper end-to-end

---

## 31. INSTALLATION / START – SNABBGUIDE

1. Installera beroenden: `pip install -r requirements.txt`
2. Starta: Windows: `pythonw main.pyw` (eller `python main.pyw`) · Linux/macOS: `python main.pyw`
3. FÖRSTA STARTEN:
   - Programmet startar minimerat i systemfältet → enkelklick på ikonen öppnar fönstret
   - ⚙️ Inställningar → konfigurera SMTP
   - Ställ in Standard-To / Standard-Bcc / Arkivkopia om önskat
   - Välj mall från dropdown i Skicka-flödet (steg ①)
   - Fyll i platshållare (glastyp, bilmodell, reg.nr) → live preview uppdateras
   - Bifoga bilder/filer (steg ② – drag & drop fungerar)
   - Lägg till mottagare (steg ③ – adressbok, standardadresser, senaste)
   - 📤 Skicka (steg ④) → SendConfirmDialog → bekräfta
   - Formuläret rensas automatiskt efter skickat mail (före "✅ Klart"-dialogen)
4. HISTORIK: dubbelklick eller högerklick → "✏️ Öppna för redigering / Skicka om"
5. AVSLUTA: högerklick på tray-ikon → "❌ Avsluta helt" · [X]-knapp minimerar till tray (standard)
6. LOGGAR: logs/email_app.log (roterande) – öppna via Loggar-fliken

---

## 32. KÄNDA BEGRÄNSNINGAR

| Begränsning | Konsekvens |
|---|---|
| python-docx krävs för DOCX-mallar | Utan: enbart HTML/TXT |
| darkdetect valfri | "system" → light fallback |
| QSystemTrayIcon kräver display | Utan: vanligt fönsterläge (fallback) |
| email-validator valfri | Utan: regex-fallback |
| deep-translator krävs för översättning | Utan: googletrans-fallback, sedan original |
| PyQt6 6.7.0+ | Äldre Qt-versioner stöds ej |
| Python 3.10+ | Äldre Python stöds ej |
| Windows Registry (HKCU) | Kräver ej admin-rättigheter |
| macOS LaunchAgent | Kan kräva kod-signering |
| Linux .desktop autostart | Kan k| Linux .desktop autostart | Kan kräva .desktop-fil i ~/.config/autostart |

> ⚠️ ÅTERSTÄLLT (v5.1 Windows-start-session): §33–§39 försvann ur
> workspace-snapshoten (filen var avklippt mitt i §32). Allt innehåll
> nedan återskapades ordagrant från konversationen – inget tappat.

---

## 33. AI ENGINE-REGLER (UPPDATERADE)

Gäller ALLT arbete i detta projekt:

1. **Arbeta ENBART med kod användaren klistrat in eller explicit bett om.**
   Inklistrad/uppdaterad kod sparas ALLTID till workspace.
2. **ARBETSFLÖDESREGEL:** efter **5 kodfiler** → presentera **10 förslag**
   som användaren väljer om hen vill implementera eller inte. Alla förslag
   ska göra appen bättre/snabbare. Valda förslag hamnar i §34.
3. **spec.md får ALDRIG tappa information** – alla versioner, buggar,
   förslag och beslut sparas (inga borttag, bara tillägg).
4. Mail får ALDRIG skickas direkt – **SendConfirmDialog är obligatorisk**.
   Använd `result.success` (INTE `result.ok`).
5. **EventBus-subscribe med bundna metoder** – aldrig lambdas
   (weakrefs GC:ar dem).
6. **Ingen CC i ny kod** – endast To + Bcc. Arkivkopia via dold Bcc.
7. Återkommande önskemål (v5.9): **"50000% bättre"** – gäller BÅDE
   kod OCH design. Varje ändring/leverans ska vara en märkbar
   förbättring: snabbare kod, snyggare/tydligare UI, bättre flöden.
8. Alla svar på svenska; kod med svenska etiketter/meddelanden.
9. Återställande av förlorade spec-avsnitt sker ordagrant från
   konversationen (som här).
10. **100 %-TESTREGEL (OBLIGATORISK, v5.7): ALL kod som skrivs måste
    testas till 100 % INNAN den levereras.**
    * Varje ny/ändrad fil verifieras med: py_compile + enhetstester
      (alla grenar som går att nå) + regression på berörda moduler +
      end-to-end där flödet tillåter
    * Inga undantag: en ändring räknas INTE som klar förrän dess
      testpaket är grönt och redovisat
    * Vid "Funkar allt nu?"-kontroller körs fullständig verifiering
      (alla moduler + nyckelbeteenden) och resultatet redovisas
    * Regeln gäller ALLT: bugfixar, nya funktioner, refaktorering,
      versionsbumpar och spec-uppdateringar
    * Testmiljön (tests_email/pystub med klass-cache) ska hållas
      fungerande – den är en förutsättning för 100 %-testning
11. **FÖRSLAGSREGEL EFTER 10 KODUPPDATERINGAR (v5.8):** efter **10
    koduppdateringar** (levererade/ändrade kodfiler) sedan Omgång 5
    presenterades → presentera **Omgång 5:s 25 förslag** (spec §35)
    igen för användaren, som väljer vilka som ska implementeras eller
    inte. Räknaren förs i §35 Omgång 5 (start: 0/10).
12. **SKRIV ALDRIG OM HELA KODEN (v5.9) – UPPDATERA BEFINTLIG:**
    * All kodändring görs som MINIMALA, RIKTADE uppdateringar av
      befintliga filer/funktioner – aldrig hel omskrivning av en fil,
      klass eller funktion som redan fungerar
    * Vid inklistrad kod: reparera/förbättra det befintliga –
      behåll struktur, API, namn och kompatibilitet; ändra bara det
      som behövs för uppdraget
    * Ingen "renskrivning" av fungerande kod, inga onödiga
      omskrivningar, ingen ändrad stil i onödan
    * Nya funktioner läggs TILL i befintlig struktur (nya metoder/
      klasser/moduler där det passar) – utan att riva upp det gamla
    * Regelbrott = onödig risk för regression; diff:en ska vara liten
      och granskbar per ändring

---

## 34. VALDA FÖRSLAG – SKA IMPLEMENTERAS (BESLUT)

Följande förslag är **valda av användaren** och ska implementeras:

### ✅ 4. TANGENTBORDSGENVÄGAR
- Ctrl+Enter = Skicka (via _send) · F5 = Förhandsgranska · Ctrl+S = Spara mall
- Ctrl+K = Fokusera sök (Kontakter) / global snabbsök
- Ctrl+1–4 = Hoppa till steg ①–④ (Skicka-tabben) · Ctrl+Q = Avsluta
- **Filer:** `ui/main_window.py` (keyPressEvent/shortcuts på QMainWindow) · Låg komplexitet

### ✅ 6. TEMA-KNAPP I VERKTYGSRADEN
- "🌙/☀️"-knapp i toolbar för ett-klick-temabyte
- Använder befintlig `StyleEngine.toggle()` (finns redan)
- Uppdatera ikon/knapptext beroende på aktuellt läge
- **Filer:** `ui/main_window.py` (_build_toolbar) · Låg komplexitet
- **IMPLEMENTERAD 2026-10-19 (main_window v5.8):** `btn_theme` i
  `_build_toolbar`, `_on_theme_button_clicked` anropar `StyleEngine.toggle()`,
  `_update_theme_button` sätter ☀️ Ljust / 🌙 Mörkt efter aktuellt läge.
  EventBus: bundna metoder. Menyn Tema (mörkt/ljust/system) är kvar.

### ✅ 7. AUTOMATISK LOGGRENSNING (10 DAGAR)
- Vid start: ta bort loggfiler äldre än **10 dagar** (email_app.log, email_app.log.1..5, startup_crash.log, launch_*.log)
- Ny funktion i `core/logger.py`: `cleanup_old_logs(log_dir, days=10)`
- Anropas från main.pyw efter setup_logging · Fail-safe (loggar fel, kastar aldrig)
- **Filer:** `core/logger.py`, `main.pyw` · Låg komplexitet

### KOMMANDE – VALDA 2026-09-16 (implementeras när användaren ber om kod)
Status: **KOMMANDE** – ingen kod i denna leverans. Se §47 för full text.

1. **To+Bcc-dubblettvarning** – samma adress i båda → röd rad i bekräftelsen
2. **Historik: öppna tidigare mail** – förstärkning (dubbelklick/öppna finns delvis)
3. **Små thumbnails av bilder vid bifogning**
4. **Bättre autostart** – vidare efter v6.0 (v24.7)
5. **Dubbelklick-start: saknat tillägg → fråga om installera**

---

## 35. ALLA FÖRSLAG SOM PRESENTERATS (SPARADE – INGET TAPPAS)

### Omgång 1 (10 förslag)
1. Krypterat lösenord (keyring/Fernet)
2. Schemalagd sändning
3. Historik-export + statistik
4. vCard-import (.vcf) + Google CSV
5. Signaturhantering (HTML per avsändare)
6. Flera SMTP-konton
7. Lazy-load av tabbar
8. "Ångra rensning" (återställ förra formuläret)
9. Validera mallar direkt vid val
10. Dra-och-släpp mallar in i appen

### Omgång 2 (10 förslag – andra)
1. Cachad översättning (sv→en, minne + disk)
2. Streamade bilagor (minnessnål MIME)
3. Auto-återställ formulär vid krasch (autospar)
4. **Tangentbordsgenvägar** ← VALD
5. Snabbval senaste bilagor
6. **Tema-knapp i verktygsraden** ← VALD
7. **Automatisk loggrensning (10 dagar)** ← VALD
8. Favoritkontakter (stjärna)
9. Global snabbsök (Ctrl+K)
10. Formulärmallar ("Spara som utkast")

### Övriga förslag från diskussion
Lazy-load tabbar · preload mallar (bakgrundstråd) · återanvänd MIME mellan batchar ·
throttlad progress · debounce live-preview · cachad mallinläsning (mtime) ·
debounce kontaktsökning · cachad historik/logg (mtime) · "Ångra rensning".
- **LOKAL AI-ÖVERSÄTTNING (diskuterad v5.2):** mall enbart på svenska;
  engelsk version genereras av lokal AI (Ollama/LM Studio, OpenAI-
  kompatibel API) vid sändning till EN-mottagare. Föreslagen arkitektur:
  core/translator.py (pluggbar backend + ordlista + disk-cache),
  inställningar (server-URL, modell, timeout), [en]-block vinner om det
  finns, "Generera [en]-block"-knapp i mallverktygen. Ej beslutad –
  inväntar användarens val.

### Omgång 3 (10 förslag – presenterade i ikonrundan, valfria att välja)
1. **Spam-diagnostik på mallen** – innan sändning: varningspoäng för
   spam-signaler (länktäthet, versaler, ord som "gratis", snedstreck i
   ämnesrad) med förslag på åtgärder
2. **Utkast ("Skicka som utkast")** – spara ej skickade mail och
   återuppta senare (utkastflik eller i historiken)
3. **Auto-inkrement ordernummer** – {ORDER_ID} fylls automatiskt med
   nästa nummer (från settings), spårar använda nummer
4. **Klickbara länkar i preview** – URL:er/mailto blir klickbara i
   förhandsgranskningen (QTextBrowser i preview)
5. **Snabbsök i historik + loggar** – filtrera medan du skriver
   (debounce), som kontaktsökningen
6. **Bild-miniatyrer i bilagesteget** – ikonvy med förhandsvisning av
   bilder i stället för textlista
7. **Autosparat utkast vid krasch** – om appen avslutas med ifyllt
   formulär: erbjud återställning vid nästa start (koppla
   RecoveryManager)
8. **DSN-rapport i historiken** – när läskvitto/leveranskvitto begärts:
   spara mottagna kvitton/studs och visa i historiktabellen
9. **Datum-placeholders** – {DATE}/{TOMORROW} fylls automatiskt med
   dagens/morgondagens datum i valfritt format (inställning)
10. **Signatur-hanterare** – HTML-signatur per avsändare, infogas
    automatiskt före fritext (i stället för att ligga i varje mall)

### Omgång 4 (25 förslag – presenterade på användarens begäran, valfria att välja)
**BESLUT (v5.2): användaren valde INGET – inget av förslagen 1–25 är
implementerat. Förslagen finns kvar som referens för framtiden.**

**A. Leveransbarhet & anti-spam**
1. **DNS-kontroll i appen** – knapp som slår upp SPF/DKIM/DMARC för
   avsändardomänen (valfri dnspython) och visar grönt/rött + fix-förslag
2. **Testmail till mig själv** – ett klick: skicka nuvarande mall till
   egen adress (snabb kontroll av utseende + spam-score via mail-tester)
3. **Jitter på batch-fördröjning** – slumpmässig variation (±40 %) av
   delay mellan batchar → bryter "massutskicksmönstret" som filter ser
4. **Sändningskoll före skick** – varningar i sänddialogen: ämne > 78
   tecken, bilagor > 25 MB, många mottagare utan Bcc-batchning

**B. Uppföljning & effektivitet**
5. **Svarsregistrering** – markera i historiken när mottagaren svarat
   (ej svarat/svarat) + påminnelse-knapp "Skicka påminnelse"
6. **Mottagarlistor** – spara namngivna grupper ("Glasfirmor",
   "Alla kunder") och fyll To/Bcc med ett klick
7. **Klistra in mottagare från Excel** – klistra in kolumn med
   adresser → tolkas och läggs till (komma/tabb/radseparerad)
8. **Batchkö** – bygg flera mail (olika mallar/mottagare) och skicka
   i följd med kontroll per steg
9. **Offline-kö** – om SMTP misslyckas: spara mailet i kö och skicka
   automatiskt när anslutningen finns igen
10. **Ångra-sändning** – fördröjd sändning (10 s nedräkning med
    Avbryt-knapp) i stället för omedelbar

**C. Mallar & innehåll**
11. **Mall-kategorier** – undermappar i Mallar/ visas som grupper i
    dropdown-menyn
12. **Återställ mallversion** – knapp i Mallverktyg som återställer
    senaste .bak-versionen av en mall (export_template finns redan)
13. **Förhandsvisning i mall-dropdown** – visa första raderna av mallen
    när man väljer den i listan
14. **Egen ordlista för översättning** – dina egna sv→en-termer som
    vinner över Google Translate (t.ex. Vindruta → Windshield)
15. **Fler språkblock** – [fi]/[de] m.fl. utöver [sv]/[en] i mallar
16. **Kom ihåg senast använda mall** – nytt alternativ till
    standardmallen: återställ senaste valet vid start

**D. Prestanda & stabilitet**
17. **Minnessnål historik** – tabellen laddar max 200 rader åt gången
    (virtuell scroll) – snabbare med stor historikfil
18. **ETA i progressdialogen** – uppskattad kvarvarande tid + takt
    (mail/min)
19. **Pausa/återuppta sändning** – pausknapp under stora batchar
20. **Autospar av mallredigering** – malländringar sparas automatiskt
    (debounce) + återställs vid krasch

**E. Design & kontakter**
21. **Bilagor med ikoner + storlek** – filtyp-ikon, storlek och
    drag-omordning i bilagelistan
22. **Typsnittsval i mallredigeraren** – teckensnitt och storlek för
    editorn (inställning)
23. **Rikare kontakter** – telefon, adress och noteringar utöver
    namn/e-post/företag/kategorier
24. **Färgkodad status i historiken** – grön/orange/röd för
    skickat/ej svarat/fel (kopplas till förslag 5)
25. **Ljudnotis** – ljudplupp vid skickat/fel (av/på i inställningar)

### Omgång 5 (25 NYA förslag – sparade som KOMMANDE val, v5.8)
**Regel (v5.8): EFTER 10 KODUPPDATERINGAR presenteras dessa 25 förslag
igen för användaren, som väljer vilka som ska implementeras eller inte.**
**Räknare: 2/10 koduppdateringar (v6.0: settings_manager.py + main.pyw).**
**Inget av förslagen nedan är implementerat – de ligger som referens
för framtiden.**

**A. Arkiv & säkerhet**
1. **Säkerhetskopiering med ett klick** – zip av settings, kontakter,
   mallar, historik och loggar till valfri mapp; återställ från backup
2. **Exportera enskilt mail som .eml/.pdf** – spara skickade mail för
   arkiv/redovisning
3. **PIN-lås på appen** – lås vid start/återöppning (inställning)
4. **App-uppdaterare** – kolla efter ny version av EmailApp (nedladdning
   + installationsvägledning)
5. **Windows-jumplist** – "Senaste mallar"/"Skicka nytt" i
   aktivitetsfältets högerklick

**B. Sändning & innehåll**
6. **Personlig hälsning per mottagare (mail merge)** – {NAME} ersätts
   per mottagare i Bcc-batchar (varje mottagare får egen hälsningsrad)
7. **Mall-varianter A/B** – två versioner av ämne/text, välj per sändning
8. **Prioritetsflagga** – X-Priority (viktigt/normalt/lågt) per mail
9. **Skicka via standardklient** – mailto-fallback till Outlook/
   Thunderbird som alternativ till SMTP
10. **Klistra in bild från urklipp som bilaga** – Ctrl+V i bilagesteget
    skapar bildfil och bifogar
11. **Kopiera mail som HTML till urklipp** – för nyhetsbrev/webbpublicering
12. **Tyst läge** – tillfälligt avaktivera notiser/ikonbyten (t.ex. vid
    presentation)

**C. Mallar & redigering**
13. **Mall-diff och versionshistorik** – se exakt vad som ändrats mellan
    .bak-versioner (utöver återställning)
14. **Sök i mallarnas innehåll** – hitta vilken mall som innehåller en text
15. **Favoritmallar** – stjärna på ofta använda mallar, visas överst
16. **Mallpaket** – export/import av mallar + mappstruktur som .zip
    (dela mellan datorer)
17. **Snabbtextblock (snippets)** – infoga återkommande stycken
    (hälsning, prisinfo) med ett klick
18. **Stavningskontroll i mallredigeraren** – markera felstavade ord
19. **Tecken-/ordräkning i statusraden** – live-räknare i editorn
20. **Auto-komplettering i ämnesraden** – förslag från tidigare ämnen i
    historiken

**D. Kontakter & uppföljning**
21. **Slå ihop dubbletter** – hitta och slå ihop liknande kontakter
    (namn/e-post)
22. **Automatiska påminnelser** – "ingen har svarat inom X dagar" →
    påminnelse i appen (t.ex. för offerter)
23. **Ämnesradsförslag** – förslag utifrån mall + mottagare (statiska
    mallar, ingen AI krävs)
24. **Ångra i mottagarlistor** – Ctrl+Z återställer borttagna
    mottagare/bilagor

**E. Utseende & beteende**
25. **Tema-schema** – automatiskt mörkt/ljust tema efter klockslag

### Omgång 6 (FORSKNINGSBASERADE förslag – v5.9, valfria att välja)
**Källa: forskning i liknande appar (GMass, Mailshake, Woodpecker, Streak,
Pipedrive, Mailspring, Outlook-tillägg m.fl., 2026). Inget implementerat –
ligger som kommande val. Bygger där så anges på tidigare förslag.**

**A. Leverans & listhygien (källa: bounce-hantering i verktygen)**
1. **Verifiera mottagare före utskick** – knapp som kontrollerar
   domänens MX-post + syntax för alla mottagare och flaggar riskadresser
   (skyddar avsändarryktet; "yopail.com"-typo fångas före sändning)
2. **Auto-flagga hard bounces** – SMTP 550/552/553 + DSN FAILURE vid
   sändning markerar kontakten som "studsad"; appen föreslår rensning
   och varnar före nästa utskick (branschregel: ta bort hard bounces
   direkt – skyddar rykte)
3. **Leveransrapport per utskick** – efter sändning: skickat/studsat/
   ej svarat per mottagare + bounce-rate (mål under 2 %)
4. **Färgstatus på kontakter** – verifierad/studsad/gammal (färgkod i
   adressboken) – håller listan ren över tid

**B. Uppföljning & pipeline (källa: Streak/Pipedrive-mönstret)**
5. **Offert-pipeline-vy** – varje mottagare/ärende med status
   (skickad → påmind → svarat → klar/ej svarat) i en överblick, som
   kanban-lista. *Bygger vidare på Omgång 4 #5 + Omgång 5 #22*
6. **"Vad väntar på mig idag?"-vy** – startöversikt: skickat för X
   dagar utan svar, dagens påminnelser, studs att städa
7. **Auto-påminnelseflöden dag 3/7** – påminnelsemail med mall som
   stoppas när svar registreras (manuellt nu; IMAP-avkänning senare)
8. **Anteckningar på historik & kontakter** – snabbnotis
   ("ringde 5/9, svar på väg") som följer posten/kontakten
   (Mixmax/Streak-mönster)

**C. Innehåll & skrivhjälp (källa: GMass spam-test + skrivverktyg)**
9. **Spam-score på innehåll före sändning** – kontroll av ämne/brödtext
   (spam-ord, versaler, tecken, länktäthet) med poäng + åtgärdsförslag
10. **Förslag på följebrevsformulering** – vid "Skicka påminnelse"
    föreslås färdiga, personliga formuleringar att välja bland

**D. Smidighet (källa: desktop-klientgranskningar 2026)**
11. **Klistra in "Namn <epost>"** – klistrar du in en signaturrad
    tolkas den och appen föreslår att spara kontakten (Evercontact-mönster)
12. **Snooze på påminnelser** – "påminn mig på fredag" per ärende
13. **IMAP-koppling (störst, frivillig)** – hämta svar automatiskt och
    synka status + stoppa påminnelseflöden (automatisk svarsavkänning)

**E. Designlärdomar (källa: klientgranskningar: kortare vägar, statusfärger)**
14. **Färgkodad status i historiken** – skickat/påmind/svarat/fel med
    färger och ikoner (kopplas till B.5)
15. **Minsta antal klick till "Skicka"** – Skicka-knappen alltid synlig +
     bygg äntligen §34 #4 (tangentbordsgenvägar: Ctrl+Enter m.fl.) som
     forskningen bekräftar är det mest uppskattade

### Omgång 7 (10 förslag – 2026-09-16, efter arkiverad chat)
**BESLUT:** fem punkter VALDA som **KOMMANDE** (§34 + §47). Ingen kod
i v6.1. Övriga 5 avvaktar.

1. **Alltid-synlig mini-preview** – preview till höger i wizard
2. **Steg-4 checklista** – bockar: mall, glastyp, modell, reg, mottagare, SMTP
3. **SMTP-autofyll från e-post** – t.ex. @bilrutan.se → smtp.websupport.se / 587
4. **To+Bcc-dubblettvarning** ← VALD KOMMANDE (§47.1)
5. **"Senast mail" på kontakt** – kolumn i adressbok/kontakter
6. **Ett klick: samma som förra** – fyll senaste lyckade utskicket
7. **Kompakt / bekväm vy** – täthet i UI
8. **Skrivbordsgenväg** – skapa .lnk till Starta EmailApp.vbs
9. **Bilaga-förhandsvisning / små thumbnails** ← VALD KOMMANDE (§47.3)
   *(Omgång 3 #6 närbesläktad)*
10. **SMTP-hälsokoll vid start** – tyst test, grön/röd i statusfältet

Tillägg valda samma dag (inte i tabellen ovan, egna krav):
- Historik: öppna tidigare mail (§47.2)
- Bättre autostart, vidare efter v6.0 (§47.4)
- Dubbelklick: saknat tillägg → fråga om installera (§47.5)

### Omgång 8 (10 förslag – 2026-10-19, användaren skrev \"förslag\")
**GitHub-regel (samma dag):** pusha efter varje uppdatering, **merga aldrig**.
Remote: `https://github.com/Tokke2/MailOffer.git` — push från Arena saknar inloggning.
**Redan valda utan kod (byggs när användaren säger till):** tema-knapp (§34 #6),
To+Bcc-dubblett (§47.1), historik öppna (§47.2), thumbnails (§47.3),
autostart-polish (§47.4). §47.5 ersatt av automatisk pip + progress (inlagd).
**Nya att välja (inget implementerat förrän användaren väljer nummer):**

1. **Alltid-synlig mini-preview** – förhandsvisning till höger i wizard medan
   man fyller mall/bilagor/mottagare (Omgång 7 #1, ej vald då)
2. **Steg-4 checklista** – bockar: mall, glastyp, modell, reg, VIN vid EN,
   mottagare, SMTP innan skick (Omgång 7 #2)
3. **SMTP-hälsokoll i statusfältet** – tyst test vid start, grön/röd prick
   (Omgång 7 #10)
4. **Ett klick: samma som förra** – fyll senaste lyckade utskicket
   (Omgång 7 #6)
5. **Klistra in bild från urklipp som bilaga** – Ctrl+V i steg ② skapar
   bildfil och bifogar (Omgång 5 #10)
6. **Sändningskoll före skick** – varning i bekräftelsen: ämne > 78 tecken,
   bilagor > 25 MB, många mottagare (Omgång 4 #4)
7. **Thunderbird: spara även To / Svara-till** – inte bara avsändare (From)
   vid högerklick → kontakter
8. **Kom ihåg senast använda mall** – återställ senaste valet vid start,
   utöver standardmallen (Omgång 4 #16)
9. **Tecken-/ordräkning i mallredigeraren** – live i statusraden
   (Omgång 5 #19)
10. **Kompakt / bekväm vy** – tätare UI, mindre tom yta (Omgång 7 #7)

---

## 36. SESSIONENS ARBETE – SAMMANFATTNING (ALLT SOM GJORTS)

### 36.1 Alla filer som klistrats in → reparerade + förbättrade + testade
1. **core/email_sender.py** v3.5 → **v3.7.1**: compress_images + inställningsstyrda parametrar, QImage-komprimering (Pillow-fallback), temp-rensning, atexit, v3.7.1 guard (endast om bilder finns), markdown-mangling reparerad
2. **core/cache_manager.py** v1.1 → **v1.2**: EN os.walk med pruning (~10x snabbare), is_protected normcase+prefix, base_dir exakt match
3. **core/event_bus.py** v3.4 → **v3.5.1**: snapshot-dispatch (lock-fri publish, 1,9–3,3x snabbare), lazy log_event, unsubscribe-fix för bundna metoder (__self__/__func__)
4. **core/logger.py** v3.4 → **v3.5**: queue-baserad (42x snabbare anropstråd), shutdown_logging/flush_logging, cachade loggers
5. **core/recovery_manager.py** v3.4 → **v3.5**: is_disabled lås-fri (3,6x snabbare), publish efter lås
6. **core/settings_manager.py** v24 → **v24.3**: copy-on-write (lås-fri get, 3,4x snabbare), archive_copy_email (v24.2), default_to (v24.3)
7. **core/single_instance.py** v3.2 → **v3.3**: ctypes-mutex, POSIX socket-fokus, PID PermissionError-fix
8. **script/templates.py** v3.5 → **v3.6**: scan-cache (filantal+mtime), early-return, SyntaxError fixad
9. **script/contacts_ui.py** v4.2 → **v4.3**: mtime-cachad reload, kategori-cache, bundna metoder
10. **script/recipients.py** v5.3 → **v5.4**: _selected_contacts fixad, deterministiska färger, adressbok kvar vid lägg till
11. **ui/dialogs.py** v4.3 → **v4.6**: ProgressDialog defensiv, arkivkopia-fält, Standard-To-grupp
12. **ui/editors.py** v4.1 → **v4.2**: bundna metoder, set_known-skydd, Any-import fixad
13. **ui/preview.py** v4.2 → **v4.3**: bundna metoder (live preview funkade ej), ren HTML-template, parse-cache, debounce
14. **ui/styles.py** v1.2 → **v1.3**: QSS-cache (get_cached_qss)
15. **ui/tray.py** v4.3 → **v4.4**: ikoncache, handlers i _handlers (unsubscribe fungerar), dubbelklick
16. **ui/main_window.py** v4.5 → **v4.9**: bundna metoder, QClipboard-import, debounce, DOCX-säker sparning, arkivkopia, rensning inkl. ämne, historik öppna/skicka om, Standard-To, dubbelklick historik, rensning före dialog
17. **main.pyw** v4.5 → **v4.6**: shutdown_logging i finally, crash-fil, safe_show_critical

### 36.2 Verifiering
- Alla filer kompilerar (py_compile)
- Hela appen importerar och samverkar (core+script+ui med stubbade PyQt6)
- Bootstrapper end-to-end (main() → app.exec → finally-kedja → lock-släpp)
- Tester per modul: alla gröna
- **(v5.7) 100 %-TESTREGEL §33.10: all kod testas till 100 % innan
  leverans – se regeln (obligatorisk).**

### 36.3 Session v5.0 (leveransbarhet)
1. **core/settings_manager.py** v24.3 → **v24.4**: request_receipts (bool, false)
2. **core/email_sender.py** v3.7.1 → **v3.8**: request_receipts-param, kvitto-headers
   (Disposition-Notification-To/Return-Receipt-To), SMTP-DSN fail-safe,
   SendResult.receipts_requested (6/6 tester)
3. **ui/dialogs.py** v4.6 → **v4.7**: kvittocheckbox + result_params() +
   DeliverabilityGuideDialog (HTML-guide + kopiera DNS + mail-tester)
4. **ui/main_window.py** v4.9 → **v5.0**: request_receipts genom hela kedjan
   (params → dialog → worker → send_email), inställningsgrupp
   "📨 Leveransbarhet", guide-knapp i Inställningar + Hjälp-menyn
5. **script/templates.py** v3.6 återskapad (fanns ej i snapshot) – trogen spec §9
6. **Mallar/**: Offertförfrågan – anti-spam.txt (ny) + original.txt (sparad)
7. **spec.md** → v5.0 (ny §37-38, filstatus, versioner)

### 36.4 Session v5.1 (standardmall)
1. **core/settings_manager.py** v24.4 → **v24.5**: default_template (str, "")
   + get_default_template()/set_default_template() + str_fields
2. **ui/main_window.py** v5.0 → **v5.1**: ny inställningsgrupp
   "📝 Standardmall" (dropdown + uppdatera-knapp), _apply_default_template(),
   _template_names()-refaktor, _scan_tpls() med standardmall vid första
   inläsning + behåller användarens val vid omskanning,
   _collect/_reload hanterar "(ingen – senast valda)" → ""
3. **spec.md** → v5.1 (ny §38, schema, filstatus)

### 36.5 Session v5.1 (ikonrunda)
1. **main.pyw** v4.6 → **v4.7**: set_app_icon(app) (steg 9.5), ikon även på
   kritiska dialoger, APP_VERSION 4.6.0 → 5.1.0 (synk med UI)
2. **core/app_icon.py** v1.0 (NY): central ikonladdning med cache –
   PNG → ICO → ritad fallback (appen får ALLTID en ikon)
3. **ui/tray.py** v4.4 → **v4.5**: idle = app-ikonen, statuslägen =
   app-ikonen + badge (…/!/✓), APP_VERSION 5.1
4. **icons/app_icon.png** (512x512 RGBA, rundade hörn, AI-genererad +
   programmatisk puts) + **app_icon.ico** (16–256 px, Windows)
5. **spec.md** → v5.1 (ikonrunda): §39, filstatus, §23 steg 9.5, §35 omgång 3

### 36.6 Session v5.1 (Windows-start)
1. **main.pyw** v4.7 → **v4.8**: _ensure_pythonw() (steg 0.5 – omstart
   med pythonw om appen körs med konsol; loop-skydd EMAILAPP_USE_PYTHONW)
2. **core/settings_manager.py** v24.5 → **v24.6**: _find_pythonw()
   (bredvid exe → base_prefix → PATH), _script_path() (argv0 → projekt),
   autostart-kommandot använder pythonw (ingen konsol vid registry-start)
3. **Starta EmailApp.vbs** (NY): dubbelklick-lanserare utan terminal –
   fallkedja pyw.exe → pythonw.exe → association
4. **spec.md** → v5.1 (Windows-start): §40, filstatus, §23 steg 0.5,
   §33-§39 återställda efter snapshot-klipp

### 36.7 Session v5.2 (språkgrupper)
1. **script/contacts_ui.py** v4.3 (NY i workspace – användarens klistring
   sparad ordagrant, 1175 rader): kompilerar + ContactStore/Contact/CSV
   testade med stubbad PyQt6
2. **core/email_sender.py** v3.8 → **v3.9**: recipients_to_lang /
   recipients_bcc_lang, per-språk parsing (endast använda språk),
   batchar to_sv/to_en/bcc_sv/bcc_en, SendResult.recipients_sv/en +
   had_language_split, summary-rad "🌐 Språk: SV n · EN n" (6/6 tester)
3. **ui/main_window.py** v5.1 → **v5.2**: "🌐 Språk för nya mottagare"-
   dropdown, taggade mottagare [SV]/[EN], högerklick-meny + dubbelklick
   för språkbyte, recipients_to_lang/bcc_lang i params, sammanfattning
   med språkfördelning, historik sparar/återställer språktaggar
4. **ui/dialogs.py** v4.7 → **v4.8**: SendConfirmDialog visar
   "🌐 Språk: SV n · EN n" + varning när EN-markerade finns men
   engelska är av
5. **spec.md** → v5.2 (ny §41, filstatus, §8, §2)

### 36.8 Session v5.3 (kontakter med språk)
1. **script/contacts_ui.py** v4.3 → **v4.4**: Contact.language ("sv"/"en",
   default sv), to_dict/from_dict (language sparas bara avvikande),
   upsert/update med language, _ContactEditDialog får "🌐 Språk"-dropdown,
   ContactsTab får språkkolumn + sortering "Språk (A-Ö)/(Ö-A)",
   CSV export/import med language
2. **ui/main_window.py** v5.2 → **v5.3**: _contact_lang(email) slår upp
   kontaktspråk i ContactStore; inkopplad på 5 ställen
   (_address_book_add_callback, _contacts_tab_add_to,
   fallback-adressboken add_selected + kompatibilitetsväg) –
   kontakter läggs in med rätt [SV]/[EN]-tagg automatiskt
3. **spec.md** → v5.3 (ny §42, §18-format med language, filstatus)

### 36.9 Session v5.4 (engelska automatiskt – ingen knapp)
1. **ui/main_window.py** v5.3 → **v5.4**: "Inkludera engelsk version"-
   checkboxen borttagen (steg 1 ersatt med info-text + inställningsfliken),
   _on_en_toggle borttagen, placeholder-labels alltid svenska (_PH_SV),
   _gather_send_params härleder include_english från mottagarnas språk
   (EN i To ELLER Bcc → True), historik-återställning utan knapp,
   inställningen include_english lämnas som legacy (oanvänd)
2. **ui/dialogs.py** v4.8 → **v4.9**: _include_en + språkvarningsraden
   borttagna (kan aldrig inträffa längre) – "🌐 Språk: SV n · EN n" kvar
3. **spec.md** → v5.4 (uppdaterad §41-regel 4, filstatus)

### 36.10 Session v5.5 (smartare kontaktslista)
1. **script/contacts_ui.py** v4.4 → **v4.5**:
   - _natural_key(): naturlig sortering (siffror numeriskt, "Kund 2"
     före "Kund 10"), case-insensitiv
   - Svensk ordning: lower-case → å/ä/ö sist
   - _on_header_clicked() + _update_sort_indicator(): sortera med
     kolumnrubrik-klick (stigande/fallande, pil-indikator), dropdownen
     synkas via _HEADER_SORT_MAP
   - Språkfilter (_lang_filter_cb): (Alla) / 🇸🇪 SV / 🇬🇧 EN – kombineras
     med kategori-filter + sök
   - "Språk (SV först)/(EN först)" ersätter "Språk (A-Ö)/(Ö-A)";
     rank-nyckel sv=0/en=1, namn alltid stigande inom gruppen
   - Sammanfattning: "SV n · EN n · Filter: <kategori>/<språk> · Sortering"
2. **ui/editors.py** v4.2 – verifierad identisk med användarens klistring
   (redan sparad, ingen ändring)
3. **spec.md** → v5.5 (ny §43, §18, filstatus)

### 36.11 Session v5.5 (recipients.py i workspace)
1. **script/recipients.py** v5.4 – ANVÄNDARENS KLISTRING SPARAD (2096
   rader, den fil som tidigare saknades i workspace-snapshoten):
   Contact + initials, _StoreAdapter (korskompatibel), lokal ContactStore
   (CRUD/CSV), RecipientStore (To/Bcc), AddContactDialog,
   AddressBookDialog (kategorier, avatarer, stängs ej vid Lägg till),
   RecipientsTab (3-stegs), load_legacy_txt
2. **Testmiljö:** PyQt6-stubben utökad (QListWidget/QComboBox/QLineEdit-
   metoder: count/item/text/toPlainText/currentData) så att dialoger och
   tabbar kan instansieras i tester
3. **Verifierat:** Contact/validering, ContactStore CRUD+CSV,
   RecipientStore to/bcc/dedupe/defaults, _StoreAdapter mot
   contacts_ui.ContactStore (språk bevaras via to_dict/from_dict),
   AddressBookDialog + sortering (A-Ö/Ö-A), RecipientsTab-publik-API,
   load_legacy_txt, integration med main_window (AddressBookDialog +
   _contact_lang), full regression 21 moduler
4. **spec.md** → v5.5 (filstatus: recipients.py ✅ i workspace)

### 36.12 Session v5.6 (grupper i adressboken)
1. **script/recipients.py** v5.4 → **v5.5**: AddressBookDialog –
   gruppåtgärdsrad ("📚 <Grupp>: n mottagare" + "➕ Alla (n) → To/Bcc"),
   _category_emails(), _emit_add_all(), kontextmeny på kategorilistan
   ("➕ Lägg till alla (n) som To/Bcc" + "↕ Sortera A-Ö" /
   "↕ Sortera efter antal"), _categories_sort (alpha/count)
2. **script/contacts_ui.py** v4.5 → **v4.6**: "➕ Alla visade → To/Bcc"-
   knappar i kontaktfliken, self._last_visible i refresh_list, _push_all()
3. **ui/main_window.py** (v5.4 oförändrad version, tillägg): fallback-
   adressboken får "➕ Alla visade → To/Bcc"-knappar + add_all()
4. **spec.md** → v5.6 (ny §44, filstatus, versionshuvud)

### 36.13 Session v5.7 (muskjulsskydd)
1. **ui/wheel_guard.py** v1.0 (NY): globalt event-filter på QApplication –
   när mushjulet används över värdekänsliga fält (QComboBox,
   QAbstractSpinBox/QSpinBox/QDoubleSpinBox/QDateTimeEdit, QSlider/QDial,
   QLineEdit) konsumeras händelsen och skrollningen skickas till
   närmaste QScrollArea (40 px/notch, vertikal + horisontell).
   Fältvärdet ändras ALDRIG. Undantag: öppen combo-popup skrollas som
   vanligt; QScrollBar exkluderas; textfält/listor/träd skrollar sig
   själva. Klassnamnsbaserad + isinstance-fallback (robust i riktig Qt).
2. **main.pyw** v4.8 → **v4.9**: install_wheel_guard(app) efter
   QApplication-skapandet (steg 9.6)
3. **ui/main_window.py** v5.4 → **v5.5**: install_wheel_guard() i
   MainWindow.__init__ (idempotent fallback)
4. **Testmiljö:** PyQt6-stubben fick klass-cache (_CLASS_REGISTRY) –
   isinstance fungerar nu mellan moduler (samma klass per namn)
5. **spec.md** → v5.7 (ny §45, filstatus, versionshuvud)

### 36.14 Session v5.8 (glastyp förinställd efter rensning)
1. **ui/main_window.py** v5.5 → **v5.6**: _reset_form_after_send()
   återställer dropdown-placeholders (PLACEHOLDER_DROPDOWNS, dvs
   ::ruta:: = glastyp) till options[0] = "Vindruta" efter tömning;
   sparar "replacements_values" = {"ruta": "Vindruta"} så att
   förinställningen gäller även vid mallbyte. Övriga fält töms som
   förut. Användaren kan alltid välja i dropdown-menyn.
2. **spec.md** → v5.8 (versionshuvud fixat till 5.8, §21 uppdaterad,
   ny §46, session 36.14, footer)

### 36.15 Session v5.8 (Omgång 5 – 25 nya förslag)
1. **spec.md §35**: Omgång 5 med 25 HELT NYA förslag (inga dubbletter
   av omgång 1–4) sparade som KOMMANDE val – arkiv/säkerhet (5),
   sändning/innehåll (7), mallar/redigering (8), kontakter/uppföljning
   (4), utseende/beteende (1). Inget implementerat.
2. **spec.md §33 punkt 11**: FÖRSLAGSREGEL – efter 10 koduppdateringar
   presenteras Omgång 5 igen för användarens val. Räknare 0/10 i §35.
3. **spec.md**: versionshuvud + footer uppdaterade (v5.8, omgång 5)

### 36.16 Session v5.9 (regler + forskningsbaserade förslag Omgång 6)
1. **spec.md §33 punkt 7**: "500% bättre" → **"50000% bättre"** – gäller
   BÅDE kod OCH design (snabbare kod, snyggare/tydligare UI, bättre flöden)
2. **spec.md §33 punkt 12 (NY)**: **SKRIV ALDRIG OM HELA KODEN** –
   all kodändring görs som minimala, riktade uppdateringar av befintlig
   kod; vid inklistrad kod repareras/förbättras det befintliga utan att
   struktur/API/namn rivas upp; inga onödiga omskrivningar; diff:en ska
   vara liten och granskbar per ändring
3. **spec.md**: versionshuvud → v5.9 + två nya rubrikrader, session
   36.16, footer → v5.9. (Specändring – räknar EJ i 10-koduppdateringarna.)

### 36.17 Session v5.9 (Omgång 6 – forskningsbaserade förslag)
1. **Forskning i liknande appar** (GMass, Mailshake, Woodpecker, Streak,
   Pipedrive, Mailspring, Outlook-tillägg 2026): sammanställda mönster –
   listhygien/bounce-hantering, uppföljnings-pipelines, spam-test på
   innehåll, klistra-in-kontakt, snooze, IMAP-svarsavkänning,
   statusfärger, tangentbordsgenvägar
2. **spec.md §35**: Omgång 6 med 15 forskningsbaserade förslag sparade
   som kommande val (inga dubbletter; bygger där så anges på R4/R5).
   Inget implementerat.
3. **spec.md**: rubrikrad + session 36.16/36.17 uppdaterade. (Specändring –
   räknar EJ i 10-koduppdateringarna.)

---

## 37. V5.1 – STANDARDMALL (ANVÄNDARBESLUT)

Användaren bad om: "kunna sätta mall i inställningar till standardmall som
alltid används, om inte användaren ändrar i dropdown-menyn."

### Regler (exakt beteende)
1. **Inställningar → "📝 Standardmall"**: dropdown med "(ingen – senast
   valda)" + alla mallar i Mallar/ (.docx/.html/.htm/.txt, utan ~$/bak/tmp).
2. **Vid start**: standardmallen väljs automatiskt om inställningen är satt
   och filen finns; annars första mallen (som förut). Saknas standardmallen
   visas varning + första mallen väljs.
3. **Manuella dropdown-val VINNER**: när användaren byter mall på
   Skicka-fliken gäller det valet tills appen startas om – standarden
   appliceras INTE igen vid "🔄 Sök" eller formulärrensning.
4. **Spara i inställningarna** → standardmallen appliceras direkt.
5. **Formulärrensning efter skickat mail** påverkar inte mallvalet
   (befintlig regel: mallval + malltext behålls).
6. **Omskanning (🔄 Sök)**: behåller användarens nuvarande mall om den
   fortfarande finns (v5.1 – byter inte tillbaka till första mallen).

### Filer
- `core/settings_manager.py` v24.5 – default_template + hjälpmetoder
- `ui/main_window.py` v5.1 – grupp, _apply_default_template(),
  _template_names(), _scan_tpls()-logik, formulärkoppling

---

## 38. V5.0 – LÄSKVITTO, LEVERANSBARHETS-GUIDE & ANTISPAM-MALL (ANVÄNDARBESLUT)

Användaren bad om: (1) Leveransbarhets-guide – ja tack, (2) checkbox för
lev/läskvitto, (3) uppdaterad Offertförfrågan-mall som slipper SPAM med
grundinställningarna. Allt implementerat och testat.

### 38.1 LEVERANS-/LÄSKVITTO (checkbox i sänddialogen)
- **UI:** `ui/dialogs.py` v4.7 – SendConfirmDialog får checkboxen
  "📨 Begär leverans- och läskvitto" + `result_params()` som MainWindow
  hämtar efter bekräftelse (dialogen anropar aldrig sändning direkt).
- **Flöde:** `ui/main_window.py` v5.0 – `_gather_send_params()` sätter
  `request_receipts` (från settings v24.4); `_confirm_send()` slår ihop
  dialogens `result_params()`; `SendWorker.run()` skickar
  `request_receipts` till `send_email()` (v3.8).
- **Kärna:** `core/email_sender.py` v3.8 –
  - Headers: `Disposition-Notification-To` (läskvitto, RFC 3798 –
    Outlook frågar mottagaren) + `Return-Receipt-To` (många
    servrar/klienter).
  - SMTP-DSN (RFC 3461): `rcpt_options=["NOTIFY=SUCCESS,FAILURE"]`
    ENBART om servern annonserar `dsn` i EHLO (`esmtp_features`).
  - Fail-safe: RCPT nekad med DSN-option → nytt försök UTAN DSN i
    samma anslutning. **Kvitto är aldrig ett skäl att misslyckas.**
  - `SendResult.receipts_requested` + rad i summary().
- **Settings:** `core/settings_manager.py` v24.4 – `request_receipts`
  (bool, default false). Schema förblir 24 (defaults-merge).
- **Verifierat:** dry-run headers 3/3 · DSN 6/6 · end-to-end worker
  (True/False/arkivkopia) 3/3.
- **Viktigt att veta:** läskvitto kan alltid nekas av mottagarens
  klient; leveranskvitto är inte garanterat – servern avgör.

### 38.2 LEVERANSBARHETS-GUIDE (knapp i Inställningar + Hjälp-menyn)
- **UI:** `ui/dialogs.py` v4.7 – `DeliverabilityGuideDialog` med
  QTextBrowser (HTML-guide) + knappar:
  - "📋 Kopiera DNS-poster" → SPF/DKIM/DMARC till urklipp
  - "🧪 mail-tester.com" → öppnar webbläsaren
  - "✅ Stäng"
- **Placering:** `ui/main_window.py` v5.0 – ny inställningsgrupp
  "📨 Leveransbarhet (mot skräppost)" + Hjälp-menyn
  ("📖 Leveransbarhets-guide").
- **Innehåll (WebSupport):** SPF `v=spf1 include:_spf.websupport.se ~all`,
  DKIM via kontrollpanelen (`default._domainkey...`), DMARC
  `v=DMARC1; p=none; rua=mailto:dmarc@din-domän.se` (börja p=none,
  skärp senare till p=quarantine). SMTP `smtp.websupport.se` 587
  STARTTLS / 465 SSL, användarnamn = hela e-postadressen.
- Innehållstips (rak ämnesrad utan "/", ren signatur, personlig text,
  batch 5–10 med fördröjning) · Thunderbird-träning ("Inte skräppost",
  (E)-taggen = filter) · kvitton förklaras · mail-tester.com 10/10-mål.

### 38.3 ANTISPAM-MALL (Offertförfrågan)
- **Nya mallar i `Mallar/`:**
  - `Offertförfrågan – anti-spam.txt` – rekommenderad (använd denna)
  - `Offertförfrågan – original.txt` – användarens klistring sparad
- **Ändringar som minskar SPAM-signaler:**
  - Ämne: `Offertförfrågan: ::ruta:: till ::modell:: (::reg::)` –
    ordet "förfrågan" gör syftet tydligt (en förfrågan, inte ett
    erbjudande), inget snedstreck, inget företagsnamn/suffix.
  - Signatur rensad: en telefon, en e-post, båda adresserna på en rad,
    webbplatsen borttagen (länktäthet sänks), konsekvent avsändarnamn.
  - Inga "______"-separatorrader, inga tabb-bullets ("•\t"),
    versaler normala, texten personlig ("Vi söker en leverantör…").
  - `[en]`-blocket behålls (engelska), `::kommentar::` behålls.
- **Kombinera med §38.2:** SPF/DKIM/DMARC + avsändaradress på egen
  domän är det som väger tyngst – mallen är bara en del av bilden.
- Mallformatet är samma som förut (ÄMNE: första raden, ::placeholders::,
  [en]-block) – fungerar med script/templates.py v3.6 utan ändringar.

### 38.4 WORKSPACE-STATUS V5.0 (viktig notis)
- **script/contacts_ui.py + script/recipients.py SAKNAS i workspace-
  snapshoten** (finns på användarens dator i D:\Program\Email\script\).
  De återskapades INTE – att kopiera stubbversioner över riktiga filer
  skulle vara en regression. Användarens lokala filer är oförändrade.
- script/templates.py återskapades (v3.6, trogen spec §9) – krävs av
  core/email_sender.py (modulimport) och möjliggör testning.
- Mallar/ skapades med de två mallfilerna.
- Testmiljö: PyQt6-stubb i tests_email/pystub + isolerad XDG_CONFIG_HOME
  (gamla inställningar i ~/.config/EmailApp påverkar inte tester).

---

## 39. IKON-SYSTEM – EN IKON, ALLA YTOR (v5.1 IKONRUNDA)

Användaren bad om: "gör en mer passande ikon, som används överallt."

### Design
- **icons/app_icon.png** (512x512 RGBA, rundade hörn): modern kuvert-
  ikon med pappersplan på blå→lila gradient (matchar appens färger)
- **icons/app_icon.ico**: Windows-ikon med 7 storlekar (16–256 px) –
  för genväg/taskbar om så önskas

### Var ikonen används (överallt)
| Yta | Mekanism |
|---|---|
| Huvudfönster + taskbar | QApplication.setWindowIcon (main.pyw steg 9.5) |
| Alla dialoger (sändbekräftelse, inställningar, meddelanden) | ärver automatiskt app-ikonen |
| Kritiska startup-dialoger | _safe_show_critical sätter ikonen på temp-app |
| Systemfältet (tray) | idle = app-ikonen; sending/error/success = app-ikonen + status-badge (…/!/✓) nere till höger (tray v4.5) |

### core/app_icon.py v1.0 (ny)
- `get_app_icon()` – laddad EN gång, cachad; prioritet PNG → ICO →
  programmatiskt ritad kuvertikon (QPainter) – appen får ALLTID en ikon
- `set_app_icon(app)` – sätter QApplication.setWindowIcon
- `icon_path()` / `icon_ico_path()` / `project_root()` / `clear_icon_cache()`
- Tester: sökvägar, cache, set_app_icon, fallback utan fil, tray-lägen

### REGLER
- Ikonsökväg: `<projektrot>/icons/app_icon.png` – ersätt filen för att
  byta ikon (ingen kodändring krävs)
- Koden får ALDRIG krascha om ikonfilen saknas (fallback)
- Ingen ny dependency (QIcon/QPixmap/QPainter finns i PyQt6)

---

## 40. WINDOWS-START – DUBBELKLICK + AUTOSTART UTAN TERMINAL (v5.1)

Användaren bad om: "ska kunna startas via dubbelklick och autostart via
registret, ingen terminal + 5000% bättre."

### Så här startas appen (ingen konsol någonsin)
| Väg | Mekanism |
|---|---|
| Dubbelklick på main.pyw | .pyw → pythonw (Windows-association) |
| Dubbelklick på Starta EmailApp.vbs | Fallkedja: pyw.exe → pythonw.exe → association (fungerar även om .pyw-association saknas) |
| Autostart vid inloggning | Inställningar → "Starta med systemet" → HKCU\Software\Microsoft\Windows\CurrentVersion\Run (värdet skrivs med pythonw.exe) |
| Startad med python.exe (konsol) | main.pyw `_ensure_pythonw()` startar OM med pythonw – loop-skydd EMAILAPP_USE_PYTHONW=1 |

### main.pyw v4.8 – _ensure_pythonw() (steg 0.5, allra först)
- Windows + python.exe + ingen EMAILAPP_USE_PYTHONW → hitta pythonw
  (bredvid exe → sys.base_prefix → PATH) → Popen omstart → exit
- Hoppar över: icke-Windows, redan pythonw, frozen, pythonw saknas
- Går omstarten fel → appen körs vidare ändå (med konsol som sista utväg)

### core/settings_manager.py v24.6
- `_find_pythonw()`: pythonw bredvid sys.executable → sys.base_prefix →
  PATH (shutil.which) – returnerar None om ingen finns
- `_script_path()`: sys.argv[0] om giltig .pyw/.py som finns, annars
  <projektrot>/main.pyw (förra versionen kunde peka fel vid relativ start)
- `_get_autostart_command()` (Windows): `"pythonw.exe" "main.pyw"` –
  registry-autostart öppnar ALDRIG en terminal
- `is_autostart_enabled()` läser HKCU\...\Run-värdet; `sync_autostart()`
  anropas vid start (main.pyw steg 12)

### Starta EmailApp.vbs (ny)
- Dubbelklick utan terminal; hittar main.pyw bredvid sig själv
- Fallkedja: pyw.exe -3 → pythonw.exe → standardassociation
- Felmeddelande (MsgBox) om main.pyw saknas eller start misslyckas

### Verifierat
- _find_pythonw (3 fall) · _get_autostart_command (citerat, fallback) ·
  _script_path (argv0 + fallback) · _ensure_pythonw (omstart, loop-skydd,
  pythonw-redan-aktiv) · VBS-innehåll · regression på allt övrigt

---

## 41. SPRÅKGRUPPERADE MOTTAGARE – SV/EN PER MOTTAGARE (v5.2)

Användaren bad om: "man ska kunna gruppera mottagare via sv/en – dom som
enbart har SV ska endast skickas svenskt mail till och dom som är markerat
EN ska enbart få eng verision av mailet även om en är ikryssad."

### Regler (exakt beteende)
1. **Märkning**: varje mottagare i To/Bcc-listan har ett språk – visas
   som "namn@example.se [SV]" eller "[EN]".
2. **SV-mottagare får ENBART svensk version.**
3. **EN-mottagare får ENBART engelsk version.**
4. **ENGELSKA SKICKAS ALLTID automatiskt till EN-mottagare** – i To
   ELLER Bcc (v5.4). "Inkludera engelsk version"-knappen är BORTTAGEN
   (steg 1 + inställningsfliken); include_english härleds i
   _gather_send_params från mottagarnas språk.
5. Bara SV-mottagare → ingen engelsk version skapas (snabbare).
6. Saknad språktagg/annat värde → SV (standard).

### UI (main_window v5.2, steg ③ Mottagare)
- Dropdown "🌐 Språk för nya mottagare": 🇸🇪 Svenska (SV) / 🇬🇧 Engelska (EN)
  – gäller alla NYA mottagare
- Högerklick på markerade mottagare → "🇸🇪 Sätt svenska / 🇬🇧 Sätt engelska"
- Dubbelklick på en mottagare växlar språk SV↔EN
- Skicka-sammanfattningen visar "🌐 SV n · EN n"
- Historiken sparar to_lang/bcc_lang och återställer dem vid
  "Öppna för redigering / Skicka om"

### Kärna (email_sender v3.9)
- Parametrar: recipients_to_lang / recipients_bcc_lang
  ({e-post: "sv"/"en"}, case-insensitivt; saknad nyckel → sv)
- Mottagarna delas i SV-/EN-grupper EFTER merge (own_email/arkivkopia → sv)
- Mallen parsas per språk – ENDAST språk som används (ingen dubbelparsning)
- Placeholder-översättning sker endast för EN-gruppen
- Batchar: to_sv / to_en / bcc_sv / bcc_en (Bcc-batchning per språk)
  med etiketter "TO · SV" m.fl. i progress/logg
- To-headern i varje batch visar rätt språkgrupps synliga mottagare
- SendResult: recipients_sv, recipients_en, had_language_split
  + summary-rad "🌐 Språk: SV n · EN n"
- Utan lang-dicts: exakt samma flöde som tidigare (bakåtkompatibelt)
- Fix: endast EN-mottagare → en enda engelsk batch (KeyError-'sv'-fix)

### Bekräftelse (dialogs v4.8)
- SendConfirmDialog visar "🌐 Språk: 🇸🇪 SV n · 🇬🇧 EN n"
- Varning: "Engelska är av – EN-markerade mottagare får svensk version"

### Verifierat
- email_sender 6/6: blandat SV+EN (3 batchar), engelska-av → alla SV,
  bakåtkompatibilitet, dry-run+summary, bara-EN (KeyError-fix),
  Bcc-batchning per språk (4 batchar)
- End-to-end: SendWorker → send_email skickar svensk till SV och
  engelsk till EN
- Språktaggar (_lang_tag/_strip_lang_tag), ContactStore v4.3 (CRUD+CSV),
  SendConfirmDialog-läsning av språkdicts

---

## 42. KONTAKTER MED SPRÅK – SV/EN PER KONTAKT (v5.3)

Användaren bad om: "kunna redigera kontakter om de ska ha svenska eller engelska."

### Beteende
1. **Redigera kontakt** (kontaktfliken → ✏️ eller dubbelklick) → ny
   dropdown **"🌐 Språk (mail-språk för denna kontakt)"**: 🇸🇪 Svenska (SV)
   / 🇬🇧 Engelska (EN). Förifylld vid redigering.
2. **Kontaktfliken** visar kolumnen **"🌐 Språk"** (🇸🇪 SV / 🇬🇧 EN) +
   sorteringslägen "Språk (A-Ö)" / "Språk (Ö-A)".
3. **När kontakten läggs till i To/Bcc** (via adressboken, kontaktfliken
   eller fallback-adressboken) märks mottagaren automatiskt med
   kontaktens språk: "namn@example.se [SV]" / "[EN]" – därefter gäller
   språkgrupperingen från §41 (SV får svensk version, EN får engelsk).
4. Handinmatade mottagare får språk från dropdownen "Språk för nya
   mottagare" (som förut). Högerklick/dubbelklick på mottagare kan
   fortfarande ändra språk per sändning.
5. Kontakter utan språk = SV (default). Befintliga contacts.json-filer
   fungerar oförändrat (language skrivs bara när avvikande).

### Filer
- `script/contacts_ui.py` v4.4 – Contact.language, dialog-dropdown,
  språkkolumn + sortering, CSV med language
- `ui/main_window.py` v5.3 – _contact_lang() + inkoppling på 5 ställen
  (adressbokscallback, kontaktflik-callback, fallback-adressbok,
  kompatibilitetsväg)

### Verifierat
- Contact-normalisering (EN→en, tom→sv), to_dict/from_dict-roundtrip
- ContactStore: spara/ladda/uppdatera language, JSON med language enbart
  avvikande, CSV export/import med language
- _ContactEditDialog bygger språkdropdown (ny + redigera)
- _contact_lang: en/sv/utan-store · inkoppling på 5 ställen
- End-to-end: kontakters språk → rätt version per mottagare (dry-run)

---

## 43. SMARTARE KONTAKTSLISTA + BÄTTRE SORTERING (v5.5)

Användaren bad om: "ska vara en smartare kontaktslista, bättre sortering."

### Vad som byggdes (script/contacts_ui.py v4.5)
1. **NATURLIG SORTERING** – siffror sorteras numeriskt i stället för
   bokstavligt: "Kund 2" före "Kund 10", "Vindruta 3" före
   "Vindruta 12". Case-insensitivt. Gäller Namn, E-post, Företag,
   Kategorier.
2. **SVENSK ORDNING** – lower-case-sortering ger korrekt svensk
   alfabetisk ordning: å/ä/ö sist (Åberg efter Zetterlund).
3. **SORTERA MED KOLUMNKLICK** – klicka på rubriken (👤 Namn, 📧 E-post,
   🏢 Företag, 🌐 Språk, 📁 Kategorier) → stigande; klicka igen →
   fallande. Pil-indikator visas i rubriken. Dropdownen "↕ Sortera"
   synkas automatiskt (kartan _HEADER_SORT_MAP).
4. **SPRÅKFILTER** – ny dropdown "🌐 Språk": (Alla) / 🇸🇪 SV / 🇬🇧 EN.
   Kombineras med kategori-filtret och sökningen. Perfekt för att snabbt
   se alla EN-kontakter (som ska få engelsk version).
5. **SMARTARE SPRÅKSORTERING** – "Språk (SV först)" / "Språk (EN först)"
   (ersätter Språk A-Ö/Ö-A). Namnen sorteras alltid stigande inom
   gruppen – inga konstiga omkastningar.
6. **SAMMANFATTNING** – visar nu: antal visade/totalt, "🌐 SV n · EN n",
   filter (kategori/språk) och aktuell sortering.

### Filer
- `script/contacts_ui.py` v4.5 – _natural_key, _on_header_clicked,
  _update_sort_indicator, _lang_filter_cb, _HEADER_SORT_MAP,
  sammanfattning med språkfördelning

### Verifierat
- _natural_key: 2<10, 3<12, case-insensitiv, tom<bokstav
- Svensk ordning: Andersson < Zetterlund < Åberg
- Sorteringslägen: Namn A-Ö/Ö-A, Språk SV först/EN först, E-post –
  alla korrekta (inkl. fix: rank-nyckel så "EN först" inte vänder namn)
- Källkod: header-klick, indikator, språkfilter, smarta lägen inkopplade
- Regression: ContactStore + validering

---

## 44. GRUPPER I ADRESSBOKEN – LÄGG TILL HELA GRUPPER I TO/BCC (v5.6)

Användaren bad om: "man ska kunna sortera mottagare i adressboken, tex
Bilrutor (10 mottagare), Reservdelar, mm. När man lägger till BCC ska man
kunna lägga till en hel adressbok direkt, tex Bilruta (alla mottagare)."

### Funktioner (script/recipients.py v5.5 – AddressBookDialog)
1. **Grupper med antal** – kategorisidopanelen visar
   "👥 Alla kontakter (n)" och varje kategori med antal:
   "Bilrutor (10)", "Reservdelar (4)" osv.
2. **Lägg till HELA gruppen direkt i To/Bcc** – ny gruppåtgärdsrad:
   - "📚 Bilrutor: 10 mottagare" (namn + antal för vald grupp)
   - "➕ Alla (10) → To" / "➕ Alla (10) → Bcc" – ETT klick lägger till
     alla mottagare i gruppen; dialogen stannar öppen
   - Gäller även "Alla kontakter (n)" → hela adressboken på en gång
   - Knapparna avaktiveras om gruppen är tom
3. **Kontextmeny på kategorilistan** (högerklick):
   - "➕ Lägg till alla (n) som To" / "➕ Lägg till alla (n) som Bcc"
   - "↕ Sortera A-Ö" / "↕ Sortera efter antal (flest först)"
4. **Gruppsortering** – self._categories_sort ("alpha"/"count"):
   Bilrutor (10) hamnar före Reservdelar (4) vid "antal".
5. Språk följer med: _emit_add_all → on_add-callback → main_window
   _add_recipient(lang=_contact_lang) → EN-kontakter i gruppen får
   engelsk version automatiskt.

### Bonus (samma beteende i kontaktfliken + fallback)
- **script/contacts_ui.py v4.6**: "➕ Alla visade → To/Bcc" i
  kontaktfliken – lägger till ALLA kontakter som visas (sök + kategori +
  språkfilter gäller) via self._last_visible + _push_all()
- **ui/main_window.py**: fallback-adressboken får "➕ Alla visade → To/Bcc"
  + add_all() (används endast om AddressBookDialog saknas)

### Verifierat
- _category_emails: Bilrutor=2, Reservdelar=1, Alla=4, okänd=0
- _update_group_actions: etikett "📚 Bilrutor: 2 mottagare",
  knapptext "➕ Alla (2) → To/Bcc", avaktivering vid tom grupp
- _emit_add_all('bcc'): hela gruppen → callback; ('to') med Alla: 4 st
- Gruppsortering "antal": Bilrutor först
- Källkod: kontextmeny, _push_all, add_all inkopplade
- Full regression: 21 moduler grön

---


## 45. MUSHJULSSKYDD – MUSHJULET SKROLLAR SIDAN, ÄNDRAR ALDRIG FÄLTVÄRDEN (v5.7)

Användaren bad om: "man ska kunna skrolla med mushjulet utan att några
textfält ändras, endast musscroll över."

### Beteende (ui/wheel_guard.py v1.0 – globalt event-filter)
- **Mushjulet över en QComboBox** → byter INTE val; sidan skrollar
- **Mushjulet över en QSpinBox/QDoubleSpinBox/QDateTimeEdit** → ändrar
  INTE värdet; sidan skrollar
- **Mushjulet över en QSlider/QDial** → ändrar INTE värdet; sidan skrollar
- **Mushjulet över en QLineEdit** → sidan skrollar (tidigare: ingenting)
- **Skrollriktning** följer mushjulet (ner/upp + sidled), 40 px per notch
  (≈ 3 textrader)
- **Undantag:**
  * Öppen QComboBox-lista (popup) skrollas som vanligt
  * QScrollBar skrollar sig själv när musen är över den
  * QTextEdit/QPlainTextEdit/listor/träd skrollar sitt eget innehåll
  * Inget skrollområde i närheten → händelsen konsumeras ändå
    (fältvärdet ändras aldrig)

### Implementation
- `ui/wheel_guard.py` v1.0: _WheelGuard(QObject).eventFilter →
  _handle_wheel → _widget_under_cursor (QApplication.widgetAt) →
  _is_sensitive (klassnamn + isinstance-fallback) → _find_scroll_area
  (max 40 föräldranivåer) → _scroll_area (vertikal/horisontell)
- `install_wheel_guard(app)` idempotent; installeras av main.pyw
  (steg 9.6) + MainWindow (fallback)
- `_WHEEL_STEP_PX = 40`

### Verifierat
- _is_sensitive: combo/spin/slider/dial/lineedit = känsliga,
  scrollbar/text/label/widget = inte
- _find_scroll_area: närmaste QAbstractScrollArea / None
- _scroll_area: ner +40 px, upp -40 px, sidled korrekt
- install idempotent + reset · inkoppling i main.pyw + MainWindow
- Testmiljö: PyQt6-stubb med klass-cache (isinstance fungerar mellan
  moduler) · full regression 22 moduler

---

## 46. GLASTYP FÖRINSTÄLLD PÅ VINDRUTA EFTER RENSNING (v5.8)

Användaren bad om: "när formuläret rensas efter skickat mail så ska ändå
dropdown menyn för glastyp finnas kvar och vara förinställd på vindruta,
men kan välja via dropdown menyn."

### Beteende (ui/main_window.py v5.6 – _reset_form_after_send)
1. Efter lyckad sändning töms ALLA platshållarfält som förut
   (modell/reg/kommentar m.fl. → tomma).
2. **Undantag – dropdown-placeholders (::ruta:: = glastyp):** sätts
   tillbaka till FÖRSTA alternativet i PLACEHOLDER_DROPDOWNS:
   **"Vindruta"**. Dropdownen finns kvar med alla 13 glastyperna och
   användaren kan alltid välja fritt i menyn.
3. Värdet sparas i `settings.replacements_values` = {"ruta": "Vindruta"}
   → vid mallbyte förinställs glastypen på Vindruta automatiskt.
4. Övriga regler för rensningen är oförändrade (ordning v4.9,
   clear_form_after_send, mallval + malltext behålls).

### Filer
- `ui/main_window.py` v5.6 – förinställning av dropdowns i
  _reset_form_after_send (options[0] för nycklar i PLACEHOLDER_DROPDOWNS)

### Verifierat
- PLACEHOLDER_DROPDOWNS["ruta"][0] == "Vindruta"
- _reset_form_after_send: ruta töms → förinställs "Vindruta";
  modell/reg/kommentar töms som förut (clear)
- settings.replacements_values == {"ruta": "Vindruta"}
- Användaren kan välja annat värde (t.ex. Bakruta) efter rensning
- Mallbyte förinställer ruta från sparade värden
- Full regression: 22 moduler grön

---

### 36.18 Session v6.0 (dubbelklick + autostart v2)
1. **Forskning:** FILREGISTRERING-spec v1.5 KRAV 94 (stale_console,
   verify-after-write, --background, registry-backup, konflikter) –
   återanvänt som riktade tillägg i EmailApp, ingen omskrivning.
2. **core/settings_manager.py** v24.6 → **v24.7**: classify_autostart,
   get_autostart_info, sync_autostart reparerar stale_console,
   verify-after-write, backup, VBS-kommando, utökad pythonw-sök,
   `--background`.
3. **main.pyw** v4.9 → **v5.0**: CREATE_NO_WINDOW, argv-vidarebefordran,
   `--background`/`--minimized`, APP_VERSION 5.2.0.
4. **Starta EmailApp.vbs** v5.1 → **v5.2**: djup pythonw-sök, cwd,
   argument-forwarding.
5. **spec.md** → v6.0 (§11, §23, §40 v6.0-tillägg). Räknare Omgång 5:
   4/10 (settings_manager.py + main.pyw + VIN-runda; VBS räknas ej som .py).

### 36.19 Session v6.1 (kommande val – ingen kod)
1. Användaren arkiverade gamla chatten, bad om förslag (Omgång 7).
2. Valda som **KOMMANDE** (ingen implementation i denna leverans):
   To+Bcc-dubblettvarning · historik öppna mail · bild-thumbnails vid
   bifogning · bättre autostart · saknade tillägg vid dubbelklick →
   fråga om installera.
3. Sparat i §34 (kommande-lista), §35 Omgång 7, §47 (full text).
4. Spec-ändring – räknar **EJ** i 10-koduppdateringarna (kvar 4/10).

---

## 47. KOMMANDE KRAV – VALDA 2026-09-16 (INGEN KOD ÄN)

Användaren: "lägg till som kommande". STATUS: **KOMMANDE** –
implementeras när användaren ber om kod (inklistrad fil eller
uttrycklig order). Tills dess inte blockerande. Ingen omskrivning
av hela filer när det väl byggs – minimala riktade diffar + 100 % test.

### 47.1 To+Bcc-dubblettvarning (Omgång 7 #4)
Samma e-postadress i **både To och Bcc** ska synas tydligt före sändning:
- Röd rad i `SendConfirmDialog` (t.ex. "⚠️ Dubblett To+Bcc: a@b.se")
- Jämförelse case-insensitiv, trim
- Skicka tillåts fortfarande (varning, inte block) om inte användaren
  senare ber om hård spärr
- **Filer när det byggs:** `ui/dialogs.py` (SendConfirmDialog), ev.
  `ui/main_window.py` (`_gather_send_params`)

### 47.2 Historik: öppna tidigare skickade mail
Användaren ska kunna **öppna** mail från historiken.
- **Redan i koden (v4.8/v4.9):** dubbelklick / högerklick
  "✏️ Öppna för redigering / Skicka om" fyller formuläret
  (mall, ämne, brödtext, platshållare, To/Bcc, fritext, bilagor, språk)
- **KOMMANDE förstärkning:** göra öppna-åtgärden tydligare (egen knapp
  i historiken, öppna även bilagor/thumbnails, ev. spara/öppna som .eml)
- Ingen funktion får tas bort
- **Filer när det byggs:** `ui/main_window.py` (historik-flik)
- **IMPLEMENTERAD 2026-10-19 (tydligare öppna, main_window v5.8):**
  egen knapp "✏️ Öppna / skicka om" (aktiveras vid radval), hint-text,
  tabell-tooltip, dubbelklick via bunden metod `_on_history_double_clicked`.
  Högerklick-menyn och `_open_history_for_edit` oförändrade i beteende.
  Valfritt kvar: .eml-export / thumbnail i historiken.

### 47.3 Små thumbnails av bild vid bifogning
I steg ② Bilagor/Bilder: miniatyr för bildfiler (png/jpg/jpeg/gif/bmp/webp/tif)
bredvid filnamnet – inte bara 🖼️-text.
- Klick → större förhandsvisning (närbesläktat Omgång 3 #6 / Omgång 7 #9)
- Icke-bilder behåller fil-ikon
- Fail-safe om QImage inte kan läsa filen → vanlig ikon
- **Filer när det byggs:** `ui/main_window.py` (AttachmentDropListWidget /
  bilagelista), ev. `ui/styles.py`

### 47.4 Bättre autostart (vidare efter v6.0)
v6.0/v24.7 finns: stale_console-reparation, verify-after-write, VBS,
`--background`. **KOMMANDE** = ytterligare polish om det fortfarande
blinkar/missar på användarens Windows:
- Skrivbordsgenväg / Start-meny-länk till `Starta EmailApp.vbs` (Omgång 7 #8)
- Tydligare status i Inställningar (klassificering: correct/stale_console/…)
- Reparera även `py.exe`-starter och fel working directory
- **Filer när det byggs:** `core/settings_manager.py`, `main.pyw`,
  `Starta EmailApp.vbs`, ev. Inställningar-UI

### 47.5 Dubbelklick-start: saknat tillägg → fråga om installera
Om appen startas via dubbelklick (VBS / main.pyw) och ett **Python-tillägg
saknas** (PyQt6, python-docx, darkdetect, email-validator, deep-translator,
Pillow …):
- Visa dialog: "Tillägget X saknas. Vill du installera det nu?"
- Ja → `python -m pip install <paket==pinad version>` (från requirements
  när den finns), visa resultat, starta om med pythonw
- Nej → fortsätt om det går, annars tydligt fel (inte tyst krasch)
- Aldrig tyst pip utan fråga. Aldrig admin-krav som default (användarens
  Python / --user)
- **Filer när det byggs:** `main.pyw` (tidig dep-check före QApplication
  om möjligt; Qt-dialog när Qt finns, annars MessageBox/VBS), ev. ny
  `core/dep_check.py`

---

### 36.20 Session v6.2 (VIN EN-only)
1. **ui/main_window.py** v5.6 → **v5.7**: VIN-fält syns bara vid EN-mottagare.
2. **core/email_sender.py** v3.9 → **v3.10**: VIN bara i EN-version.
3. Mall: VIN-rad endast i [en]. Tester 12/12. Räknare 4/10.


## 48. VIN ENDAST I ENGELSKT MAIL (v6.2)

Användaren: fält för VIN som bara syns för [en] och bara skickas om det
finns EN-mottagare.

### Regler
1. Platshållare `::vin::` ligger **endast i [en]-blocket** i mallen.
2. UI-fältet **"🔢 VIN (endast engelska)"** visas BARA när minst en
   mottagare i To eller Bcc är märkt [EN].
3. VIN skickas BARA i den engelska versionen. SV-mottagare får aldrig VIN.
4. **VIN är obligatoriskt** så fort det finns minst en [EN]-mottagare –
   skicka stoppas med dialog tills fältet är ifyllt.
5. Utan EN-mottagare: fältet dolt, VIN skickas inte, räknas inte som saknat.
6. Tom VIN i EN-mail (ska inte kunna ske) → VIN-raden utelämnas.
6. VIN översätts inte (registreringsliknande värde).

### Filer
- `ui/main_window.py` v5.7 – EN_ONLY_PLACEHOLDERS, synlighet, gather
- `core/email_sender.py` v3.10 – VIN bort ur SV-replacements, strip tom rad
- `Mallar/Offertförfrågan – ruta och tillbehör.txt` – `VIN: ::vin::` i [en]

---

# MASTER SPEC v6.2 – KOMPLETT RENSRIVNING (INGET BORTTAGET) – SLUT

**NÄSTA STEG: Inväntar kod. Inklistrad kod sparas till workspace och gås igenom.**
**§34 väntar: tangentbordsgenvägar, tema-knapp, loggrensning 10 dagar.**
**§47 KOMMANDE (valda 2026-09-16): To+Bcc-dubblett · historik öppna · bild-thumbnails · bättre autostart · saknade tillägg vid start.**
**§35 omgång 3–4 valfria · Omgång 5: 25 förslag igen efter 10 koduppdateringar (räknare 4/10) · Omgång 6 forskningsförslag · Omgång 7 delvis vald.**
**§35 Omgång 8 (2026-10-19): 10 nya förslag presenterade. GitHub: push efter varje uppdatering, merga aldrig.**

### 36.21 Session v6.3 (2026-10-19 – tema-knapp + historik öppna)
Användaren valde från redan-valda: tema-knapp (§34 #6) och tydligare
öppna i historiken (§47.2). **Ingen merge. Push efter uppdatering.**
1. `ui/main_window.py` v5.7 → **v5.8** (minimal diff): `btn_theme`,
   `_on_theme_button_clicked` / `_update_theme_button`; historik-knapp
   "✏️ Öppna / skicka om", hint, tooltip, `_open_selected_history`.
2. Helpers (testbara utan Qt): `theme_button_caption`,
   `history_selected_row`, `history_open_feedback`.
3. `tests/test_v58_theme_history.py` + py_compile.
4. spec.md: §34 #6 och §47.2 markerade implementerade (ingen text borttagen).
5. Omgång 5-räknare: +1 kodfil denna leverans (main_window.py).
