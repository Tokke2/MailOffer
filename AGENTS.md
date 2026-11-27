# AGENTS.md – Permanenta hårda projektregler för E-postofferten (MailOffer)

Denna fil ligger i repots rot som gemensam sanningskälla för alla kodagenter och nya chattsessioner i **E-postofferten (`Tokke2/MailOffer`)**. Reglerna är anpassade specifikt efter E-postoffertens arkitektur och flöden.

---

## 0. HÅRD REGEL – Skriv alltid in nya regler på GitHub vid `- hård regel` eller `regel`
- Varje gång användaren skriver **`- hård regel`** eller **`regel`** i chatten ska den nya regeln **alltid skrivas in i `AGENTS.md`** (och synkas till `CLAUDE.md` samt `.github/copilot-instructions.md`), committas och pushas till den aktiva branchen på GitHub.

## 1. HÅRD REGEL – Endast EN aktiv branch kvar & jobba ALDRIG mot `main`/`master`
- Arbeta, committa, pusha och publicera releaser **endast** mot sessionens enda aktiva arbetsbranch (`arena/447b9635-mailoffer`). Skapa eller lämna aldrig kvar sidobrancher.
- **Jobba aldrig mot `main` eller `master`**, särskilt inte vid appuppdateringar: både `core/github_update.py` och `tools/sync_latest_release.py` ska hårt avvisa referenser till `main` och `master`.

## 2. HÅRD REGEL – ALDRIG merga (`never merge`)
- Kör **aldrig** `git merge` eller `gh pr merge` under några omständigheter.

## 3. HÅRD REGEL – Uppdatera ALLTID GitHub Release + markera som `Latest` vid kodförändring (filjämförelse i appen)
- Appens inbyggda uppdaterare (`core/github_update.py`) hämtar `https://api.github.com/repos/Tokke2/MailOffer/releases/latest` över HTTPS och **jämför både `BUILD_ID` och varje appfils SHA-256 (`compare_release_files`)** mot installerade filer på disken.
- Vid **varje kodförändring**:
  1. Räkna upp `BUILD_ID` i `core/version.py` (behåll `__version__ = "1.0.0"` tills användaren uttryckligen begär ändrat versionsnummer).
  2. Verifiera att samtliga tester och CI-jobb är gröna.
  3. Flytta release-taggen (`v1.0.0`) till den nya commit-SHA:n och publicera releasen med **`make_latest="true"`**, `draft=false`, `prerelease=false` via:
     ```bash
     python tools/sync_latest_release.py --note "- Kort sammanfattning av ändringen"
     ```
  4. GitHub Actions-jobbet `sync-latest-release` i `.github/workflows/tests.yml` kör dessutom synkningen automatiskt efter varje grön push.

## 4. HÅRD REGEL – REQ-K4, inga tysta beroende-/gränssnittsbrott & testkrav innan klar
- **REQ-K4 (kompatibilitets-, dataskydds- och kvalitetskontrakt anpassat för E-postofferten)**:
  - Användardata (`Mallar/`, `email_settings.json`, `contacts.json`, `.data/sent_history.json`, utkast och signaturbilder) får **aldrig** skrivas över eller raderas vid uppdatering eller kodändring.
  - **Inga tysta beroende- eller gränssnittsbrott**: ändra aldrig publika funktionssignaturer, sparade JSON-format eller paket i `requirements.txt` utan explicit bakåtkompatibilitet.
  - **Testkrav innan klar**: alla Python-källfiler ska kompilera (`validate_python_sources`), samtliga enhetstester ska passera lokalt och samtliga GitHub Actions-jobb (`unittest`, `windows-startup-syntax`, `desktop-portability`, `sync-latest-release`) ska vara verifierat gröna innan uppgiften rapporteras klar.

## 5. HÅRD REGEL – Inget terminalfönster (varken vid start eller skanning) & starta alltid minimerat
- På Windows startas appen via `Starta EmailApp.vbs` med datorns befintliga system-Python (`pythonw.exe`) utan konsolfönster (`shell.Run(..., 0, True)`), och **inga medföljande `.exe`/`.dll`/`.msi`-binärer** får finnas.
- Samtliga underprocesser vid paketkontroll, sändnings-/DNS-kontroll och Thunderbird-skanning ska köras med `CREATE_NO_WINDOW` / `SW_HIDE` (`core/process_utils.py:quiet_process_options`) så att **inget terminalfönster blinkar till** varken vid start eller skanning.
- Appen **startar alltid minimerat** (`main.pyw`: dold till systemfältet när brickan finns, annars `showMinimized()` i aktivitetsfältet).

## 6. HÅRD REGEL – Ta bort uppdateringsbackup vid lyckad uppdatering
- Före filkopiering skapas en lösenordsfri rollback-backup i `.data/pre_update_backups/pre-update-*.zip`.
- När uppdateringen **och** efterkontrollen (`compare_release_files`) lyckas helt utan fel raderas `.data/pre_update_backups/` och `.data/update_cache/` automatiskt (`cleanup_pre_update_backups`).

## 7. HÅRD REGEL – Dagsarkivering, 7-dagars loggrensning + app-logg & aktiv fellogg där åtgärdade fel tas bort
- **App-logg**: i `logs/` och vyn *Dagens logg* visas endast dagens aktiva loggposter. Gårdagens och äldre loggar komprimeras och arkiveras verifierat i `logs/archive/YYYY-MM-DD/` och **raderas automatiskt efter 7 dagar** (`RETENTION_DAYS = 7` via `prune_archived_logs`).
- **Komplett aktiv fellogg (`logs/errors.log`)**: samlar alla aktiva, ej åtgärdade fel. När ett fel blir åtgärdat (automatiskt verifierat eller markerat via `✅ Rensa åtgärdade fel` / `resolve_issues`) **tas det bort från den aktiva felloggen `logs/errors.log`**.

## 8. HÅRD REGEL – Skärmanpassning, HiDPI-skärpa, minnes-/energisnål drift, profil-underflik, ruta-val & sorterbara/flyttbara kolumner
- **Start i maxhöjd & anpassad bredd, minimera scroll**: utan tidigare sparad fönstergeometri startar fönstret i skärmens fulla tillgängliga höjd (`availableGeometry().height()`) med skärmanpassad bredd och kompakta marginaler.
- **Knivskarp HiDPI (`100 %–300 %`)**: `PassThrough`-skalning utan mellanskalningsoskärpa, skarp typsnitts-hinting, vektorikoner i fysiska enhetspixlar (`1.0x–3.0x` DPR i `ui/vector_icons.py`) och omritning av logotyp vid byte mellan skärmar med olika DPI (`_refresh_dpi_assets`).
- **Skarp vektorlogotyp överallt + redigerbara tryckoriginal**: används konsekvent på fönster, taskbar, bricka och dialoger (`core/app_icon.py`); rena konturkonverterade lager i `icons/*.svg` och `tryck/*.svg` (`tryck/E-postofferten-farg.svg` i 100 % plana färger).
- **Egen underflik för profiler (endast i appar som använder profiler)**: eftersom E-postofferten använder avsändarprofiler är *Inställningar → Avsändarprofiler* en egen dedikerad underflik med fast knapprad längst ned.
- **Val av ruta (`::ruta::` – 13 glastyper)**: finns både i sändflödets Steg 1 och i Mall-wizarden (`ui/template_wizard.py` Steg 2 & Steg 4).
- **Sortera och flytta kolumner**: alla flerkolumnstabeller och trädvyer (*Skicka-historik*, *Kontakter/Adressbok*, kontaktväljare) har klickbar kolumnsortering (`setSortingEnabled` / `sectionClicked`) och flyttbara kolumner med dra-och-släpp (`setSectionsMovable(True)`).
- **Minnes- och energisnål drift**: grova bakgrundstimers (`VeryCoarseTimer`), nedsaktad bakgrundspollning när fönstret är dolt/minimerat (`ui/idle_polling.py`) och begränsade LRU-ikoncachar med automatisk bakgrundstrimning.
- **Upphovsrätt & donation**: `Skapad av Rickard Längkvist` / `© 2026 Rickard Längkvist` samt låsta donationsmottagare i `core/donate.py` får aldrig ändras.

## 9. HÅRD REGEL – ALDRIG merga eller skapa Pull Request (`PR`)
- Kör **aldrig** `git merge`, `gh pr merge`, squash/rebase-merge eller `gh pr create`. Arbetet sker direkt på den aktiva branchen och publiceras via release-synken (`tools/sync_latest_release.py`) – **inga PR:er, ingen merge**.

## 10. HÅRD REGEL – EN standardbranch som gäller även efter chattbyte
- Repot ska ha **endast en aktiv/standardbranch** (`arena/447b9635-mailoffer`). Vid ny chatt eller ny session ska arbetet **återupptas på exakt denna branch** – aldrig skapa en ny sidobranch per chatt och aldrig arbeta mot `main`.
- Om `main` finns kvar som skyddad standardbranch i GitHub-inställningarna (Arena-token saknar admin-scope) får den **aldrig användas för kod, uppdateringar eller release**; all release- och uppdateringslogik pekar på den aktiva branchen.

## 11. HÅRD REGEL – Autouppdatering kl. 00:00 varje dag om uppdatering finns
- Appen kör en daglig **00:00-autouppdatering**: första kontrollen efter midnatt (`should_midnight_auto_update` i `core/github_update.py`, sparat datum i `last_midnight_auto_update_date`) söker efter ny release och **installerar den automatiskt och tyst** – ingen nedladdningsdialog, inga modala varningsrutor.
- Vid lyckad installation: `cleanup_pre_update_backups` tar bort backupen, arbetsläget sparas i `update-session.json` och appen startar om tyst (minimerat). Misslyckas nattuppdateringen loggas felet **utan dialog** och appen fortsätter oförändrad.
- Kan stängas av i *Inställningar → 🔄 Uppdateringar* (`auto_midnight_update`, standard **på**); övriga tider gäller fortsatt 12-timmarsregeln som bara **anmäler** en uppdatering.

## 12. HÅRD REGEL – `::ruta::`-val endast i appar som hade det i `ttk`-versionen
- `::ruta::`-väljaren (13 glastyper) ska finnas i **alla appar som hade `::ruta::` i sin `ttk`-version** – E-postofferten hade det, så väljaren ska finnas både i sändflödets Steg 1 och i Mall-wizarden. Appar som aldrig haft `::ruta::` ska **inte** få väljaren påtvingad.

## 13. HÅRD REGEL – Förslagslistor skrivs ALLTID ut i chatten (10 nya var 10:e meddelande + 25 unika konkurrentförslag)
- Efter **var 10:e chattmeddelande** ska en ny lista på **10 helt nya förbättringsförslag** (aldrig återbrukade från tidigare omgångar i `docs/forslagslogg.md`, `docs/25-produktforslag.md` eller `docs/VAD-SAKNAS.md`) **alltid skrivas ut direkt i chatten** och loggas i `docs/forslagslogg.md`.
- Likaså ska begärda 25-listor med nya funktioner som konkurrenter saknar och användare efterfrågar **alltid skrivas ut i chatten** och bokföras så att de aldrig återbrukas senare.
