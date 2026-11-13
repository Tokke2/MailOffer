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
  vid start och sedan var 12:e timme (kan stängas av) + manuell knapp under
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

**Enklast på Windows:** dubbelklicka **`Starta EmailApp.vbs`**.
Starten använder datorns befintliga system-Python via pythonw, utan konsolfönster.
Ingen egen EXE eller Python-runtime medföljer.
`Installera_Python.bat` har kvar sitt namn för kompatibilitet men **installerar
eller uppgraderar aldrig Python**. Appen använder befintlig gemensam Python
3.10+. Saknas den visas ett fel; användaren/IT behöver
själv installera eller välja en lämplig systeminstallation. Ingen winget,
Python-nedladdning eller separat virtuell miljö används.
Endast appens tillägg kontrolleras/uppgraderas **en gång per vecka,
måndagar kl. 08.00 enligt datorns lokala tid**. Ett dolt Windows-schema
registreras för aktuell inloggad användare, utan sparat lösenord eller krav
på administratörskonto. Ingen app behöver vara öppen. Om tiden missas kan
Windows köra uppgiften senare när användaren är inloggad. Datorn väcks inte.
Vanlig start läser bara lokal veckostatus och vald interpreter; ingen ny
pip-kontroll görs när veckans kontroll redan lyckats. Missad kontroll
tas även igen vid nästa appstart. Första starten eller saknad interpreter
kräver initial kontroll. Misslyckade kontroller kan försöka igen vid nästa start.
Om arbetsdatorns policy blockerar schemat varnas det i loggen och nästa
appstart efter måndag 08.00 används som reserv.

Befintligt tidigare valt Python behålls om det fungerar; annars prioriteras
systemets PATH och därefter registrerade/standardinstallerade tolkar.
Python-versionen ändras inte. Ingen egen virtuell miljö skapas eller väljs.
Paket i requirements.txt används som minimiversioner vid veckokontrollen;
pip hämtar nyare stabila kompatibla paket och kör därefter pip check.
**Gemensamma uppgraderingar kan påverka andra program** som använder samma
Python och paket. Nätåtkomst krävs när underhållet utförs, inte vid vanliga
starter däremellan. Fel vid kontroll avbryter appstart med synlig varning.
Detaljer finns i logs/startup.log, veckostatus i
logs/python-maintenance.json. Parallella kontroller i samma appmapp spärras.
Veckouppgiften heter MailOffer-Python-Weekly-<appmappens ID>; ta bort den i
Windows Schemaläggaren om appmappen avinstalleras manuellt.
`Starta EmailApp.vbs` finns kvar som reservstart.
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
12-hour silent check + manual button; user templates/JSON/settings are never
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

### Avancerad start- och feldiagnostik

Vid fel: granska och dela vid behov `logs/startup.log`, `logs/app.log` och
`logs/errors.log`. Innehållet kan innehålla lokala sökvägar och kunduppgifter.
- `startup.log`: startfil, system-Python-kontroll, tillägg och startfel.
- `app.log`: appkörning, tidig diagnostik, trådar, varningar, Qt och fullständiga
  stackspår. Faulthandler skriver också här; ingen separat crash-logg skapas.
- `errors.log`: alla insamlade öppna fel och varningar från de andra loggarna.
- Inga storleksroterade .log.1-kopior skapas. Äldre dagar går till verifierade
  ZIP-filer i logs/archive; sju avslutade dagar behålls.
- Loggar skrivs bara i appmappens logs. Kan mappen inte skrivas visas fel,
  ingen tempmapp används som dold reserv.

Den fristående diagnostiken överlever ominitiering av den vanliga loggern.
Vanliga lösenords-/tokenfält och SMTP AUTH-data maskeras i diagnostikloggen,
men godtyckliga feltexter kan innehålla andra känsliga uppgifter. Inget
mejlinnehåll eller inställningsobjekt dumpas av diagnostikmodulen.
Strömavbrott, tvångsavslut och fel som fångas utan att loggas kan inte
garanteras finnas i loggen. Om VBS är blockerat av Windows och aldrig körs
kan det inte heller skapa någon launcher-logg.

### Fritext före signatur och anpassad sändbekräftelse

Fritext placeras före en igenkänd avslutningsrad i mallen, exempelvis
"Tack på förhand!", "Med vänliga hälsningar", "Mvh" eller "Best regards".
Samma hjälpfunktion används vid sändning och i förhandsvisning. Om mallen
saknar igenkänd avslutningsrad läggs fritext sist i malltexten, fortfarande
före eventuell separat profilsignatur. Lägg därför avslutningen på en egen
rad/block för entydig placering. HTML-fritext behandlas som vanlig text,
inte som körbar/formaterande HTML.

Bekräftelserutan före sändning anpassas till skärmens arbetsyta. Lång
sammanfattning, varningar och kontrollresultat ligger i ett rullningsbart
område. Avbryt/Förhandsgranska/Skicka nu ligger kvar utanför området och
knappraden kan radbrytas vid smalare fönster. Ämnen och adresser återges
som vanlig text så att vinkelparenteser inte tolkas som HTML.

### Skärmanpassning för appfönster

En gemensam Qt-kontroll håller huvudfönster och dialoger inom skärmens
**tillgängliga arbetsyta**, med hänsyn till aktivitetsfält och Qt:s logiska
pixlar vid DPI-/Windows-skalning. För stora eller bortflyttade sparade
fönsterstorlekar begränsas; negativ position på en ansluten vänsterskärm
är däremot giltig och behålls när fönstret ryms.

Kontrollen körs vid visning, storleksändring, skärmbyte och förändrad
arbetsyta. Minimerade och maximerade fönster lämnas åt fönsterhanteraren.
När innehåll inte ryms får vanliga dialoger rullning; wizard-sidor rullas
separat så att navigeringen ligger kvar. Befintliga dialoger med egen
rullning, till exempel sändbekräftelsen, behåller den. Vid behov kan även
huvudfönstrets innehåll rullas i stället för att kapas. Inga automatiska
ändringar av textstorleken görs.

Verifierat med offscreen-Qt på små arbetsytor; faktisk Windows-skalning
på flera fysiska skärmar behöver också provas på användardatorn.


### Tyst sökning två gånger per dygn och tyst omstart

Automatisk uppdateringssökning görs när 12 timmar gått sedan senaste
kontrollen, även när appen varit öppen länge. Appen kontrollerar tiden
varje minut och gör en kontroll strax efter start om det är dags. När
appen är stängd körs ingen sökning; förfallen sökning tas vid nästa start.
Automatiken visar ingen popup, tray-notis eller fråga när fönstret öppnas.
Statusrad/logg kan visa att uppdaterade filer finns. Manuella sökningar
visar fortfarande resultat och erbjudande om installation.

Installation kräver fortfarande godkännande. Efter lyckad installation
startar appen om utan separat fråga. Om sändning eller en modal dialog
pågår väntar omstarten. Installation väntar också på pågående sändning.
Arbetsläget (text, mottagare, språk, profil-id, fält och bilagesökvägar)
sparas lokalt och återställs efter omstart; inga SMTP-profiler/lösenord
sparas i sessionsfilen. Bilagornas filer måste fortfarande finnas kvar.
Sessionsfilen innehåller mejlutkast och raderas efter lyckad återställning.
Om sparandet misslyckas avbryts omstarten och felet loggas. Partiellt
misslyckad installation startar inte automatiskt om och ger felbesked.
Tidigare synligt fönster visas igen; tray/minimerat läge återstartar i
bakgrunden utan konsolfönster. Versionen förblir 1.0.0 även vid nya byggen.

### Ingen konsol vid normal Windows-start

Starta med `Starta EmailApp.vbs` för appfönster utan
terminal. Om `.pyw` är associerad med konsol-Python i Windows kan den
associationen skapa en konsol innan appkoden hinner köra; VBS-starten
undviker det. En redan öppnad terminal som användaren själv startat stängs
inte av appen.

Bakgrundskontroller av pip/ensurepip, paketinstallation och test av
Thunderbird-bryggan använder nu `CREATE_NO_WINDOW` på Windows. När hjälpen
behöver läsa Pythons stdout används tillgänglig python.exe bredvid pythonw,
men utan konsolfönster och med omdirigerad utdata. Loggarna ligger kvar i filer.

Beroendekontrollen verifierar även att pip fungerar efter en lyckad
ensurepip-körning. Felkod eller timeout rapporteras som fel, inte som lyckad
installation. Hjälpprocesserna har stängd standardinmatning och tidsgränser,
så att en dold process inte väntar på terminalinmatning.

### Automatisk cacherensning med smartfilter

I **Inställningar → Loggning & drift** finns automatisk rensning en gång
per 24 timmar (aktiverad som standard) och **Rensa cache med smartfilter nu**.
Även den manuella knappen behåller färska cachefiler. Endast vanliga `.pyc`-filer
äldre än 24 timmar i `__pycache__` direkt under appens rot, `core`, `ui`
och `script` tas bort. Inga rekursiva sökningar, symlänkar/junctions eller
systemets temporära katalog rensas av smartfiltret. Låsta filer lämnas kvar
med fel i loggen.

Kontrollen sker tyst under körning och strax efter nästa start om den är
förfallen; ingen schemalagd uppgift körs när appen är stängd. Pågående sändning
eller uppdateringsinstallation får avslutas först. Tidpunkten sparas i
inställningarna, så omstarter startar inte nya dygnsrensningar. Vid avslut
rensas endast registrerade temporära filer, inte längre all Python-cache.
Mallar, bilagor, kontakter, loggar, inställningar och backuper lämnas orörda.

### Skydd mot dubbla utskick

Skicka-knapparna låses direkt, redan före förhandskontroll och bekräftelse,
och visar att sändning förbereds/pågår. Även kortkommandon spärras mot ny
sändning medan den första förbereds eller körs. Knapparna återställs efter
avbrott eller fel, och efter att sändning och resultathantering avslutats.

Finns samma registreringsnummer i den sparade sändhistoriken visas en
extra varning med **Nej som standard**. Du kan godkänna en avsiktlig
återsändning. Kontrollen gäller hela tillgängliga historiken (högst 500
utskick), oavsett ålder, mottagare eller innehåll. Versaler/gemener,
mellanslag och bindestreck ignoreras. Äldre historik med registreringsnummer
i formulärfälten stöds; nummer gissas inte från fri ämnes-/brödtext.
Testmail utlöser inte registreringsvarningen. Befintlig varning för samma
innehåll till samma mottagare inom 24 timmar finns kvar.

### Standard-BCC för vissa mallar

Öppna **Mallar → Standard-BCC per mall**, välj mall och markera de kontakter
som alltid ska få en dold kopia med den mallen. Spara med OK. Avmarkera alla
för att ta bort kopplingen. Lägg först till nya adresser under Kontakter.
Sparade adresser kan avmarkeras även om kontakten senare tagits bort.

Mallens BCC visas under mallvalet och standard-BCC-adresserna visas även i
sändbekräftelsen. Dessa adresser kompletterar global standard-BCC och vald
profils arkivkopia. De läggs inte i den manuella mottagarlistan, så byte till
en annan mall lämnar inte kvar föregående malls adresser. Dubbletter hanteras
av samma mottagarkontroll som övriga adresser. Testmail får inga mallbundna
kopior. Kopplingen sparas per mallfilnamn och e-postadress, inte som en
följande kontaktidentitet; ändrad kontaktadress kräver nytt val. Byter mallen
namn behöver kopplingen också göras för det nya namnet.


### Ny MailOffer-ikon och Windows-autostart

Den valda kuvertikonen med turkos offertbricka används i app/dialoger,
systemfältet (med statusmärken), Thunderbird-tillägget och Windows-genvägar.
PNG har transparenta hörn, ICO innehåller 16–256px-varianter. EXE-startfilen
har inbyggd ikon och produktinformation med Rickard Längkvist som skapare.

Windows-autostart använder `wscript.exe` och `Starta EmailApp.vbs --background`.
Aktiverad äldre autostart migreras av den befintliga synkroniseringen vid
appstart. Om EXE saknas används VBS via wscript som reserv; aldrig en direkt
Python/.pyw-post. Om båda startfilerna saknas rapporteras fel. Avstängd
autostart aktiveras inte av uppdateringen. Python/pythonw kan fortfarande
användas internt – appen ändrar inte Windows globala filassociationer.

Skapa genvägar till **Starta EmailApp.vbs**; välj icons/app_icon.ico som genvägsikon.
Gamla aktivitetsfältsnålar till Python behöver lossas och ersättas med den
nya startfilen; vi ändrar inte användarens nålar automatiskt. Windows kan
behålla en gammal ikon i sin ikoncache. Startfilen är inte kodsignerad och
Windows/SmartScreen kan därför visa en säkerhetsvarning.

Bygg om ikoner med `python tools/make_icon.py` (Pillow krävs) och tillägget
med `python tools/build_thunderbird.py`. Bygg startfilen med
`pip install ziglang==0.17.0` och `python tools/build_launcher.py`.
Källkod/resurser finns under `launcher/`. Startfilens GUI-subsystem,
ikonresurser och autostartval kontrolleras i portabla tester; faktisk start
och aktivitetsfält på Windows behöver verifieras på en Windows-dator.

### Uppdatering vid samma versionsnummer: verklig commit- och filkontroll

Appens kontroll använder senaste **publicerade GitHub-release**, aldrig
`main`. Release-taggen slås upp till sin verkliga commit (även annoterade
taggar); `target_commitish` räcker inte eftersom det kan innehålla ett
gammalt branchnamn. Källarkivet låses till den upplösta commit-SHA:n.

Vid kontrollen laddas release-arkivet ned i en tillfällig katalog. SHA-256
för appfilerna jämförs med installerade filer, med samma undantag för
användardata som installationen. Ändrade/saknade appfiler eller en ändrad
sparad release-commit ger uppdatering även om både version och byggstämpel
är oförändrade. Detta fungerar även vid en manuell installation utan
sparat release-fingeravtryck. Enbart ändrade releaseanteckningar ger ingen
ominstallation när commit och filinnehåll matchar.

Vid installation verifieras att arkivet är det som kontrollerades och att
kopierade appfiler matchar efteråt. Ändrat arkiv kräver en ny kontroll;
verifieringsfel rapporteras som fel, inte som ”senaste version installerad”.
Baseline för commit/fingeravtryck sparas först efter verifierat matchande
innehåll eller lyckad installation. Mallar, JSON/inställningar, kontakter,
loggar och andra skyddade användarfiler jämförs/ersätts inte. Lokala filer
som saknas i releasen raderas inte.

Kontrollen körs i bakgrunden men hämtar nu ett arkiv vid varje förfallen
12-timmarskontroll, vilket använder mer nättrafik än enbart metadata.
Tyst sökning, godkännande före installation och automatisk säker omstart
är oförändrade. Versionsnumret ligger kvar på **1.0.0**.

### Samlad fellogg för snabb felsökning

**`logs/errors.log`** samlar identifierade fel, varningar och stackspår från
`app.log` och `startup.log`. Äldre loggformat läses också in vid migrering.
Varje post anger källfil och insamlingstid; ursprunglig
tid och feltext behålls. Äldre källposter flyttas därefter till dagsarkiv.

Loggarna läses inkrementellt i en bakgrundstråd ungefär var femte sekund,
vid nästa start och en sista gång vid normalt avslut. Läspositioner sparas
i `logs/errors.state.json` så omstarter/vanlig loggrotation inte återimporterar
samma innehåll. Indexet lagrar positioner och hashvärden, inte feltexter.
Samma fel kan finnas under flera källfiler om originalen loggat det på
flera ställen. Normal start/avslut med felkod 0 tas inte med.

Öppna **Loggar → Öppna samlad fellogg** för att uppdatera och öppna filen.
Samtliga loggar, arkiv och insamlarens index/lås ligger i
`<appmapp>\logs\`. Insamlaren läser bara loggar i denna undermapp, inte
gamla reservloggar eller andra filer i tempmappen.

Den centrala felloggen är nu en genererad vy över **alla öppna fel** i
`logs/error-issues.sqlite3`: den roteras eller gallras inte bort. För att begränsa
resursåtgång läses högst 1 MB per källfil och omgång och de 128 senast ändrade
loggfilerna bevakas. Arkivering väntar tills källans fel har sparats i registret.
Stora loggar kan därför kräva flera insamlingsomgångar.

Vanliga lösenords-, token- och AUTH-värden maskeras, men loggen kan innehålla
andra person- och ärendeuppgifter: **granska den innan du delar den**.
Ingen automatisk uppladdning sker. Fel som aldrig loggats, raderade eller
oläsbara loggar, full disk och en hård process-/strömavstängning kan inte
garanteras fångade. Native-krascher och startfel som skrivs efter att appen
stannat samlas tidigast vid nästa start/manuell insamling.

Om appens gränssnitt inte går att öppna kan insamlingen köras utan Qt:
`python -m core.error_log --base-dir "D:\Program\MailOffer"`.
Appmappen måste vara skrivbar; alternativ utmatning med `--output-dir`
finns inte längre, så även manuell insamling stannar i appens loggmapp.

### Uppdateringskontroll från systemfältet

Högerklicka på MailOffer-ikonen i systemfältet och välj **Sök efter
uppdateringar**. Appfönstret visas och samma manuella release-/commit-/
filkontroll som under Hjälp startas, med resultat och installationsfråga.
Om en automatisk kontroll redan körs används dess resultat som en manuell
kontroll i stället för att starta en till. Tyst automatisk kontroll påverkas
inte när du inte uttryckligen begär ett resultat.

### Importera bildbilagor direkt från Thunderbird

1. Uppdatera MailOffer och **installera om `thunderbird/MailOffer.xpi`** i
   Thunderbird (hjälp finns under appens Thunderbird-inställningar).
2. Markera **ett mejl** i Thunderbirds meddelandelista. Högerklicka och välj
   **Importera bildbilagor till MailOffer**.
3. Visa/starta MailOffer. När appen är synlig och ingen sändning, installation
   eller modal dialog pågår visas ett bildval med filnamn/storlek.
4. Markera vilka bilder som ska bifogas och välj OK. De läggs till i det
   aktuella utskickets vanliga bilagor och skickas med när du senare
   godkänner sändningen. Befintlig text/mottagare ersätts inte.

PNG, JPEG, GIF, WebP, BMP och TIFF stöds; högst 10 bilder, 10 MB per bild
respektive 20 MB totalt per import. Tillägget använder mejlets lokala
bildbilagor, inte externa bildlänkar i HTML-text. Inline-/signaturbilder
kan följa med om Thunderbird listar dem som bilagor – avmarkera dem i valet.
SVG och andra format tas inte med. Bildsignaturer kontrolleras och säkra
filnamn skapas; detta är inte en antiviruskontroll eller garanti att en
bild går att avkoda.

Bilder kopieras lokalt till `.data/mail-images/<unik import>/`. De kan
köas medan appen är stängd och väljas vid nästa start. Ingen sändning eller
uppstart av MailOffer görs automatiskt av tillägget. Originalmejlet ändras
inte och inga bilder laddas upp av importfunktionen. Vanlig e-postsändning
skickar däremot de valda bilagorna till dina mottagare.

Kopiorna behålls även efter avslutad/avbruten import för att inte bryta
bilagor, sparade utkast eller historik. De rensas inte av smart cache eller
uppdatering. Rensa endast en importmapp manuellt när bilderna inte längre
behövs. Funktionen gäller Thunderbird; andra e-postprogram har ingen ny
koppling i den här uppdateringen. Faktisk Thunderbird-/Windows-interaktion
behöver provas på användardatorn.


### En enda loggmapp i appmappen

Alla loggar samlas i **`<appmapp>\logs\`**, exempelvis
`D:\Program\MailOffer\logs\`. Undermappen skapas automatiskt och innehåller
exakt tre aktiva textloggar: `app.log`, `startup.log` och `errors.log`.
Felloggens databas,
index och lås ligger också där, inte bland appfilerna i roten.

Ingen ny loggning sker till `%TEMP%`. Startfilen varnar om den inte kan
skriva loggar och huvudloggern kontrollerar skrivbehörighet redan vid
start; vid fel behöver appen en skrivbar plats eller korrigerade
mappbehörigheter. Uppdatering/smart cache rensar inte loggmappen. Äldre
reservloggar flyttas eller raderas inte automatiskt.

### Dagsarkiv: bara dagens poster kvar i aktiva loggar

Tidigare dagars poster flyttas till verifierade ZIP-filer under
`logs/archive/ÅÅÅÅ-MM-DD/`. **Efter verifieringen ersätts den aktiva filen med
endast dagens poster**, inklusive deras fortsättningsrader/stackspår.
Framtidsdaterade poster behålls också, för att inte tappa data vid felställd
klocka. Dagsgränsen följer datorns lokala kalenderdatum. Odaterade poster
hänförs till senaste läsbara ISO-datum, annars filens ändringsdatum.

Det sker vid start, dygnsskifte och uppföljande försök ungefär varje minut.
Innan något tas bort måste insamlaren ha hunnit spara källans fel i registret.
Appens filskrivare pausas med handlerlås. På Windows stängs deras filhandtag
under kontrollen och källan får exklusiv skrivåtkomst; upptagna externa filer väntar.
Den färdiga dagsfilen skrivs till en temporär fil och synkas till disk innan
ett atomiskt namnbyte. Inga öppna filer skrivs om med oskyddad trunkering.
En liten arkivjournal gör att läspositionen kan återställas efter avbrott,
så kvarvarande dagens fel inte återimporteras som nya bara på grund av bytet.
På andra system kräver externa skrivare att de respekterar filens advisory-lås.

Dagsarkiv sparas för de **sju avslutade kalenderdagarna före idag**. Äldre data
arkiveras/verifieras före borttagning ur källan och gallras därefter enligt
sjudagarsregeln. Loggar över 50 MB, otolkbar textkodning och upptagna filer
lämnas orörda i stället för att riskera data; orsaken loggas och nya försök görs.
Aktuellt rått faulthandler-utflöde hanteras först när processen avslutats.
Öppna arkivmappen via **Loggar → Öppna loggarkiv**.

### En central fellogg som behåller olösta fel

**`logs/errors.log`** visar alla insamlade **öppna fel och varningar**, med
referens-ID, källfil, första/senaste observation, antal och feltext/stackspår.
Den är undantagen från dagsarkiveringen: ett olöst fel ligger kvar även om
ursprungsdagen är äldre än sju dagar. Inga nya roterade kopior av denna vy skapas.
**`logs/error-issues.sqlite3`** är det beständiga registret bakom filen.

Äldre `errors.log`-historik importeras vid uppdatering och säkerhetskopieras
som verifierat ZIP före formatbytet (engångskopian kan även innehålla dagens
historik). Den tidigare genererade `unresolved-errors.log` slås samman med
registret och tas bort först när den centrala vyn skapats. Tidigare åtgärdade
fel öppnas inte igen av historieimporten. Redan raderad historik kan inte återskapas.
Kända gamla stderr-INFO-felklassningar tas inte in på nytt som fel. Redan
registrerade historiska fel lämnas dock kvar tills de markeras som åtgärdade.

Välj **Loggar → Öppna fel / markera åtgärdade**, markera poster och bekräfta
**Markera valda som åtgärdade**. Det reparerar inte orsaken; kontrollera först
att felet är löst. Appen gissar inte att ett fel är åtgärdat bara för att det
varit tyst en tid. Återkommer samma identifierade fel öppnas det igen.
Åtgärdade poster finns kvar i databasen men tas bort ur den öppna felloggen.
Redigera inte den genererade filen manuellt. Kopiera även databasen vid flytt.
Om den genererade felloggen saknas återskapas den från registret.

Alla loggar, arkiv, index och journaler stannar i appmappens `logs/`.
Öppna fel/SQLite har ingen automatisk storleks- eller tidsgallring. Granska
innehållet före delning: arkiven innehåller originaltext, inte en garanterat
anonymiserad export. Diskfel/strömavbrott kan aldrig ge en absolut datagaranti.

### Autosparade utkast, dubbletter och bilagor

- **Autosparning:** ändrat arbetsinnehåll sparas ungefär varannan sekund och
  vid normal avslutning i `.data/compose-draft.json`. Ämne, text, fritext,
  mallnamn, platshållarvärden, profil-ID, mottagarnas adresser/språk och
  bilagornas sökvägar ingår. SMTP-inställningar/lösenord sparas inte av denna
  funktion. Mejlets innehåll kan naturligtvis ändå vara känsligt: filen är
  lokal och inte krypterad. Utkastet skyddas från releaseuppdateringar.
- Vid nästa synliga appstart frågar appen om utkastet ska återställas eller
  kastas. Dold autostart skriver inte över ett väntande utkast. Saknade bilagor
  rapporteras; filerna kopieras inte av autosparningen. Ett återställt utkast
  skickas aldrig automatiskt. Lyckad ordinarie sändning rensar utkastet;
  testmejl eller misslyckad sändning gör det inte. De sista sekunderna före
  ett hårt avbrott kan saknas. Ett arbetsläge efter godkänd uppdateringsomstart
  prioriteras framför ett äldre autosparat utkast.
- **Dubbla mottagare:** adresser jämförs utan hänsyn till stora/små bokstäver.
  Samma adress i Till och Hemlig kopia (eller överlappande standard-/arkiv-Bcc)
  blockerar sändningen med en varning tills överlappningen rättats. Ett
  standard-Bcc som redan visas i Bcc-listan är samma mottagare, inte en extra
  dubblett. Upprepad manuell inmatning i samma lista ger också en varning.
  Appen har inget separat Kopia-fält.
- **Kontakter → Granska dubbletter:** föreslår kontakter med samma icke-tomma
  namn **och** företag, med normaliserade blanksteg och bokstäver. Detta är
  endast förslag, inte säker identifiering av en person. Exakta e-postadresser
  är redan unika i adressboken. Granska före/efter, välj vilken e-postadress
  som ska behållas och bekräfta. Övriga adresser tas bort ur adressboken,
  kategorier förenas och primärkontaktens språk behålls. Historik och redan
  ifyllda mottagarlistor ändras inte. En `contacts-merge-backup-<ID>.json`
  sparas bredvid kontaktfilen före ändringen; dessa kopior gallras inte
  automatiskt. Vid sparfel återställs kontaktmodellen.
- **Dra och släpp:** släpp en eller flera lokala filer direkt i bilagelistan
  i steg 2. Mappar och webblänkar accepteras inte; redan tillagda sökvägar
  läggs inte till en gång till. Ingen fil flyttas eller skickas automatiskt.

### Skriptstart utan egen EXE

Appen distribueras utan egen EXE. Start, autostart och omstart använder
`Starta EmailApp.vbs` och datorns befintliga system-Python via pythonw.
Appens fönster och systemfält behåller egna ikoner, men Aktivitetshanteraren
kan visa Python som processnamn och processikon. Befintligt enkelinstansskydd
finns kvar. Första start är minimerad.

Gamla EXE-filer används inte, även om de ligger kvar från en tidigare version.
Stäng appen och radera en sådan gammal fil manuellt; återställ inte en fil som
Defender har satt i karantän. Gamla fastnålade EXE-genvägar måste ersättas.
Uppdateraren installerar inga .exe-filer.

### Alltid minimerad start
Appen startar alltid i systemfältet när brickan är tillgänglig, även vid
dubbelklick och oavsett äldre startinställning. Saknas systembricka startar
fönstret minimerat i aktivitetsfältet, inte oåtkomligt dolt. En andra start
visar fortfarande den befintliga instansen. Återställning av utkast väntar
tills fönstret visas.

### Rätt nivå för stderr-loggar
Normal INFO-/DEBUG-utmatning blir inte längre ERROR bara för att den passerar
stderr i pythonw. GUI-läget skapar ingen konsollogger när stdout saknas.
Strukturerade stderr-loggrader behåller sin nivå; oformaterade fel/tracebacks
behålls som fel. Tidigare felloggsposter raderas eller markeras inte automatiskt
som åtgärdade av denna ändring.

### Python 3.15 först, 3.14 som reserv
Vid val av system-Python provas installerad 3.15 först och därefter 3.14.
Misslyckade versions-, tilläggs- eller Qt-starttester leder vidare till nästa
befintliga kandidat. Äldre stödda systemversioner provas sist. Ett fungerande
sparat val behålls mellan veckokontrollerna, men kontrolleras offline vid start.
Tillägg uppdateras bara när veckounderhållet är aktuellt. Reservvalet installerar
inte Python, ändrar inte PATH och skapar ingen separat miljö. Ett misslyckat
paketunderhåll kan redan ha ändrat tillägg i den gemensamma installationen;
dessa paketändringar återställs inte automatiskt när nästa Python provas.

### Koppla mottagare till en mall
Välj mall i steg 1 och klicka **Koppla adresser…**. Välj från dropdown,
skriv en adress eller markera flera i **Adressbok…**. Spara kopplingen.
Alla sparade adresser visas automatiskt i **Bcc-listan** och skickas som
hemliga kopior. Dropdownens **Lägg till i Bcc** kan återlägga valda adresser.
Mallbyte tar bort automatiska rader från föregående mall men behåller manuella
Bcc-adresser. Kopplade adresser tas bort ur Till för att inte exponeras där.
Språk från adressboken används, och ändrat språk på en befintlig rad behålls.
Ta bort en koppling i dialogen och spara för att utesluta den permanent;
att bara radera en automatisk rad återlägger den vid nästa uppdatering.
Både äldre mottagarkopplingar och äldre Bcc-regler används; vid sparande
samlas de under den redigerade mallens mottagarkoppling. Avbryt ändrar inget.
Kopplingarna gäller exakt mallfilnamn och är globala för appen, inte per profil.
Byter du namn på filen behöver kopplingen läggas upp igen.

### Tangentbord utan mus
Tab/Shift+Tab följer layoutordningen genom utskickets fyra steg, även ut ur
mejltext och fritext. Dynamiska mallfält tas med när de byggs om. Fokuserade
kontroller skrollas fram och markeras; dialoger får layoutbaserad tabbordning.
Använd piltangenter i dropdown/listor och Mellanslag på knappar/kryssrutor.
Shift+F10 eller Meny-tangenten öppnar snabbmenyn i listor med sådan meny.
- Ctrl+1–4: gå till steg; Ctrl+M: mall; Ctrl+L: avsändarprofil.
- Ctrl+Shift+R/B: Till/Bcc. Ctrl+Shift+A: lägg till bilagor.
- Ctrl+Shift+O: adressbok. Ctrl+Shift+M: koppla mallens mottagare.
- Ctrl+Shift+P: sändningskontroll. F5: förhandsgranskning.
- F1: kortkommandohjälp. Ctrl+Enter öppnar befintligt sändningsflöde med
  dess kontroller; Tab och fokusförflyttning skickar aldrig mejl.
Dialoger från Windows (exempelvis filväljaren) använder Windows egna kortkommandon.

### Musens bakåt-/framåtknappar
När huvudfönstret är aktivt går musens bakåtknapp till föregående besökta
flik och framåtknappen framåt i flikhistoriken. Ett nytt flikval efter bakåt
ersätter framåthistoriken. Dolda/inaktiverade flikar hoppas över. Upp till
100 besök behålls under sessionen. Knapparna fångas inte i andra fönster,
dialoger eller öppna popupmenyer. Funktionen ändrar inte fält eller skickar mejl.

### Start, systemfält och olika operativsystem
- **Windows:** Starta EmailApp.vbs, befintlig system-Python, ingen egen EXE.
- **Linux:** `./Starta MailOffer.sh`; tillägg måste redan finnas för vald system-Python.
- **macOS:** `Starta MailOffer.command` (kan öppna Terminal vid manuell start),
  eller start med befintlig Python. Registrerad LaunchAgent öppnar ingen Terminal.
- Shell-starten provar 3.15, 3.14 och övriga listade systemversioner och testar
  Qt/tillägg utan att installera Python eller skapa en virtuell miljö.
- Under **Inställningar → Autostart**: välj **Starta med systemet** och spara.
  **Kontrollera/reparera autostart…** kan aktivera efter bekräftelse och visar
  registrerat kommando/status. Autostart betyder vid **användarinloggning**.
- Windows använder aktuell användares Run-post. Om Windows själv blockerat
  posten visas det; appen kringgår inte OS-inställning, Defender eller policy.
- macOS använder användarens LaunchAgent, Linux XDG-autostart (inklusive
  XDG_CONFIG_HOME). Linux Exec får korrekt escaping och arbetsmapp/ikon.
- Registrerad post är inte ett bevis på lyckad inloggningsstart. Desktop-policy,
  macOS bakgrundsbehörigheter och miljön kan fortfarande hindra den.
- Med synlig, tillgänglig systembricka gömmer minimera/stäng appen i brickan.
  Saknas brickan minimeras den i stället och blir inte oåtkomligt dold.
  Välj **Avsluta** i app/systembricka för fullständig avslutning.
- Linux behöver en skrivbordsmiljö med systemfält/AppIndicator-stöd för bricka.
  macOS använder menyraden. Fysisk inloggning/tray har inte verifierats på alla
  skrivbordsmiljöer; se tester och OS-inställningar vid problem.
- Veckovis automatiskt tilläggsunderhåll är Windows-funktionen; på macOS/Linux
  hanteras installation/uppdatering av tillägg manuellt i systemets Python.

### Ny logotyp och tryckoriginal
Se `docs/BRANDING.md`. SVG-original finns i `icons/mailoffer-logo.svg`,
`icons/mailoffer-logo-black.svg` och `icons/app_icon.svg`. Texten är banor,
inte ett typsnittsberoende eller en inbäddad bild. PNG, ICO och ICNS exporteras
från samma vektorsymbol. Aktivitetshanteraren kan fortfarande visa Python-ikon.

### Tre aktiva textloggar och sju dagars arkiv
Från bygg 2026102341 används app.log, startup.log och errors.log. Äldre
loggfiler säkerhetskopieras till verifierade ZIP-filer och tas bort först
efter att insamlaren läst hela innehållet. Även dagens äldre format kan
finnas i migrationsarkivet, i stället för som en extra aktiv logg.
Vanliga dagsloggar behåller bara dagens och eventuella framtidsdaterade poster.
Olösta fel behålls i errors.log oavsett ålder tills de åtgärdsmarkeras.
Databas, läsindex, låsfiler och underhållsstatus är tekniska filer, inte
ytterligare textloggar, och behövs för att bevara fel och läspositioner.
Windows-startlogg använder genomgående UTF-16 för både VBS och PowerShell;
app.log är UTF-8. macOS-startlogg använder systemets UTF-8-utmatning.
Faulthandler pausas kort under verifierad filkomprimering och binds om till
den nya app.log-filen; en native-krasch just under pausen kan sakna stackdump.
Låsta/otolkbara/för stora eller ännu inte helt inlästa källor lämnas kvar
och provas igen. Därför kan äldre extra loggar tillfälligt finnas vid migration.
Arkivering sker vid start och med återförsök under körning; efter avstängning
behandlas föregående dagar vid nästa start. Ingen separat ständig loggtjänst.

### Sändningsdiagnostik (bygg 2026102342)
Vid sändning från appen kontrolleras avsändardomänens SPF-/DMARC-poster och
vanliga DKIM-selektorer automatiskt i sändningstråden. Uppslagen använder
befintlig DNS-over-HTTPS mot Google, nu även automatiskt; endast domännamn
skickas i DNS-frågorna, inte mottagare, signatur eller meddelandetext. Varje
uppslag har 0,7 sekunders nätverkstimeout (tio uppslag; operativsystemets
namnuppslagning kan ta längre tid). DNS-fel stoppar inte utskicket.
Före varje verklig MIME-batch kontrolleras text/HTML, signaturtext,
kontakttext, inbäddad signaturlogo, bildreferenser, ämne, centrala headers
och kvarvarande {{platshållare}}. Brister ger SEND_CHECK-varningar i app.log
och samlas i errors.log; Bcc-header eller exponering av batchens hemliga
mottagare i Till/Kopia stoppar sändningen. Torrkörning använder samma
MIME-kontroller utan SMTP eller automatiska DNS-anrop. De nya kontrollraderna
loggar inte meddelandetext, signaturtext, lösenord eller mottagarlistor.
Befintlig SMTP-loggning visar anslutning, TLS/SSL och autentiseringsresultat.
Övriga befintliga loggar kan fortfarande innehålla adresser; granska innan delning.

**Ingen inkorgsgaranti:** hittad SPF-post innebär inte att sändande server
är auktoriserad; hittad DKIM-nyckel bevisar inte giltig signering. Att ingen
vanlig DKIM-selektor hittas betyder okänt, inte säkert saknad DKIM. DMARC-
alignment och faktiska SPF/DKIM-resultat måste kontrolleras i mottagarens
Authentication-Results från ett mottaget testmejl. Spam kan också bero på
rykte, innehåll, länkar, mottagarpolicy och medgivande. Kontrollerna ändrar
inte DNS, leverantörens DKIM-signering eller mottagarens spamfilter.

### Autostartreparation, bygg 2026102343
Vid första manuella start efter uppdateringen aktiveras/repareras autostart
vid användarinloggning och önskemålet sparas när OS-registrering och
inställningssparning lyckats. Öppna appen manuellt en gång efter uppdatering.
Efter denna engångsaktivering respekteras om du själv stänger av autostart
i appens inställningar. Misslyckade försök provas igen vid nästa start.
Windows-blockeringar via Autostart-appar/StartupApproved och IT-policy
kringgås inte. Status och kommando loggas på INFO i logs/app.log; misslyckad
verifiering ger varning även i errors.log. Inställningarnas autostartkontroll
visar diagnostik och möjlighet till reparation.
Appen startar alltid minimerad: systemfält om synlig bricka finns, annars
minimerad i aktivitetsfältet, oberoende av gamla start_minimized-värden.
En extra --background/--minimized-start väcker inte ett redan öppet fönster;
en andra manuell start får fortfarande visa den befintliga instansen.
VBS sätter appmappen som arbetsmapp redan före Python-kontrollen, även vid
inloggning från Windows systemmapp. Ingen EXE, Pythoninstallation eller
ändring av andra programs autostartposter görs. Faktisk inloggning på din
dator kan inte verifieras av CI-tester.
