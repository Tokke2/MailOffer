# CLAUDE.md

Läs och följ **samtliga permanenta hårda regler** i [`AGENTS.md`](./AGENTS.md) samt [`docs/forslagslogg.md`](./docs/forslagslogg.md) innan du ändrar kod eller svarar.

Sammanfattning av stående hårda regler för **E-postofferten (`MailOffer`)**:
1. **Release alltid uppdaterad + markerad som `Latest` vid varje kodförändring**: räkna upp `BUILD_ID` i `core/version.py` och kör `python tools/sync_latest_release.py` (körs även automatiskt av CI-jobbet `sync-latest-release`). Appens uppdaterare jämför filer mot `/releases/latest`.
2. **ALDRIG merga (`never merge`)** och arbeta **endast** mot den aktiva branchen – aldrig mot `main` eller `master`.
3. **Inga tysta beroende- eller gränssnittsbrott** och **gröna tester/CI krävs innan klar**.
4. **Ingen `.exe`/binär**, **ta bort uppdateringsbackup vid lyckad uppdatering**, och **rensa arkiverade loggar efter 7 dagar**.
5. **10-meddelanderegeln**: var 10:e chattmeddelande ska 10 helt nya, ej återbrukade förslag visas och sparas i `docs/forslagslogg.md`.
