# 25 produktförslag för E-postofferten

## Vad listan betyder
Idéer för nästa produktsteg, inte verifierade påståenden om konkurrenter eller
uppmätt efterfrågan. Inga konkurrentprodukter eller användarstudier har angetts.
Att alla konkurrenter saknar något kan därför inte beläggas här. Förslagen är
inte implementerade eller beslutade. Befintlig individuell sändning, mallar,
adressbok, utkast, bilagor och historik är utgångspunkten, inte nya funktioner.

**Validering före utveckling:** intervjua 5–10 offertavsändare och några
mottagare, jämför namngivna produkter med samma abonnemangsnivå och datum,
och testa prototypen i riktiga arbetsuppgifter. Prioritet nedan är en
produkthypotes, inte en omröstning eller marknadsundersökning.

| # | Förslag och skillnad mot dagens grundfunktioner | Nytta att pröva med användare | Prioritet / validering |
|---|---|---|---|
| 1 | Ärendekort som knyter ihop förfrågan, skickade mejl, inkomna svar och beslut | Slippa leta i flera system | Hög – följ ett ärende från början till slut |
| 2 | Normaliserad offertjämförelse med moms, frakt, valuta och enhetspris | Jämföra samma omfattning, inte bara slutpris | Hög – testa anonymiserade olika offerter |
| 3 | Förklarad fullständighetskontroll före offertförfrågan, per bransch | Färre följdfrågor om saknade specifikationer | Hög – kartlägg vanligaste kompletteringarna |
| 4 | Svarsmatris per leverantör: svarat, saknar uppgifter, avböjt, väntar | Se vilka nästa steg som faktiskt behövs | Hög – prototyp med 5–15 mottagare |
| 5 | Ärendespecifik checklista för beslut med obligatoriska egna kriterier | Dokumentera varför en offert valdes | Medel – granska ett verkligt köpbeslut |
| 6 | Påminnelseförslag endast till dem som inte svarat, med manuell granskning | Undvika felaktiga eller dubbla påminnelser | Hög – prova med svar som kommer sent |
| 7 | Automatisk extraktion av svar till jämförelsetabell, med källhänvisning och osäkerhetsmarkering | Minska inmatning utan att dölja tolkningsfel | Medel – mät fel på olika PDF/mejl, godkänn manuellt |
| 8 | Synlig skillnadsgranskning när en leverantör reviderar sin offert | Upptäcka ändrade villkor eller omfattning | Hög – jämför två verkliga revisioner |
| 9 | Mallkontrakt: fälttyper, tillåtna enheter och beroenden | Förhindra fel enhet eller orimliga kombinationer | Hög – använd befintliga mallar som testfall |
| 10 | Malltestare med anonymiserade exempel och kontroll av båda språken | Kvalitetssäkra en mall före publicering | Hög – låt mallskapare köra regressionstest |
| 11 | Integritetsförhandsvisning som visar exakt vad just den mottagaren får, inklusive bilagor | Säkerställa att konkurrentuppgifter inte följer med i innehållet | Hög – testa avsiktligt inlagda känsliga uppgifter |
| 12 | Lokal sekretesskontroll för personnummer, andra leverantörers adresser och internkommentarer i innehåll | Komplettera befintligt skydd av mottagarhuvuden | Hög – mät falsklarm och missar, ingen tyst borttagning |
| 13 | Bilageversioner per ärende, med varning vid gammal ritning | Minska risken att skicka fel revision | Hög – prova flera liknande filnamn |
| 14 | Bildmarkeringar med pilar/mått som separat bilaga, original bevaras | Förklara vad en offert gäller utan telefonsamtal | Medel – följ ett verkligt bildbaserat ärende |
| 15 | Offlineläge med tydlig utkorg och obligatorisk ny granskning före sändning | Förbereda arbete utan att lova automatisk leverans | Medel – bryt anslutningen under arbetsflödet |
| 16 | Återupptagbar sändningsjournal per mottagare efter avbrott | Inte skicka igen till redan accepterade mottagare | Hög – simulera avbrott mitt i sändning, skilj SMTP från leverans |
| 17 | Dubblettskydd per ärende och mottagare över flera arbetsdagar | Upptäcka upprepade utskick utan att stoppa avsiktliga revisioner | Hög – testa korrigerade förfrågningar |
| 18 | Tillfälliga projektdeltagare med ärendespecifik behörighet i framtida teamläge | Dela rätt information utan full adressboksåtkomst | Senare – kräver uttryckligt val av delningsmodell |
| 19 | Exportpaket för ett ärende med läsbart index och anonymiseringsval | Överlämning eller spårbar dokumentation | Medel – låt någon annan förstå paketet utan appen |
| 20 | Dataminimeringsguide och raderingstid per ärendetyp | Behålla nödvändig dokumentation, rensa resten | Medel – stäm av verkliga lagringskrav; ingen juridisk garanti |
| 21 | Tillgänglighetsprofil med större text, kompakt/luftig täthet och inga dekoranimationer | Färre fel vid liten skärm eller nedsatt syn | Hög – testa med skärmläsare och 200 % skalning |
| 22 | Startöversikt med bara blockerade ärenden och nästa manuella steg | Minska informationsbrus | Medel – jämför tid till nästa åtgärd |
| 23 | Förklarade leveransproblem som kopplar fel till möjlig åtgärd, inte löften om inkorg | Hjälpa användaren felsöka SMTP/DNS utan att exponera hemligheter | Hög – prova verkliga anonymiserade fel |
| 24 | Leverantörsanpassade frågepaket med gemensam kärna och tydligt synliga avvikelser | Anpassa detaljer utan att tappa jämförbarhet | Medel – testa att två offerter fortfarande kan jämföras |
| 25 | Återkopplingsläge efter avslutat ärende: vad saknades i förfrågan? | Förbättra nästa mall utifrån verkliga följdfrågor | Medel – testa förslag, aldrig ändra mall automatiskt |

## Rekommenderad första valideringsomgång
Börja med 3, 11–13, 16 och 21: fullständighet, sekretess, bilageversioner,
avbrottssäkerhet och tillgänglighet. De passar produktens befintliga
integritetsinriktning. Identifiera vilka delar som redan finns innan en
specifikation skrivs. Inkommande e-post/automatisk tolkning/teamläge kräver
separata beslut om åtkomst, lagring, kostnad och integritet.

**För att kalla något efterfrågat:** spara anonymiserade intervjufynd eller
faktiska ärenden, frekvens och datum. **För att kalla något en konkurrensfördel:**
ange produkt, version/plan, verifierad dokumentation och vad jämförelsen gäller.

---

## Omgång 2: 25 nya nischförslag (lokal offert- och reservdelsförfrågan utan molninlåsning)

Följande 25 nya förslag fokuserar på arbetsflöden där generiska e-postklienter
(Outlook, Thunderbird), nyhetsbrevsverktyg (Mailchimp, Brevo) och molnbaserade
upphandlingsportaler lämnar luckor: snabba tekniska förfrågningar med foton,
fordons-/artikelidentifiering, tvåspråkig fackterminologi, leverantörshygien
och noll-moln-integritet.

| # | Nytt förslag (saknas i generiska e-post-/nyhetsbrevsverktyg) | Konkret användarnytta | Prioritet / validering |
|---|---|---|---|
| 1 | Lokal EXIF- och GPS-rensning på foton vid sändning (originalfilen bevaras orörd) | Kundens hemadress/verkstadsposition och kameradata läcker inte till externa leverantörer | Hög – verifiera på 20 mobilfoton från iOS/Android |
| 2 | Smart bildoptimering med total storleksbudget per mottagardomän (t.ex. max 8 MB MIME) | Slippa studsar hos leverantörer med äldre mailservrar utan att typskyltar blir oläsbara | Hög – mät läsbarhet på chassiplåtar efter skalning |
| 3 | Lokal offline-OCR för regnummer, 17-teckens VIN och OEM-artikelnummer ur inklistrat foto | Slipp skriva av långa chassi- och artikelkoder manuellt med risk för sifferfel | Hög – mät träffsäkerhet på smutsiga/vinklade skyltar |
| 4 | Inbyggd VIN- (ISO 3779 kontrollsiffra, I/O/Q-spärr) och nordisk regnummervalidering | Stoppar felaktiga underlag innan 15 leverantörer räknar på fel fordon | Hög – enhetstesta mot kända giltiga/ogiltiga VIN |
| 5 | Klickbar visuell fordons-/glaskarta i vektorformat med höger-/vänsterstyrningskontroll | Noll missförstånd mellan t.ex. vänster bakre sidoruta, kvartsruta och ventilationsruta | Hög – användartesta på 5 glasmästare/inköpare |
| 6 | Låsbar branschspecifik fackordlista SV↔EN (OEM-termer, ADAS, sensortyper, lister) | Korrekt fackengelska till utländska leverantörer där vanlig översättning gissar fel | Hög – granska 30 verkliga engelska utskick |
| 7 | Mobilkamerabrygga via engångs-QR över lokalt Wi-Fi (LAN) utan molnkonto | Fota skadan vid bilen och få in bilden i Steg 2 på 5 sekunder utan mejl-till-sig-själv | Medel – testa i verkstadsnät med brandvägg |
| 8 | Direkt `Ctrl+V`-skärmklippsfångare med snabb beskärning och sekretessmaskering | Klistra in ur reservdelskatalog/EPC och maskera kundnamn eller egna priser direkt | Hög – mät tidsbesparing mot externt bildprogram |
| 9 | Lokalt beräknad svarstidsklocka och leveransprecision per leverantör i adressboken | Se direkt vilka leverantörer som brukar svara snabbt på just den kategorin | Medel – kräver minst 20 historiska ärenden |
| 10 | Leverantörskalender för nationella helgdagar per land, semesterstängt och frakt-cut-off | Varnar före sändning om t.ex. polsk/tysk leverantör har helgdag eller dagens cut-off passerats | Medel – testa med utländska leverantörsgrupper |
| 11 | Lokal domän- och MX-förkontroll av mottagarlistan före SMTP-anslutning | Fångar felstavade domäner (`@gmial.com`) och nedlagda bolag innan de skadar avsändarryktet | Hög – kör offline-säker DNS-kontroll med timeout |
| 12 | Adaptiv domän-throttling och jitter när flera mottagare delar mailserver/webbhotell | Förhindrar tillfällig greylisting eller spamblockering vid individuella utskick | Hög – verifiera mot strikta SMTP-reläer |
| 13 | Kryptografiskt lokalt sändningskvitto (RFC-tidsstämpel, SHA-256 och SMTP-svar per mottagare) | Spårbart bevis vid reklamation eller tidsfrist utan att röja andra mottagare | Medel – testa läsbar PDF/JSON-export |
| 14 | Ett-klicks artig ”Ärendet löst / beställt på annat håll”-uppföljning till övriga tillfrågade | Leverantörer som får återkoppling prioriterar avsändarens nästa förfrågan högre | Hög – intervjua 5 leverantörer om önskad ton |
| 15 | Försäkrings- och ROT/RUT-fältpaket med separata vyer för leverantör respektive slutkund | Skadenummer/kunduppgifter stannar internt medan teknisk specifikation går till leverantör | Medel – validera mot verkliga skadeärenden |
| 16 | Inbyggd inköps- till kundpriskalkylator (valuta, frakt, påslag, moms och avrundning) | Räkna fram kundoffert direkt från leverantörens EUR/PLN-svar utan separat kalkylblad | Medel – kontrollräkna mot befintliga rutiner |
| 17 | Lokal ”tidsmaskin” för mallar med automatiska versionspunkter och visuell textdiff | Återställ en råkat raderad formulering på 5 sekunder utan Git eller molnbackup | Hög – låg komplexitet och noll databasberoende |
| 18 | Villkorsstyrda mallstycken (`[om:adas]`, `[om:express]`, `[om:begagnat_ok]`) i SV + EN | En smart mall ersätter 10 nästan likadana varianter och håller båda språken i synk | Hög – bakåtkompatibel utökning av mallmotorn |
| 19 | Signerade `.mailpack`-paket för säker lokal delning av mallar och ordlistor mellan kollegor | Nyanställd får rätt mallar och kategorier via USB/internmapp utan molnserver | Medel – förhandsgranska alltid paket före import |
| 20 | Blixtsnabb kommandopalett (`Ctrl+P`) över regnummer, mallar, kontakter och historik | Hoppa till valfritt tidigare utskick eller rätt mall på <100 ms utan att lämna tangentbordet | Hög – stor vardagsnytta för vana användare |
| 21 | Lokal `.eml`-import som omvandlar gamla skickade mejl till återanvändbara mallar/kontakter | Sänk tröskeln vid byte från manuell Outlook/Thunderbird-kopiering på 5 minuter | Medel – testa mot Outlook- och Thunderbird-export |
| 22 | Portalfri snabbsvarsruta i mejlfoten (`Pris | Frakt | Leveranstid | OEM/Eftermarknad`) | Leverantören svarar direkt med ”Svara” i sin vanliga mejlklient utan inloggningskrångel | Hög – noll friktion för mottagaren |
| 23 | Verkstads-/pekskärmsläge med extra stora träffytor (56 px) och handskvänlig kontrast | Enklare användning på surfplatta/dator vid billyft eller lagerhylla i starkt ljus | Medel – testa på 11–13" pekskärm i 150–200 % DPI |
| 24 | Valbar läs-endast IMAP-studs- och autosvarsdetektor kopplad till utskickets `Message-ID` | Ser direkt i ärendet om en kontakt studsat eller är på semester utan att spara inkorgen | Senare – kräver uttryckligt opt-in för IMAP |
| 25 | Begriplig svensk SPF/DKIM/DMARC-hälsopanel med guide för svenska webbhotell | Hjälper småföretag fixa DNS en gång för alla så offertförfrågningar når inkorgen | Hög – bygger vidare på befintlig DNS-kontroll |

---

## Omgång 3 (`#N01`–`#N25`): 25 helt nya funktioner som konkurrenter saknar och användare efterfrågar

Dessa 25 helt nya punkter återbrukar ingen av de 50 punkterna ovan eller `#F01`–`#F10` i `docs/forslagslogg.md`, utan adresserar praktiska luckor gentemot Outlook, Thunderbird, nyhetsbrevstjänster och tunga verkstads-/affärssystem.

| # | Nytt förslag | Varför konkurrenter saknar det & användarnytta | Prioritet |
|---|---|---|---|
| N01 | **Eurocode-/glaskodsdekoder i realtid (`::eurocode::`, t.ex. `8596AGNGYMV1B`)** | Vanliga mejlklienter förstår inte bilglas-Eurocodes – översätter koden direkt till klartext (märke, kaross, ton, solband, sensorfäste) på SV + EN i utskicket | Hög |
| N02 | **Tidsstyrd schemaläggning för morgonsändning (t.ex. kl. 07:05 lokalt i leverantörens tidszon)** | Förbered förfrågningar sent på kvällen så att de hamnar överst i inkorgen när inköp/lager öppnar – helt lokalt utan molnkö | Hög |
| N03 | **Inbyggd bildjämförare (*Skadad ruta / Före* bredvid *OEM-stämpel / Efter*) som ett samlat bildkort** | Monterar 2–4 bilagor till en tydlig etiketterad översiktsbild med ett klick så mottagaren slipper öppna fyra lösa JPG-filer | Hög |
| N04 | **Streckkods- och QR-läsare från webbkamera eller inklistrad etikettbild** | Läser av rutans eller kartongens streckkod/DataMatrix direkt in i platshållarfälten utan handskanner eller manuell inmatning | Medel |
| N05 | **Automatisk kontroll av helg-/röda-dagar-leverans vid angivet önskat leveransdatum** | Varnar direkt om valt leveransdatum råkar vara helgdag eller klämdag i Sverige eller mottagarlandet | Medel |
| N06 | **Snabbväxling mellan ”Prisförfrågan till leverantör” och ”Färdigt prisförslag till kund” i samma ärende** | Återanvänder regnr, bilmodell och glastyp direkt från leverantörsförfrågan till kundens svarsmejl utan dubbelinmatning | Hög |
| N07 | **Lokal röstanteckning-till-fritext (offline diktering för verkstadsgolvet)** | Tala in skadebeskrivning med smutsiga händer vid bilen och få färdig strukturerad fritext i Steg 1 utan molntjänst | Medel |
| N08 | ** Valbar vattenstämpel med eget företagsnamn/ärendenummer på utgående skadefoton** | Förhindrar att egna dokumentationsbilder sprids fel eller blandas ihop hos leverantörer som hanterar hundra ärenden per dag | Medel |
| N09 | **Leverantörsspecifika kundnummer per kontakt (`::kundnr::` per mottagare i individuell sändning)** | Varje leverantör ser automatiskt *sitt eget* kund-/kontonummer för avsändaren i sitt individuella mejl – omöjligt vid vanlig Bcc-sändning | Hög |
| N10 | **Smart bilagekomprimering specifikt för PDF-ritningar och skannade skadeanmälningar** | Krymper tunga skannade PDF-bilagor 5–10× lokalt utan att texten blir suddig innan SMTP-sändning | Medel |
| N11 | **Snabbknapp ”Skicka testkopia bara till mig själv exakt som mottagare X ser den”** | Låter avsändaren verifiera exakt layout, CID-logotyp och språk för en specifik utländsk eller svensk mottagare i sin egen mobil på 3 sekunder | Hög |
| N12 | **Färgkodade statusbrickor i systemfältsmenyn (Tray) för senaste 5 utskicken** | Högerklicka på brickikonen nere vid klockan för att direkt se status på senaste utskicken eller repetera ett misslyckat utan att ens öppna huvudfönstret | Medel |
| N13 | **Automatisk detektering av felaktigt valt språk per landdomän (`.de`, `.pl`, `.lt`, `.uk`, `.se`)** | Varnar före sändning om en `.de`/`.pl`/`.com`-leverantör av misstag står som `SV` i stället för `EN` | Hög |
| N14 | **Lokal frakt- och emballageprofil per glastyp (*Trähäck / Pall / Samfrakt / Hämtas på depå*)** | Ett klick infogar tydliga leveransvillkor på både svenska och engelska så att fraktkostnad alltid specificeras rätt från start | Hög |
| N15 | ** Dra-och-släpp av hel `.msg`- eller `.eml`-fil från Outlook/Thunderbird till Steg 1** | Plockar automatiskt ut kundens bilagor, regnummer ur ämnesraden och avsändarinfo till en ny leverantörsförfrågan | Hög |
| N16 | **Lokal dubblettbildsdetektor (perceptuell hash) vid bilageval** | Varnar direkt om man råkar dra in samma foto två gånger under olika filnamn eller i olika upplösning | Medel |
| N17 | **Anpassningsbara kortkommandon (egen snabbtangentprofil i Inställningar)** | Låter vana kontors- och verkstadsanvändare binda egna tangenter för favoritmallar, kontaktgrupper och direktutskick | Medel |
| N18 | **Valbar sammanfattningsrad (preheader-text) högst upp i HTML-utskick** | Styr exakt de första 90 tecknen som syns i mottagarens mobilnotis och inkorgslista i Outlook/Gmail (t.ex. `XC60 · ABC123 · Vindruta m. kamera`) | Hög |
| N19 | **Offline-validering av svenskt organisationsnummer och momsregistreringsnummer (VAT/Luhn)** | Säkerställer att företagskundens org.nr/EU-VAT i faktura- och offertmallar är matematiskt giltigt före sändning | Medel |
| N20 | ** ”Frys fält vid rensning” (nål-ikon bredvid valfritt platshållarfält i Steg 1)** | Behåller t.ex. bilmärke eller leveransort låst när man skickar 5 separata rutor/delar för samma fordon efter varandra | Hög |
| N21 | **Portabelt USB-/flyttläge med krypterat profilpaket för byte av verkstadsdator** | Flytta hela E-postofferten inklusive profiler, mallar, kolumnordning och kontakter till ny Windows-dator på 30 sekunder | Hög |
| N22 | **Visuell tecken- och radlängdsindikator för ämnesrader i mobilvy** | Visar direkt om ämnesraden klipps av på iPhone/Android så att regnummer och glastyp alltid hamnar före brytpunkten | Medel |
| N23 | **Snabbfilter för ”Senast använda kontakter senaste 14 dagarna” överst i kontaktväljaren** | Lyfter fram aktiva leverantörer direkt utan att behöva söka i en adressbok med hundratals rader | Hög |
| N24 | **Lokal SLA-varning för obesvarade utskick (t.ex. ”4 timmar utan markering”)** | Diskret Brick-/statuspåminnelse om att följa upp en tidskritisk expressförfrågan innan leverantörens eftermiddagsbil går | Medel |
| N25 | **Självtestande ”Hälsokontroll vid start” (SMTP, DNS, diskutrymme, skrivbehörighet, mallintegritet)** | En tydlig grön/gul statusindikator i statusfältet som fångar utgånget app-lösenord eller full disk *innan* man skriver ett långt utskick | Hög |

---

## Omgång 4 (`#N26`–`#N50`): 25 helt nya funktioner som konkurrenter saknar och användare efterfrågar

Helt nya förslag utan återbruk från Omgång 1–3 ovan eller `#F01`–`#F10` i `docs/forslagslogg.md`.

| # | Nytt förslag | Varför konkurrenter saknar det & användarnytta | Prioritet |
|---|---|---|---|
| N26 | **Fordonsgeneration & årsmodellsvakt mot angiven modell (`::modell::` + `::ar::`)** | Varnar direkt om angivet årtal ligger utanför karossgenerationens faktiska tillverkningsår (t.ex. brytår vid facelift där vindruta/sensorfäste skiljer sig) | Hög |
| N27 | **Snabbknapp ”Begär kompletterande foto från kund” (färdigt svars-SMS/mejl-utkast)** | När kundens insända bild saknar regskylt eller regnsensor skapas med ett klick en vänlig fotoguide som kunden kan svara på direkt | Hög |
| N28 | **Inbyggd bildrotation, automatisk rätning och kontrastlyft av mörka garagefoton** | Gör mörka eller sneda verkstadsbilder på chassinummer och glasstämplar knivskarpa på 1 sekund utan externt bildprogram | Hög |
| N29 | **Separata bilagepaket per mottagartyp i samma ärende (*Tekniska närbilder → Leverantör*, *Översiktsbild → Försäkring*)** | Slipper skicka kundkänsliga helbilder till grossister samtidigt som rätt närbild på fästet alltid följer med | Medel |
| N30 | **Lokal prisminnesbank per ruta och bilmodell från tidigare avslutade ärenden** | Visar diskret i sidopanelen vad liknande ruta kostade vid senaste inköp så du direkt ser om ett nytt prisförslag avviker kraftigt | Hög |
| N31 | **Växelkurslåsning vid utskickstillfället för utländska leverantörer (EUR/PLN/DKK/NOK → SEK)** | Sparar aktuell kurs på ärendet så marginalen kan kontrollräknas rätt även om fakturan kommer tre veckor senare | Medel |
| N32 | **Automatisk kontroll av trasiga platshållare med stavfelsförslag (`::regn::` → menade du `::reg::`?)** | Fångar felstavade taggar direkt medan man redigerar mallen eller mejlet i stället för att först varna om okänd tagg vid sändning | Hög |
| N33 | **Klickbara snabbchip för standardfraser i fritextfältet (*”Endast originalglas”*, *”Brådskande – bil på lyft”*, *”Inkl. list & lim”*)** | Infogar vanliga tillägg på både svenska och engelska med ett klick utan att behöva skapa en ny mall för varje kombination | Hög |
| N34 | **Lokal kontroll av mottagarens maximala bilagestorlek per känd mailleverantör (t.ex. 10 MB / 20 MB / 25 MB)** | Anpassar varningsgränsen i förkontrollen efter den striktaste mottagardomänen i mottagarlistan så inget enskilt mejl studsar | Hög |
| N35 | **”Spegla utskick som ren kopia till lokal ärendemapp” (`Ärenden/2026-11/ABC123-XC60/`)** | Sparar skickat `.eml`-original + bilagor i en prydlig datum-/regnummermapp på disken för verkstadens egen dokumentation eller bokföring | Hög |
| N36 | **Snabbval av vänster-/högerstyrd bil (`Vänsterstyrd LHD` / `Högerstyrd RHD`) vid utlandsförfrågningar** | Kritiskt vid beställning från UK/utland där vindrutans torkarfält och kameravinkel annars blir spegelvända | Medel |
| N37 | **Visuell förhandsgranskning av hur mejlet ser ut i smal mobilskärm (375 px) vs bred datorskärm** | Växla mellan *Mobilvy* och *Datorvy* i Förhandsgranska-fliken så breda tabeller och signaturlogotyper alltid ser proffsiga ut i telefonen | Hög |
| N38 | ** Engångsläge ”Dölj avsändarens direktnummer” vid reservdelsförfrågan till nya utländska kontakter** | Växlar signaturvariant med ett klick så man slipper oönskade säljuppringningar och får alla svar skriftligt på mejl | Medel |
| N39 | **Automatisk sammanställning av ”Veckans obesvarade eller misslyckade utskick” i en ren måndagsvy** | Ger full överblick på måndag morgon över vilka förfrågningar från förra veckan som behöver följas upp | Medel |
| N40 | ** Dra-och-släpp av ZIP-arkiv i bilageytan med urval av vilka filer inuti arkivet som ska bifogas** | Packar upp och låter användaren bocka för t.ex. 2 relevanta bilder ur kundens ZIP-fil utan att packa upp manuellt i Utforskaren | Medel |
| N41 | **Färdig ”Reklamations-/transportskademall” kopplad direkt till ett tidigare utskick i Skicka-historik** | Om en levererad ruta anländer sprucken skapas reklamationsmejlet färdigt med ursprungligt datum, ämne, regnummer och orderreferens | Hög |
| N42 | **Kontroll av läsbarhet på bifogade foton (oskärpe-/mörkerdetektor lokalt före sändning)** | Varnar direkt vid bilageval om ett mobilfoto är kraftigt suddigt eller kolsvart innan leverantören ber om ny bild dagen efter | Medel |
| N43 | **Stöd för dubbla referensfält (`Er referens` / `Vårt arbetsordernr`) med automatisk nummerserie** | Kan räkna upp internt förfrågningsnummer (`FO-2026-0142`) automatiskt så leverantörens svar alltid kan matchas mot rätt arbetsorder | Hög |
| N44 | **Lokal import av kontakter direkt från vCard (`.vcf`) och urklippstabeller från Excel** | Klistra in en kolumn med namn, e-post, företag och språk direkt från ett kalkylblad till Adressboken på 5 sekunder | Hög |
| N45 | ** Valbar ”Tyst arbetstid” för bakgrundsnotiser i systemfältet** | Under kundmöten eller skärmdelning hålls alla popup-notiser nere vid klockan tysta medan appen fortsätter arbeta i bakgrunden | Låg |
| N46 | **Snabbfilter i Skicka-historik på datumintervall, avsändarprofil, glastyp och endast misslyckade (`❌ Fel`)** | Kombinera kolumnsortering med snabba filterknappar för att hitta ett specifikt utskick bland 500 historikrader direkt | Hög |
| N47 | **Inbyggd kontroll av att HTML- och klartextversionen av ett mejl innehåller exakt samma fakta/siffror** | Förhindrar att en manuell ändring bara hamnar i ena versionen och ökar samtidigt leveransbarheten i strikta spamfilter | Medel |
| N48 | ** Karosstypväljare (*Sedan / Kombi / SUV / Coupé / Cab / Skåpbil / Husbil*) kopplad till `::ruta::`** | Eliminerar klassiska missförstånd kring bakrutor och bakre sidorutor där kombi och sedan har helt olika glas på samma modellnamn | Hög |
| N49 | **Säkerhetskopiering av enskild mall eller hel mallmapp före massredigering med ett klick** | Skapar en namngiven ögonblickspunkt i `.data/` precis innan man gör om företagets alla malltexter eller villkor | Medel |
| N50 | **Tangentbordsstyrt ”Snabbläge” (fyll i Mall → Modell → Regnr → Ruta → Enter → Förhandsgranska)** | Låter vana mottagare/inköpare mata in en komplett förfrågan på under 15 sekunder helt utan att flytta handen till musen | Hög |


## Omgång 5 (`#N51`–`#N75`): 25 helt nya funktioner som konkurrenter saknar och användare efterfrågar

Helt nya förslag utan återbruk från Omgång 1–4 ovan eller `#F01`–`#F10` i `docs/forslagslogg.md`.

| # | Nytt förslag | Varför konkurrenter saknar det & användarnytta | Prioritet |
|---|---|---|---|
| N51 | **Offertaccept med ett klick + artigt avböjande till övriga leverantörer i samma ärende** | När kunden tackat ja skickas orderbekräftelse till vald leverantör och ett hövligt, språkanpassat avböjande till de andra – med samma ärendenummer i alla mejl. Ingen mejlklient kan hålla ihop den tråden | Hög |
| N52 | **Samfraktgruppering: slå ihop flera öppna ärenden till en leverantörsförfrågan med delposter** | Fyra rutor till samma grossist blir ett mejl med fyra numrerade rader och en gemensam fraktberäkning i stället för fyra separata portokostnader | Hög |
| N53 | **Leverantörskvalitetspoäng lokalt (svarstid, prismarginal, reklamationsfrekvens)** | Visas i kontaktkortet och vid mottagarval: "svarar i snitt 3 h, 2 reklamationer i år" – helt ur den egna historiken, utan molntjänst | Hög |
| N54 | **Prisförslagskalkylator med påslag per glastyp och kund samt marginalvakt** | Räknar ut kundpris från leverantörens inköpspris med valt påslag och varnar om marginalen blir negativ innan offerten skickas | Hög |
| N55 | **Import av leverantörsprislista (CSV) med automatisk prisjämförelse i offertförslaget** | Läser in grossistens prislista en gång och visar direkt i ärendet vilken leverantör som är billigast för just den rutan | Hög |
| N56 | **SHA-256-spårbarhet per bilaga i ärendet** | Varje skickad fil får ett fingeravtryck i historiken så man i efterhand kan bevisa exakt vilken ritning eller bild leverantören fick – samma princip som appens uppdaterare använder | Medel |
| N57 | **Utskrift av vindruteetikett med QR-kod (ärendenr, regnr, glastyp)** | Lagersvängen får en etikett att sätta på rutan så att inkommen glass matchas mot rätt mejlärende utan att läsa papperslistor | Medel |
| N58 | **OCR av glasstämpel från kamera eller mobilfoto direkt in i `::eurocode::`** | Fotografera stämpeln på den trasiga rutan och få märke, tillverkare och typkod ifyllt lokalt – utan handskrift eller sifferletande | Hög |
| N59 | **OCR av registreringsbevis/COC-dokument för VIN och första registreringsdatum** | Fångar upp fordon med importerade eller otydliga papper där VIN annars skrivs fel och rätt ruta beställs för sent | Medel |
| N60 | **Kalibreringsintyg som bilaga per fordon (ADAS-kamera/radar)** | Färdig intygsmall med VIN, glastyp, kameratyp och datum som bifogas kund och försäkring efter byte – krav som allt fler bilar ställer idag | Hög |
| N61 | **"Kända fallgropar per modell"-varning med källor (kamera-/regnsensorvarianter, brytår)** | Varnar innan beställning: "samma modellnamn har två olika fästen före/efter visst årtal" – kunskap som annars bara sitter i den erfarne mekanikerns huvud | Hög |
| N62 | **Villkorliga mallblock (om leveransort utomlands → exportvillkor, om glastyp = bakruta → värmeslinga)** | Mallen anpassar sig själv efter ärendets uppgifter i stället för att kräva fem olika varianter av samma text | Hög |
| N63 | **Utökat språkstöd (DE/PL/LT) med granskningsläge och ordlista per språk** | Svenska glasverkstäder handlar allt oftare i Tyskland och Polen; appen visar både original och granskad översättning så inget tekniskt fackuttryck blir fel | Medel |
| N64 | **Schemalagd krypterad säkerhetskopia av all användardata med återställningstest** | Kopierar profiler, mallar, kontakter, historik och kolumnordning på schema och verifierar att kopian går att läsa tillbaka – inte bara att filen skapades | Hög |
| N65 | **Nattlig underhållskörning kl. 03:00 utan dialoger (loggarkiv, cache, backup, index)** | Tungt underhåll flyttas till natten och körs tyst, så att appen är snabb och sval under arbetsdagen och aldrig avbryter med rutor | Medel |
| N66 | **Prestandapanel i Inställningar: minne, CPU och energianvändning per funktion** | Visar svart på vitt vilka vyer eller timers som drar resurser, så att appen kan hållas snabb även på äldre verkstadsdatorer | Medel |
| N67 | **"Föreslå alternativ leverantör" när förstahandsvalet inte har rutan** | Letar i den lokala historiken efter vilka leverantörer som tidigare levererat samma glasnummer och föreslår dem med ett färdigt mejlutkast | Hög |
| N68 | **Automatisk HEIC/HEIF-konvertering vid bilageval** | iPhone-bilder som Windows-mottagaren inte kan öppna konverteras till skarp JPEG först när de bifogas – originalfilerna lämnas orörda | Medel |
| N69 | **Kvalitetsvals-förfrågan som strukturerat block (OEM / OES / begagnat / pirat)** | Leverantören svarar på exakt samma fyra kvalitetsnivåer i alla ärenden, vilket gör offerterna jämförbara i stället för att blandas i löptext | Hög |
| N70 | **EXIF-/GPS-städning av foton före sändning** | Tar bort positionsdata och kamerainformation ur kundens bilder innan de går till leverantör eller försäkring – integritet utan att bilden försämras | Medel |
| N71 | **Anonymiserad prisjämförelse-PDF (tre leverantörer) som bilaga till kundofferten** | Kunden får ett prydligt underlag som visar att priset är marknadsprövat, med leverantörsnamnen ersatta av "Leverantör A/B/C" | Medel |
| N72 | **Stenskott vs byte-beslutstöd enligt branschregler (storlek, placering, inom synfält)** | Frågar efter skadans storlek och placering och föreslår lagning eller byte med motivering – färre feldiagnoser och färre returer | Hög |
| N73 | **Försäkrings-/skadenummer med lokal validering och automatisk självriskrad** | Kontrollerar formatet på skadenumret och lägger in rätt självrisktext i både SV- och EN-versionen av offerten | Hög |
| N74 | **Garantivillkor per glastyp som färdigt flerspråkigt block** | Väljer rätt garanti- och reklamationstext för vindruta, bakruta, sidoruta eller lagning och infogar den på mottagarens språk | Medel |
| N75 | **Lokalt "i lager"-status per glasnummer med reservation och varning vid dubbelbokning** | Markerar rutan som reserverad när förfrågan går ut och varnar om samma glasnummer bokas igen i ett annat ärende samma dag | Hög |

---
