# Förslagslogg – 10 nya förslag var 10:e chattmeddelande (ej återbrukade)

Denna logg säkerställer att varje ny 10-punktslista som presenteras var 10:e chattmeddelande består av **10 helt nya, konkreta förbättringsförslag** som **aldrig återbrukar**:
1. tidigare visade förslag i denna logg (`#F01` och framåt), eller
2. befintliga punkter i `docs/25-produktforslag.md` (50 st) och `docs/VAD-SAKNAS.md`.

---

## Omgång 1 (`#F01`–`#F10`) – 2026-11-24

1. **`#F01` – Läs-endast IMAP-svarsdetektering**: Valfri IMAP-kontroll som matchar inkommande mejlsvar (`In-Reply-To` / `References`) mot skickade förfrågningar och markerar direkt i *Skicka-historik* vilka leverantörer eller kunder som har svarat.
2. **`#F02` – Inköps- och prisjämförelsekort per förfrågan**: Koppla inkomna leverantörspriser, frakt och leveranstid till ett utskick i historiken och visa direkt billigaste respektive snabbaste alternativet.
3. **`#F03` – Snabb bilduppmärkning (pil & inringning) i steg 2**: Inbyggt miniverktyg i *Bilagor/Bilder* för att markera stenskott, spricka, regnsensorfäste eller skada med pil/cirkel direkt på bilden före sändning.
4. **`#F04` – Automatisk EXIF- och GPS-rensning på fotobilagor**: Ta bort GPS-koordinater och kamerametadata ur kund- och verkstadsfoton innan de skickas till externa leverantörer.
5. **`#F05` – Klistra in skärmklipp direkt som bilaga (`Ctrl+V`)**: Stöd för att klistra in bilder direkt från urklipp (`Win+Shift+S` → `Ctrl+V` i bilagelistan) med automatiskt tidsstämplat filnamn.
6. **`#F06` – Landskalender & helgdagsnotis för utländska mottagare**: Visa en diskret varning före sändning om valda mottagares land (t.ex. DE, PL, NL, UK) har nationell helgdag idag så leveranstidsförväntan blir rätt.
7. **`#F07` – Kundunik Swish-QR för handpenning i HTML-offert (`::swish_qr::`)**: Platshållare som genererar en inbäddad Swish-QR för valfri handpenning/bokningsavgift märkt med kundens offertnummer.
8. **`#F08` – Lokal spamfilters- och teckenkontroll före utskick**: Förhandskontroll som poängsätter ämnesrad, HTML/text-balans, versalgrad och trasiga specialtecken för maximal leveransbarhet utan molntjänst.
9. **`#F09` – "Använd som förlaga" direkt från Skicka-historik**: Högerklicksval i historiken som klonar mall, ifyllda fältvärden och mottagarval till ett nytt utskick med ett klick.
10. **`#F10` – Brådskandeväljare (*Standard / Express 24h / Akut stillestånd*)**: Valfri prio-etikett i steg 1 som sätter rätt språkprefix (`[AKUT]` / `[URGENT]`) per mottagarspråk samt standardiserade e-postheaders (`Importance`).
