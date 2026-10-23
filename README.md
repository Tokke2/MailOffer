# 📧 E-postofferten (MailOffer)

**Skapad av Rickard Längkvist**

**© 2026 Rickard Längkvist**

Tredjepartsbibliotek och deras material omfattas av respektive rättighetsinnehavares villkor.

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
- ✏️ **Redigera mallar, versioner & mallpaket** (nytt i 1.0) – öppna en
  befintlig mall i wizarden; tidigare innehåll sparas automatiskt som
  en version som kan förhandsgranskas och återställas. Elva färdiga
  mallar för påminnelser, tackmail, säsongskampanjer, bil/verkstad,
  hantverk/service och leverantörsförfrågningar kan kopieras in
- 👤 **Avsändarprofiler** (nytt i 1.0) – spara flera avsändarkonton
  (SMTP-server, avsändare, svar-till, egen kopia/arkiv) under
  *Inställningar → 📡 SMTP & Avsändare* och välj konto direkt i
  steg 4 **Skicka mail** i stället för att ändra inställningarna
- 🧪 **Testläge & förhandskontroll** (nytt i 1.0) – **🔎 Förhandskontroll**
  visar exakt slutantal (inkl. egen kopia/standard-Bcc), överlapp
  To/Bcc, ogiltiga adresser, SV/EN-fördelning och bilagestorlek;
  **🧪 Skicka testmail** skickar bara till din egen testadress
- 📡 **SMTP-förval & DNS-kontroll** (nytt i 1.0) – välj leverantör
  (Gmail/Outlook/Microsoft 365/Yahoo/iCloud eller webbhotell som
  WebSupport/Loopia/one.com – egna domäner gissas som mail.domänen;
  nodservrar som `smtp.m101.websupport.se` känns också igen)
  så fylls server, port
  och SSL i automatiskt, med länk till applösenord; kontrollera
  SPF/DKIM/DMARC för avsändardomänen med ett klick
- 💾 **Säkerhetskopiering** (nytt i 1.0) – en ZIP med kontakter,
  mallar, historik och inställningar (lösenord följer aldrig med)
  under *Inställningar → 💾 Säkerhetskopiering*, med återställning
- 👥 **Kontakter & grupper** med språk per mottagare – EN får alltid
  engelsk version, SV alltid svensk (VIN skickas bara i EN-mailet).
  **E-postlistor** kan importeras från TXT/CSV/TSV eller klistras in
  (även kopierade Excel-rader) och sparas under ett listnamn
- 🖼️ Bilagor med drag & drop och bildkomprimering, fritext ovan signatur
- 🌐 **Gränssnitt på svenska/engelska** (nytt i 5.4) – byt i menyn
  **Språk** eller i Inställningar (omstart erbjuds)
- 🔄 **Autouppdatering från GitHub Releases** (nytt i 5.4) – tyst sökning
  vid start (max 1 gång/dygn, kan stängas av) + manuell knapp under
  *Arkiv → Sök efter uppdateringar* och i Inställningar; även uppdaterade
  filer inom samma versionsnummer upptäcks och erbjuds
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
   tom mall, kopia av en befintlig eller en färdig mall från mallpaketen.
3. Skriv ämne och brödtext på svenska. Infoga uppgifter med knapparna
   (`::modell::`, `::ruta::`, `::vin::` …) eller **➕ Egen…**.
4. Bocka i engelsk version om EN-mottagare ska få mailet på engelska –
   knappen *Översätt automatiskt* ger ett utkast av den svenska texten.
5. Förhandsgranska med testvärden, spara – klart! Mallen hamnar i
   `Mallar/` och kan väljas direkt i Skicka-fliken.

I fliken **Mallar** kan en befintlig mall väljas och öppnas med
**✏️ Redigera vald mall**. När ändringarna sparas läggs den tidigare
filen automatiskt i versionshistoriken under `Mallar/.versions/`.
**🕘 Versioner** visar sparade versioner, låter dig spara nuvarande
mall manuellt och återställa eller ta bort en vald version. Med
**📦 Mallpaket** kopieras valda färdiga mallar direkt till mallmappen
utan att befintliga filer skrivs över.

## 📥 Lägg in e-postlistor

Det går att lägga in många adresser på en gång på två ställen:

- **Kontakter → 📥 Importera e-postlista**: välj en `.txt`-, `.csv`-
  eller `.tsv`-fil och ge importen ett listnamn/kategori. Svensk
  semikolon-CSV med rubriker som `E-post;Namn;Företag;Språk;Kategori`
  fungerar, liksom en enkel textfil med en adress per rad.
- **Kontakter → 📋 Klistra in lista**: klistra in adresser, Outlook-text
  (`Namn <namn@example.se>; …`), CSV-rader eller celler kopierade
  från Excel. `.xlsx` läses inte direkt – spara som CSV eller kopiera
  cellerna i stället.
- **Skicka → Steg 3 Mottagare**: varje To/Bcc-ruta har **📋 Klistra in
  lista** och **📥 Importera e-postlista** för det aktuella utskicket.
  Det går också att klistra flera adresser med `;` eller `,` direkt i
  adressfältet och trycka **Lägg till**.

Dubbletter tas bort automatiskt och importen visar hur många som
lades till, uppdaterades eller hoppades över som ogiltiga. I Kontakter
kan du filtrera på listnamnet/kategorin och använda
**Alla visade → To/Bcc**.

I Kontakter kan du även klicka **📄 Exportera kategori (.txt)** och
spara en kategori som en ren textlista med semikolon mellan
adresserna (`anna@example.se; bob@example.com`). Det går också att
exportera **alla kategorier på en gång** – då skapas en `.txt`-fil per
kategori i vald mapp. Filerna kan importeras tillbaka med samma
listimport.

## 🔄 Uppdateringar & att publicera en release (för ägaren)

Appen uppdateras **endast från GitHub Releases** – aldrig från `main`.
Vid uppdatering kopieras bara programkod. **Dina `Mallar/`, adresslistor,
JSON-filer, inställningar och loggar rörs aldrig** (`core/update_protect.py`).

Så publicerar du en ny version:

1. Bumpa `__version__` i **`core/version.py`** (enda versionskällan),
   t.ex. `"1.0.0"`.
2. Committa och pusha som vanligt.
3. Skapa releasen med exakt samma nummer i taggen:

   ```bat
   gh release create v1.0.0 --title "E-postofferten 1.0.0" --generate-notes
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
overwritten) and **Ko-fi donations**. New in 1.0: **sender profiles** (pick the
sending account per send) plus a **preflight check & test mode**
(final recipient counts, To/Bcc overlaps, attachment sizes; test
mail goes only to your own test address). New in 1.1: **SMTP provider
presets** with app-password links, a one-click **SPF/DKIM/DMARC check**
and full **backup/restore** (ZIP; passwords never included). Version number lives in
`core/version.py`. Run with `pip install -r requirements.txt` +
`python main.pyw`; tests with `python -m unittest discover -s tests -v`.

### Automatiska säkerhetskopior och profilsignaturer

Under **Inställningar → Säkerhetskopiering** kan automatisk lokal backup
aktiveras. Ange intervall i timmar (1–8760) och antal sparade kopior (1–100).
Appen kontrollerar vid start och varje minut medan den är öppen; en missad
körning tas vid nästa start. Kopior ligger i `.data/automatic-backups/` och
återställs med samma återställningsknapp som manuella ZIP-kopior. Lösenord
rensas även i automatiska kopior. Äldre automatiska kopior raderas först
sedan en ny kopia skapats korrekt; manuella kopior påverkas inte.

Varje **avsändarprofil** har egen signaturtext, kontaktinformation och
valfri PNG/JPG/GIF-logotyp (max 2 MB). Signaturen läggs till både svenska och
engelska utskick, inklusive testmejl. Logotypen bäddas in i mejlet och kräver
ingen extern bildserver. Använd **Spara profil** efter ändring. Signaturen
läggs till sist i mejlet; ta bort eventuell gammal signatur i själva mallen
för att undvika dubbla signaturer. Logotypfilen måste finnas kvar på angiven
sökväg. Lägg den gärna i mallmappen så att den kommer med i säkerhetskopior.

### Installera Thunderbird-tillägget

1. Starta MailOffer en gång från dess permanenta installationsmapp för att
   registrera native-messaging-kopplingen för den aktuella användaren.
2. I Thunderbird: **Tillägg och teman → kugghjulet → Installera tillägg från
   fil**, välj `thunderbird/MailOffer.xpi` från appmappen.
3. Högerklicka på en e-postlänk (`mailto:`) och välj **Skicka e-postadressen
   till E-postofferten**. Den klickade adressen skickas till appens kontakter,
   inte automatiskt mejlets avsändare. Adresser i kontaktfliken uppdateras när
   fliken öppnas igen eller med Uppdatera.
4. För meddelandelistan finns även **Spara avsändare i E-postofferten**.

Ingen e-post skickas av tillägget. Appen behöver inte vara öppen efter
registreringen. Flyttas appmappen, starta appen igen för att uppdatera
kopplingen. Bygg om XPI med `python tools/build_thunderbird.py` efter
ändringar i tillägget. Thunderbird-integrationen behöver också provas i
Thunderbird på den dator där den ska användas.

### Thunderbird-panel och levande signaturförhandsvisning

Under **Inställningar → Thunderbird-koppling** finns nu:
- **Registrera kopplingen** för den aktuella användaren och appmappen.
- **Installera Thunderbird-tillägg …** som öppnar XPI-mappen och visar hur
  tillägget installeras i Thunderbird. Appen kan inte installera tillägget
  utan Thunderbirds bekräftelse.
- **Testa lokal brygga**, som provar riktig native-messaging-inramning utan
  att lägga till testkontakter. Testet bekräftar den lokala hosten, inte att
  Thunderbird har laddat tillägget. Prova därefter ett högerklick i Thunderbird.

Kontaktfilen kontrolleras varannan sekund medan appen körs. Giltiga ändringar
laddas automatiskt in även när kontaktfliken redan visas. Felaktig/ofullständig
JSON laddas inte in. Om en egen adressmapp skiljer sig från bryggans adressmapp
visar testpanelen en varning.

Signaturen för vald profil visas direkt i inställningarna, även under
redigering. Utskickets förhandsvisning uppdateras vid byte av avsändarprofil
med samma signaturtext och bild som används vid sändning. Har profilen en
logotyp väljs HTML-visning för att bilden ska synas; Text kan fortfarande
väljas manuellt. Bilden läses lokalt i förhandsvisningen och bäddas in med
CID i det skickade mejlet. Mottagarens mejlklient kan påverka utseendet.

### Profilbundna mallar och dubblettskydd

På **Mallar**: välj **Tillåtna profiler för vald mall …**, välj mall och
markera vilka avsändarprofiler som får använda den. Standard är alla profiler.
Avmarkeras alla profiler (och även "Tillåt alla") spärras mallen för samtliga.
Mallhanteringsdialogen visar alltid alla mallar så att en spärr kan tas bort.
Sändlistan och mallfliken visar däremot bara den aktuella profilens mallar.
Regeln kontrolleras även i förhandskontrollen och sändtråden, inklusive testmejl.
Detta skyddar mot felval i appen, men är ingen behörighetsgräns mot personer
som kan redigera inställningsfilen eller kopiera mallfiler själva.

Före ett nytt utskick jämförs innehållsfingeravtryck och mottagare med
lyckade utskick de senaste 24 timmarna. Matchning visar en separat varning
med **Nej** som standardval. Mallinnehåll, ersättningsfält, fritext, signatur
 och bilagors innehåll ingår. Testutskick registreras inte för detta skydd.
Äldre historik utan fingeravtryck samt misslyckade/delvis lyckade utskick
kan inte användas av detta skydd. Raderad historik innebär också att
motsvarande dubblettskydd försvinner. Kontrollen är en varning, inte en
leveransgaranti eller exakt jämförelse av serverns slutliga MIME-meddelande.

### WebSupport och skräppost

Förhandskontrollen varnar för avvikande SMTP-port/kryptering och när
avsändaren skiljer sig från SMTP-inloggningen. En legitim aliasadress kan
fungera men måste vara godkänd hos leverantören. Behåll exakt servernamn
från kontrollpanelen (även exempelvis smtp.m101.websupport.se).

Kör DNS-kontrollen under Inställningar. Den kontrollerar publicerade
SPF/DMARC-poster och ett antal vanliga DKIM-selektorer; ett ej hittat
DKIM-värde bevisar inte att DKIM saknas. DNS-poster bevisar inte heller att
ett visst mejl skickats med fungerande signering eller DMARC-alignment.
Skicka ett test till en extern mottagare och granska mottagarens
Authentication-Results: SPF, DKIM och DMARC ska verifieras där. Hämta
DNS-värden för just er domän från WebSupport. Skapa inte dubbla SPF-poster.
Ingen app eller DNS-inställning kan garantera att alla mejl undgår skräppost;
rykte, mottagarnas samtycke, innehåll, volym och mottagarfilter spelar också in.

### Profilfärg och tangentbord

Under avsändarprofilens inställningar finns **Profilfärg → Välj färg …**.
Spara profilen efter ändringen. Färgen visas som ikon i profilväljaren och
som kantmarkering vid mallval, förhandsvisning och sändbekräftelse. Namn och
avsändaradress visas fortfarande; färgen är en extra ledtråd, inte en
behörighetsregel och påverkar inte mejlets innehåll. Ogiltig färg återställs
till standardblått.

**Hjälp → Tangentbord och genvägar**, eller F1, visar genvägarna:
- Ctrl+L: välj avsändarprofil; Ctrl+M: välj mall.
- Ctrl+K: sök kontakter; Ctrl+1–4: gå till ett steg i utskicket.
- F5: förhandsvisa; Ctrl+Shift+T: öppna testmejlsflödet.
- Ctrl+Enter: öppna sändflödet med kontroller och bekräftelse (skickar inte direkt).
- Ctrl+S: spara mall; Ctrl+Q: avsluta.
- Tab/Shift+Tab: flytta mellan fält, med tydlig fokusmarkering.

### Kompatibilitet med Thunderbird-tillägget

Installera om **thunderbird/MailOffer.xpi** från denna uppdatering i Thunderbird.
Både host och XPI använder nu ett separat protokollnummer (oberoende av
appversionen 1.0.0). Innan import gör tillägget en kontaktfri handskakning.
Saknat eller felaktigt protokollnummer stoppar importen innan kontakter skrivs.
Felmeddelandet ber användaren uppdatera appen, installera dess XPI och
registrera kopplingen igen. Äldre XPI som saknar protokollnummer avvisas också.

Appens **Testa lokal brygga** kontrollerar att medföljande XPI:s protokoll
stämmer med appen och att den lokala hosten svarar med rätt protokoll. Det
bevisar fortfarande inte vilken XPI som faktiskt är installerad i Thunderbird;
den kontrolleras vid ett riktigt importförsök. En nyare XPI får inte skriva
till en äldre host som inte stödjer protokollet.

### Startfönster och åtkomst till uppdateringar

Manuell start visar alltid huvudfönstret. Endast explicit `--background` eller
`--minimized` startar i brickan, och bara om brickikonen är tillgänglig.
Äldre `start_minimized`-inställningar kan inte längre dölja manuell start.
VBS-starten prioriterar `.venv`, `venv` och portabel `python` i appmappen före
systeminstallationer. Byggstämpel, vald Python och startläge skrivs i loggen.

GitHub-uppdateraren skickar ingen autentisering. **Privata GitHub-releaser är
inte åtkomliga för en vanlig installation utan en separat åtkomstlösning.**
HTTP 404 kan därför betyda antingen saknad release eller privat repo, inte
att appen redan är uppdaterad. GitHub-åtkomst via utvecklarens inloggade
verktyg är inte bevis på att en användares app kan ladda ner releasen.
Repoägaren måste besluta om offentlig release-distribution eller annan säker
åtkomstlösning; inga GitHub-token ska bäddas in i appen.

### Samma ikon i appen och Windows

`core/app_icon.py` är den gemensamma ikonkällan för app, dialoger och
systembricka. Huvudfönstret får även ikonen explicit och Windows får ett
versionsoberoende app-ID före Qt-start för korrekt gruppering i aktivitetsfältet.
Systembrickans statusmarkeringar läggs ovanpå samma grundikon. Thunderbird
använder samma motiv i sin paketerade ikon. Windows kan cachelagra gamla
ikoner för fästa genvägar; lossa och fäst om en gammal genväg vid behov.

Manuell VBS-start använder normalt Windows-visningsläge (`1`) med pythonw,
inte dolt visningsläge (`0`). Ingen konsol öppnas. Installationssteget kan
fortfarande köras dolt. Uppdaterad startkod känns igen på loggraderna
"Startfönster visas" och "Bygg=…". En äldre installation med version-only
uppdaterare kan behöva en första manuell uppdatering trots samma 1.0.0.
