# CLAUDE.md

Läs och följ **samtliga permanenta hårda regler** i [`AGENTS.md`](./AGENTS.md) samt [`docs/forslagslogg.md`](./docs/forslagslogg.md) innan du ändrar kod eller svarar.

Sammanfattning av stående hårda regler för **E-postofferten (`MailOffer`)**:
0. **Skriv alltid in nya regler på GitHub**: om användaren skriver `- hård regel` eller `regel` ska regeln läggas till i `AGENTS.md`, committas och pushas.
1. **Endast en aktiv branch (`arena/447b9635-mailoffer`) & jobba ALDRIG mot `main`/`master`**, särskilt vid appuppdateringar.
2. **ALDRIG merga (`never merge`)**.
3. **Release alltid uppdaterad + markerad som `Latest` vid varje kodförändring**: räkna upp `BUILD_ID` i `core/version.py` och synka via `python tools/sync_latest_release.py` (appen jämför filer mot `/releases/latest`).
4. **REQ-K4, inga tysta beroende-/gränssnittsbrott & gröna tester/CI krävs innan klar**.
5. **Inget terminalfönster varken vid start eller skanning & starta alltid minimerat**.
6. **Ta bort uppdateringsbackup vid lyckad uppdatering** och **arkivera gårdagens loggar + rensa efter 7 dagar**; håll aktiv `logs/errors.log` där åtgärdade fel tas bort.
7. **Skärmanpassning, maxhöjd vid start, HiDPI-skärpa, egen underflik för profiler, `::ruta::`-val i mall-wizarden samt sorterbara/flyttbara kolumner**.
8. **ALDRIG merga eller skapa PR (`gh pr merge` / `gh pr create`)** – arbetet sker direkt på den aktiva branchen.
9. **EN standardbranch även efter chattbyte** (`arena/447b9635-mailoffer`) – aldrig ny sidobranch per chatt, aldrig `main`.
10. **Autouppdatering kl. 00:00 varje dag**: hittas en ny release installeras den tyst (ingen dialog), backupen tas bort vid lyckad installation och appen startar om tyst; kan stängas av med `auto_midnight_update`.
11. **`::ruta::`-väljaren endast i appar som hade den i `ttk`-versionen** (E-postofferten hade den).
12. **10-meddelanderegeln**: skriv alltid ut 10 helt nya, ej återbrukade förslag direkt i chatten var 10:e chattmeddelande och spara i `docs/forslagslogg.md`.
