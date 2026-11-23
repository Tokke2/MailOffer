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
