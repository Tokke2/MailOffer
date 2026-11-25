# AGENTS.md – Permanenta hårda projektregler för E-postofferten (MailOffer)

Denna fil ligger permanent i repots rot så att **varje ny chatt och varje kodagent** omedelbart läser och följer samtliga stående regler i **E-postofferten (`Tokke2/MailOffer`)**.

---

## 1. HÅRD REGEL – Uppdatera ALLTID GitHub Release + markera som `Latest` vid kodförändring
- Appens inbyggda uppdaterare (`core/github_update.py`) hämtar alltid `https://api.github.com/repos/Tokke2/MailOffer/releases/latest` över HTTPS och **jämför både `BUILD_ID` och varenda appfils SHA-256 (`compare_release_files`)** mot den taggade releasens commit/zipball.
- Vid **varje kodförändring**:
  1. Räkna upp `BUILD_ID` i `core/version.py` (behåll `__version__ = "1.0.0"` tills användaren uttryckligen begär ett annat versionsnummer).
  2. Kör enhetstester och verifiera att CI går grönt.
  3. Flytta release-taggen (`v1.0.0`) till den nya commit-SHA:n och uppdatera GitHub-releasen med **`make_latest="true"`**, `draft=false`, `prerelease=false` samt uppdaterad `<!-- build: ... -->`-markering via:
     ```bash
     python tools/sync_latest_release.py --note "- Kort sammanfattning av ändringen"
     ```
  4. GitHub Actions-jobbet `sync-latest-release` i `.github/workflows/tests.yml` kör dessutom `tools/sync_latest_release.py` automatiskt efter varje grön push.

## 2. HÅRD REGEL – ALDRIG merga & arbeta ENDAST mot sessionens enda aktiva branch (aldrig `main`/`master`)
- **Aldrig merga** (`never merge`): kör aldrig `gh pr merge` eller `git merge` mot `main`/`master` eller andra brancher.
- Arbeta, committa, pusha och publicera releaser **endast** mot den aktiva arbetsbranchen (inga extra sidobrancher får skapas eller lämnas kvar).
- Appens uppdaterare och `tools/sync_latest_release.py` blockerar hårt alla referenser till `main` och `master`.

## 3. HÅRD REGEL – Inga tysta beroende- eller gränssnittsbrott & testkrav innan klar
- Ändra **aldrig** publika funktionssignaturer, sparade JSON-/inställningsformat (`email_settings.json`, `contacts.json`, `send_history.json`, utkast/uppdateringssession) eller beroenden i `requirements.txt` i smyg.
- **Testkrav innan klar**: alla Python-filer ska kompilera utan fel (`validate_python_sources` / `python -m compileall`), alla enhetstester ska passera lokalt, och **samtliga GitHub Actions-jobb** (`unittest`, `windows-startup-syntax`, `desktop-portability`, `sync-latest-release`) ska verifieras gröna innan arbetet rapporteras klart.

## 4. HÅRD REGEL – Ingen medföljande `.exe` eller binär körfil
- På Windows startas appen via `Starta EmailApp.vbs` med datorns befintliga system-Python (`pythonw`), utan konsolfönster.
- Inga `.exe`-, `.dll`- eller `.msi`-filer får läggas till i repot eller kopieras vid uppdatering (`_DISALLOWED_BINARY_SUFFIXES` i `core/app_update.py`).

## 5. HÅRD REGEL – Ta bort uppdateringsbackup vid lyckad uppdatering
- En lösenordsfri säkerhetsbackup skapas i `.data/pre_update_backups/pre-update-*.zip` före filkopiering så att installationen alltid kan rullas tillbaka vid fel.
- Så snart installationen **och** efterkontrollen (`compare_release_files`) lyckas helt utan fel ska både `.data/pre_update_backups/` och `.data/update_cache/` tas bort automatiskt (`cleanup_pre_update_backups`).

## 6. HÅRD REGEL – Endast dagens logg synlig & rensa arkiverade loggar efter 7 dagar
- I `logs/` och i fliken *Loggar* ska endast dagens aktiva loggar visas.
- Äldre loggdagar komprimeras och arkiveras verifierat i `logs/archive/YYYY-MM-DD/` och **rensas automatiskt efter 7 dagar** (`RETENTION_DAYS = 7` via `prune_archived_logs`).
- Aktiva ofixade fel sparas i `logs/errors.log` / `unresolved-errors.log` tills de är åtgärdade och rensas därefter automatiskt.

## 7. HÅRD REGEL – Skärmanpassning, maxhöjd vid start, minimera scroll, egen Profil-underflik, ruta-val & HiDPI-skärpa
- **Start i maxhöjd & anpassad bredd**: utan tidigare sparad fönsterstorlek startar huvudfönstret i skärmens fulla tillgängliga höjd (`availableGeometry().height()`) med skärmanpassad bredd för att visa maximalt innehåll och minimera skrollning.
- **Egen underflik för avsändarprofiler**: *Inställningar* har en dedikerad första underflik (*Avsändarprofiler*) för att skapa, färgsätta och konfigurera profiler och signaturer, samt alltid synlig sparaknapprad längst ned.
- **Val av ruta (`::ruta::` / 13 glastyper)**: rullmeny för glastyp ska finnas både i sändflödets Steg 1 och i Mall-wizarden (`ui/template_wizard.py`).
- **Mushjulsskydd (`ui/wheel_guard.py`)**: alla omarkerade textfält och rullmenyer ignoreras vid mushjulsskrollning så att sidan skrollar vidare; först vid aktiv markering/öppen meny skrollar kontrollen.
- **Skarpa vektororiginal & tryckfiler**: logotyp och ikoner ska vara skarpa i `100 %–300 %` DPI (`core/app_icon.py`, `ui/vector_icons.py`). Alla original i `icons/*.svg` och `tryck/*.svg` ska vara rena konturbanor (`<path>`) i namngivna lager utan `<text>`/`<image>` (`tryck/E-postofferten-farg.svg` i 100 % plana färger). Kör `python tools/make_icon.py` och `python tools/build_thunderbird.py` vid grafikändring.
- **Upphovsrätt & donation**: `Skapad av Rickard Längkvist` / `© 2026 Rickard Längkvist` samt låsta donationsmottagare i `core/donate.py` får aldrig ändras.

## 8. HÅRD REGEL – 10-meddelanderegeln (10 helt nya, ej återbrukade förslag var 10:e chattmeddelande)
- Efter **var 10:e chattmeddelande** från användaren ska en ny förslagslista med **10 helt nya förbättringsförslag** visas.
- Inget förslag får återbrukas från tidigare omgångar i `docs/forslagslogg.md`, de 50 punkterna i `docs/25-produktforslag.md` eller `docs/VAD-SAKNAS.md`.
- Varje visad 10-lista ska samtidigt loggas med löpnummer (`#F01`–`#F10`, `#F11`–`#F20`, osv.) i `docs/forslagslogg.md`.
