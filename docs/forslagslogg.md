# Förslagslogg – 10 nya förslag var 10:e chattmeddelande (ej återbrukade)

Denna logg säkerställer att varje ny 10-punktslista som presenteras var 10:e chattmeddelande består av **10 helt nya, konkreta förbättringsförslag** för **E-postofferten** som **aldrig återbrukar**:
1. tidigare visade förslag i denna logg, eller
2. någon av de 50 punkterna i `docs/25-produktforslag.md` (Omgång 1 & Omgång 2) eller `docs/VAD-SAKNAS.md`.

---

## Omgång 1 (`#F01`–`#F10`) – 2026-11-24

1. **`#F01` – Kundunik Swish-QR för handpenning i HTML-offert (`::swish_qr::`)**: Platshållare som bäddar in en kundspecifik Swish-QR för bokningsavgift/handpenning märkt med ärende- eller offertnummer, helt lokalt utan extern betallänksavgift.
2. **`#F02` – "Använd som förlaga" direkt från Skicka-historik**: Högerklicksval på tidigare utskick i *Skicka-historik* som klonar mall, ifyllda fältvärden (t.ex. bilmodell/ruta) och mottagarval till ett nytt utskick med ett klick.
3. **`#F03` – Brådskandeväljare (*Normal / Express 24h / Akut stillestånd*)**: Valfri prio-nivå i Steg 1 som automatiskt lägger till rätt språkprefix (`[AKUT]` för SV, `[URGENT]` för EN) i ämnesraden och sätter standardiserad `Importance`-header.
4. **`#F04` – Utskriftsredo A4-offertkort (PDF) som valbar bilaga**: Kryssruta som utöver mejltexten genererar och bifogar ett stilrent lokalt PDF-offertblad med avsändarprofilens logotyp, specifikationer och datum.
5. **`#F05` – Automatisk bilagenamns-städare vid utskick (`IMG_4821.jpg` → `XC60-ABC123-vindruta-1.jpg`)**: Döp om kamerans generiska filnamn i själva utskicket utifrån ifylld modell/regnr/ruta medan originalfilerna på datorn förblir orörda.
6. **`#F06` – Tillbehörs- och kalibreringschecklista styrd av vald ruta (`::ruta::`)**: När t.ex. *Vindruta* väljs visas snabba kryssval för *Regnsensor, Kamera/ADAS-fäste, Värmeslingor, Akustikglas, Solkant och List/clips* som infogas strukturerat på rätt språk.
7. **`#F07` – Tidsbokningsförslag med `.ics`-kalenderfil i kundofferten**: Välj 1–3 lediga verkstadstider så bifogas en standardiserad `.ics`-fil som kunden kan spara direkt i sin kalender.
8. **`#F08` – Kontrastkontroll för mörkt läge i HTML-mallar och signaturer**: Förhandsvarning om text- eller logotypfärger i en HTML-mall ger för låg kontrast när mottagaren läser mejlet i Outlook/Apple Mail Dark Mode.
9. **`#F09` – Tillfälliga bockrutor för att hoppa över enskild kontakt i en grupp**: Avmarkera snabbt 1–2 mottagare ur en vald grupp inför ett specifikt utskick utan att ändra den sparade gruppens medlemslista.
10. **`#F10` – Lokal månadsöversikt per glastyp, bilmodell och avsändarprofil**: Sammanställning ur den lokala historiken över vanligaste glastyperna, språken och profilerna med export till CSV/HTML.
