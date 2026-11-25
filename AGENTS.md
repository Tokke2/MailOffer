# AGENTS.md – Permanenta projektregler för E-postofferten (MailOffer)

Denna fil ligger permanent i repot så att **varje ny chatt och varje kodagent** alltid känner till och följer samtliga hårda regler i projektet.

---

## 1. HÅRD REGEL – GitHub Release + `Latest` ska ALLTID uppdateras vid kodförändring
- Appens inbyggda uppdaterare (`core/github_update.py`) hämtar alltid `https://api.github.com/repos/Tokke2/MailOffer/releases/latest` över HTTPS och **jämför både `BUILD_ID` och varenda appfils SHA-256** (`compare_release_files`) mot den taggade releasens commit/zipball.
- Vid **varje kodförändring**:
  1. Räkna upp `BUILD_ID` i `core/version.py` (behåll `__version__ = "1.0.0"` tills användaren uttryckligen begär ett annat SemVer-nummer).
  2. Kör alla tester och verifiera att CI passerar grönt.
  3. Uppdatera release-taggen (`v1.0.0`) till den nya commit-SHA:n och uppdatera GitHub-releasen med **`make_latest="true"`**, `draft=false`, `prerelease=false` och uppdaterad `<!-- build: ... -->`-kommentar genom att köra:
     ```bash
     python tools/sync_latest_release.py --note "- Kort sammanfattning av ändringen"
     ```
  4. GitHub Actions-jobbet `sync-latest-release` i `.github/workflows/tests.yml` kör dessutom `tools/sync_latest_release.py` automatiskt efter varje grön push som extra garanti.

## 2. HÅRD REGEL – Aldrig `main`/`master` & endast sessionens aktiva branch
- Uppdateringar får **aldrig** hämtas från eller peka mot `main` eller `master` (`core/github_update.py` och `tools/sync_latest_release.py` blockerar detta aktivt).
- Arbeta, committa och pusha alltid uteslutande på sessionens aktiva arbetsbranch. Skapa aldrig sidobrancher.

## 3. HÅRD REGEL – Ingen medföljande `.exe` eller binär körfil
- Start på Windows sker via `Starta EmailApp.vbs` med datorns befintliga system-Python (`pythonw`), utan konsolfönster.
- Inga `.exe`-, `.dll`- eller `.msi`-filer får skeppas i repot eller kopieras vid uppdatering (`_DISALLOWED_BINARY_SUFFIXES` i `core/app_update.py`).

## 4. HÅRD REGEL – Ta bort uppdateringsbackup när uppdateringen lyckats
- Före en uppdatering skapas en lösenordsfri förhandsbackup i `.data/pre_update_backups/pre-update-*.zip` så att återställning är säkrad om installationen avbryts eller misslyckas.
- När uppdateringen **och** efterkontrollen (`compare_release_files`) lyckas helt utan fel ska både `.data/pre_update_backups/` och `.data/update_cache/` tas bort automatiskt (`cleanup_pre_update_backups`).

## 5. HÅRD REGEL – Endast dagens logg synlig & rensa arkiverade loggar efter 7 dagar
- I `logs/` och i fliken *Loggar* ska endast dagens loggar visas som aktiva dagsloggar.
- Avslutade dagar arkiveras verifierat i `logs/archive/YYYY-MM-DD/` och **rensas automatiskt efter 7 dagar** (`RETENTION_DAYS = 7` via `prune_archived_logs`).
- Samlad felsökningslogg (`logs/errors.log` + `unresolved-errors.log`) behåller aktiva ofixade fel tills de åtgärdats och rensas automatiskt när felet är fixat.

## 6. HÅRD REGEL – Mushjulsskydd & skärmanpassning
- Alla omarkerade textfält och rullmenyer ska ignoreras vid mushjulsskrollning (`ui/wheel_guard.py`) så att sidans rullningsyta skrollar obehindrat; först när ett fält/en rullmeny är aktivt markerad skrollar kontrollen.
- Alla fönster, tabeller och ikoner ska fungera skarpt vid `100 %–300 %` DPI (`ui/screen_fit.py`, `ui/vector_icons.py`, `core/app_icon.py`) samt i dolt/minimerat systemfältsläge (`SW_HIDE` / "Visa fönster").
- För engelska mottagare (`[EN]`) ska kryssrutan **"Har ej VIN"** fungera och bevaras i utkast/session.

## 7. HÅRD REGEL – Skarp vektorlogotyp, redigerbara tryckoriginal & låst donation/upphovsrätt
- Alla logotyp- och tryckoriginal i `icons/*.svg` och `tryck/*.svg` ska bestå av rena konturbanor (`<path>`) i namngivna lager utan `<text>`, `<image>` eller externa typsnitt (`tryck/E-postofferten-farg.svg` ska vara 100 % plana färger utan gradienter/transparens/strokes/transforms).
- Efter ändring i SVG eller Thunderbird-filer ska `python tools/make_icon.py` och `python tools/build_thunderbird.py` köras så att PNG/ICO/ICNS och `MailOffer.xpi` hålls synkade.
- Upphovsrätt (`Skapad av Rickard Längkvist`, `© 2026 Rickard Längkvist`) och fasta donationsmottagare i `core/donate.py` är låsta och får aldrig ändras eller kringgås.

## 8. HÅRD REGEL – 10 nya ej återbrukade förslag var 10:e chattmeddelande
- Efter **var 10:e chattmeddelande** från användaren ska agenten presentera en ny lista med **10 helt nya förbättringsförslag** för E-postofferten.
- Inget förslag får återbrukas från tidigare omgångar i `docs/forslagslogg.md`, de 50 punkterna i `docs/25-produktforslag.md` eller punkterna i `docs/VAD-SAKNAS.md`.
- Varje ny 10-lista som visas ska samtidigt registreras med löpnummer (`#F11`–`#F20`, `#F21`–`#F30`, osv.) i `docs/forslagslogg.md`.
