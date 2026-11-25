# CLAUDE.md

Läs och följ **samtliga hårda projektregler** i [`AGENTS.md`](./AGENTS.md) samt förslagsloggen i [`docs/forslagslogg.md`](./docs/forslagslogg.md) innan du gör ändringar eller svarar i detta repo.

Kort påminnelse om de viktigaste kraven:
1. **Uppdatera alltid GitHub Release + markera som `Latest` vid varje kodförändring** (`BUILD_ID` i `core/version.py` + `python tools/sync_latest_release.py`, kontrolleras även av GitHub Actions-jobbet `sync-latest-release`). Appen jämför alla filer via GitHub Releases (`/releases/latest`).
2. **Använd aldrig `main`/`master`** och skeppa aldrig `.exe`-binärer.
3. **Ta bort uppdateringsbackup vid lyckad uppdatering** och **rensa arkiverade loggar efter 7 dagar**.
4. **Var 10:e chattmeddelande**: visa **10 helt nya förslag (ej återbrukade)** och logga dem i `docs/forslagslogg.md`.
