# 📧 E-postofferten (MailOffer)

Skrivbordsapp (PyQt6) för offertmail: mallar med ifyllnadsfält, mottagare
med språk per kontakt (SV/EN), bilagor/bilder, To/Bcc-sändning via SMTP
samt Thunderbird-koppling. Guidat fyrastegsflöde:
**Mall → Bilagor/Bilder → Mottagare → Skicka mail**.

_English summary below._

## ✨ Funktioner

- 📝 **Mallar** i TXT/HTML/DOCX med uppgifter som `::modell::`, `::reg::`,
  `::ruta::` (13 glastyper i dropdown) och `[en]`-block för engelsk version
- 🧙 **Mall-wizard** (nytt i 5.4) – skapa nya mallar steg för steg:
  namn/format → svensk text → valfri engelsk text (autoöversättning) →
  förhandsgranskning med testvärden → spara
- 👥 **Kontakter & grupper** med språk per mottagare – EN får alltid
  engelsk version, SV alltid svensk (VIN skickas bara i EN-mailet)
- 🖼️ Bilagor med drag & drop och bildkomprimering, fritext ovan signatur
- 🌐 **Gränssnitt på svenska/engelska** (nytt i 5.4) – byt i menyn
  **Språk** eller i Inställningar (omstart erbjuds)
- 🔄 **Autouppdatering från GitHub Releases** (nytt i 5.4) – tyst sökning
  vid start (max 1 gång/dygn, kan stängas av) + manuell knapp under
  *Arkiv → Sök efter uppdateringar* och i Inställningar
- ❤️ **Donation via Ko-fi** (nytt i 5.4) – hjärtknapp i verktygsraden;
  länken läggs in under *Inställningar → ❤️ Stöd & om*
- 📨 Skicka-historik, leveransbarhets-guide (SPF/DKIM/DMARC), läskvitton,
  systembricka, autostart (Windows/macOS/Linux)

## ▶️ Kom igång

Kräver Python 3.10+.

```bat
pip install -r requirements.txt
python main.pyw
```

**Enklast på Windows:** dubbelklicka **`Starta EmailApp.vbs`** – den
startar appen helt utan konsolfönster. Saknas Python kör den först
`Installera_Python.bat` (installerar senaste Python 3.12) dolt i
bakgrunden och startar sedan appen. (`main.pyw` går också att
dubbelklicka – appen startar om sig själv med `pythonw.exe`.)
En exempelmall finns i `Mallar/` – skapa egna med
**🧙 Ny mall**-knappen.

## 🧙 Skapa en mall

1. Klicka **🧙 Ny mall** (eller *Arkiv → Skapa ny mall (wizard)…*).
2. Namn + format (TXT rekommenderas) och startläge: bilglas-exemplet,
   tom mall eller kopia av en befintlig.
3. Skriv ämne och brödtext på svenska. Infoga uppgifter med knapparna
   (`::modell::`, `::ruta::`, `::vin::` …) eller **➕ Egen…**.
4. Bocka i engelsk version om EN-mottagare ska få mailet på engelska –
   knappen *Översätt automatiskt* ger ett utkast av den svenska texten.
5. Förhandsgranska med testvärden, spara – klart! Mallen hamnar i
   `Mallar/` och kan väljas direkt i Skicka-fliken.

## 🔄 Uppdateringar & att publicera en release (för ägaren)

Appen uppdateras **endast från GitHub Releases** – aldrig från `main`.
Vid uppdatering kopieras bara programkod. **Dina `Mallar/`, adresslistor,
JSON-filer, inställningar och loggar rörs aldrig** (`core/update_protect.py`).

Så publicerar du en ny version:

1. Bumpa `__version__` i **`core/version.py`** (enda versionskällan),
   t.ex. `"5.5.0"`.
2. Committa och pusha som vanligt.
3. Skapa releasen med exakt samma nummer i taggen:

   ```bat
   gh release create v5.5.0 --title "E-postofferten 5.5.0" --generate-notes
   ```

   Ingen fil behöver bifogas – appen hämtar GitHubs zipball för taggen.
   (Bifogas en `.zip` används den i stället; den måste innehålla
   `main.pyw`, i roten eller i en undermapp.)
4. Klart – installerade appar hittar versionen vid nästa start
   (eller direkt via den manuella sökknappen).

## ❤️ Donera

Appen är gratis och alltid öppen för alla. Vill du stödja
utvecklingen finns en komplett **Stöd projektet**-sida i appen
(*❤️ Stöd projektet* i sidofältet) med:

- ☕ **Ko-fi:** <https://ko-fi.com/tokke2>
- 💳 **PayPal:** <https://paypal.me/Rickard3dPrint>
- 📱 **Swish** med QR-kod – numret fylls i under
  *Inställningar → ❤️ Stöd & om* (QR-koden ritas automatiskt)

Länkarna kan bytas i samma inställningsgrupp; `.github/FUNDING.yml`
ger Sponsor-knappen här på GitHub.

## 🧪 Tester

```bat
python -m unittest discover -s tests -v
```

UI-testen (wizard/donation) körs headless med `QT_QPA_PLATFORM=offscreen`
och hoppas över automatiskt om PyQt6 saknas.

## 🗂️ Struktur (urval)

| Sökväg | Innehåll |
|---|---|
| `main.pyw` | Startpunkt (bootstrap, single-instance, omstart) |
| `core/` | Inställningar, sändning, loggning, `i18n`, `github_update`, `donate`, `version` |
| `ui/` | Huvudfönster, `template_wizard`, `donate`-dialog, preview, tray |
| `script/` | Mall-motor (`templates.py`), kontakter/mottagare |
| `thunderbird/` | Thunderbird-tillägg + native host |
| `Mallar/` | Mallfiler (användardata – skyddas vid uppdatering) |
| `spec.md` | Fullständig master-spec |
| `docs/VAD-SAKNAS.md` | Kända luckor och roadmap-förslag |

---

## 🇬🇧 English summary

**E-postofferten** ("the e-mail quote") is a PyQt6 desktop app for sending
quote-request e-mails from templates with fill-in fields (car model,
registration number, glass type…), per-recipient language (Swedish/English
versions of the same template), attachments and To/Bcc batch sending.

New in 5.4: a step-by-step **template wizard** (TXT/HTML/DOCX), a **Swedish/
English UI** (Language menu), **auto-update from GitHub Releases** (silent
daily check + manual button; user templates/JSON/settings are never
overwritten) and **Ko-fi donations**. Version number lives in
`core/version.py`. Run with `pip install -r requirements.txt` +
`python main.pyw`; tests with `python -m unittest discover -s tests -v`.
