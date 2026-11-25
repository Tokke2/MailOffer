Läs och följ alla permanenta hårda regler i `AGENTS.md` och `docs/forslagslogg.md`.
- Om användaren skriver `- hård regel` eller `regel`: skriv alltid in regeln i `AGENTS.md` och pusha till GitHub.
- Endast EN aktiv branch (`arena/447b9635-mailoffer`), jobba ALDRIG mot `main`/`master` och ALDRIG merga.
- Uppdatera ALLTID `BUILD_ID` i `core/version.py` + GitHub Release (`v1.0.0`, `make_latest="true"` via `tools/sync_latest_release.py`) vid varje kodförändring (appen jämför filer via `/releases/latest`).
- REQ-K4: inga tysta beroende- eller gränssnittsbrott, rör aldrig användardata, och alla tester + CI ska vara gröna innan klar.
- Inget terminalfönster varken vid start eller skanning (`CREATE_NO_WINDOW`) och starta alltid minimerat.
- Ta bort uppdateringsbackup vid lyckad uppdatering; arkivera gårdagens loggar och radera arkiv efter 7 dagar; ta bort åtgärdade fel ur aktiv `logs/errors.log`.
- Var 10:e chattmeddelande: skriv alltid ut 10 helt nya, ej återbrukade förslag direkt i chatten och logga dem i `docs/forslagslogg.md`.
