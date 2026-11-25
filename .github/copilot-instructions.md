Läs och följ alla permanenta hårda regler i `AGENTS.md` och `docs/forslagslogg.md`.
1. Uppdatera ALLTID `BUILD_ID` i `core/version.py` + GitHub Release (`v1.0.0`, `make_latest="true"` via `tools/sync_latest_release.py`) vid varje kodförändring (appen jämför filer via `/releases/latest`).
2. ALDRIG merga och arbeta ALDRIG mot `main`/`master` – arbeta endast mot den aktiva arbetsbranchen.
3. Inga tysta beroende- eller gränssnittsbrott; samtliga tester och GitHub Actions-jobb ska vara gröna innan klar.
4. Ta bort uppdateringsbackup vid lyckad uppdatering och rensa arkiverade loggar efter 7 dagar.
5. Var 10:e chattmeddelande: presentera 10 helt nya, ej återbrukade förslag och logga dem i `docs/forslagslogg.md`.
