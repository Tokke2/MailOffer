# Status & kvarvarande förbättringspunkter – E-postofferten 1.0.0

Detta dokument ersätter den äldre förhandsanalysen från den interna `5.4`-tiden och speglar aktuellt läge i **E-postofferten `1.0.0`**.

## ✅ Redan levererat i 1.0.0 (stängda punkter)
- **GitHub Releases med fil- och SHA-256-jämförelse (`core/github_update.py`)**: aktiv `v1.0.0`-release markerad som `Latest`, atomär transaktionsinstallation med rollback, automatisk borttagning av förhandsbackup vid lyckad uppdatering samt CI-synk (`tools/sync_latest_release.py`).
- **Start utan egen binär (`Starta EmailApp.vbs`)**: använder datorns befintliga system-Python (`pythonw`) utan konsolfönster och med veckovis paketkontroll – inga `.exe`-byggen används.
- **Avsändarprofiler i egen underflik**: stöd för flera konton, profilfärger, signatur med logotyp och förhandsvisning i *Inställningar → Avsändarprofiler*.
- **Mall-wizard med versionshistorik, mallpaket & val av ruta (`::ruta::`)**: 5-stegswizard med både SV/EN, versionsåterställning, färdiga mallpaket och rullmeny för alla 13 glastyper.
- **Daglig loggrotation & 7-dagars arkivrensning**: endast dagens logg visas aktivt i `logs/`, äldre dagar i `logs/archive/` rensas efter 7 dagar och åtgärdade fel rensas automatiskt ur `errors.log`.
- **Skärmanpassning, HiDPI-vektorikoner, skarp vektorlogotyp & redigerbara tryckoriginal (`icons/` + `tryck/`)** samt mushjulsskydd (`ui/wheel_guard.py`).
- **Låsta donationslänkar & Swish-QR** (`core/donate.py`, `ui/donate.py`).

---

## 🟡 Aktuella öppna förbättringsområden (framtida arbete)

1. **Krypterad lagring av SMTP-lösenord via OS-nyckelring**:
   - Flytta SMTP-lösenord från `email_settings.json` till Windows Credential Manager / macOS Keychain / SecretService med smidig migrering för befintliga profiler.
2. **Fullständig engelsk översättning (`core/i18n.py`) i samtliga detaljdialoger**:
   - Slutför migrering av kvarvarande svenska strängar i `ui/dialogs.py`, `ui/preview.py`, `script/contacts_ui.py` och Thunderbird-tilläggets popup.
3. **Utökade SMTP-integrationstester mot lokal mock-server**:
   - Komplettera sändningsdiagnostiktesterna med fullständiga end-to-end-tester för STARTTLS/SSL-felkoder, rate-limits och återupptagning vid nätverksavbrott.
4. **Konsolidera delade konstanttabeller**:
   - Samla `PLACEHOLDER_DROPDOWNS` till en enda gemensam modul som importeras av både `script/templates.py`, `ui/template_wizard.py` och `ui/main_window.py`.

För vidare produktidéer se `docs/25-produktforslag.md` (Omgång 1 & 2) samt den löpande icke-återbrukade loggen i `docs/forslagslogg.md`.
