# E-postofferten – redigerbara tryckoriginal (vektor)
© 2026 Rickard Längkvist.

Denna mapp ingår direkt i appens vanliga GitHub-release (Source code ZIP).
Inget separat grafikpaket behöver laddas ned.

## Filer i `tryck/`
- `E-postofferten-farg.svg` — horisontell logotyp i 100 % plana solida färger (utan gradienter, filter, strokes eller transparens), `180 × 45 mm` (`viewBox="0 0 1280 320"`).
- `E-postofferten-svart.svg` — horisontell 1-färgs svart/vit variant för ljust underlag, stämpel, gravyr och screentryck, `180 × 45 mm`.
- `E-postofferten-symbol.svg` — fristående kvadratisk symbol med vektorgradienter, `128 × 128 mm` (`viewBox="0 0 512 512"`).
- `E-postofferten-symbol-farg-plan.svg` — fristående kvadratisk symbol i 100 % plana solida färger (utan gradienter/transparens), `128 × 128 mm`.

## Fullt redigerbar lagerstruktur (Illustrator / Affinity / Inkscape / CorelDRAW)
Alla original är uppbyggda av rena, slutna Bézier-konturer (`<path>`) i 1:1-koordinater utan transform-matriser eller linjetjocklekar (`stroke`), indelade i tydliga namngivna lager (`<g id="...">`):
- `lager-symbolplatta` (`symbol-basplatta`, `symbol-innerkant`)
- `lager-kuvert-bak` (`kuvert-bakflik`)
- `lager-offertblad` (`offertblad-ark`, `offertblad-rad-1`, `offertblad-prisbricka`, `offertblad-rad-2`)
- `lager-kuvert-fram` (`kuvert-sidovingar`, `kuvert-bottenflik`, `kuvert-v-fals`)
- `lager-offertsigill` (`sigill-kontur`, `sigill-guldbricka`, `sigill-bock`)
- `lager-ordbild` (`bokstav-01-E` till `bokstav-14-n` — varje bokstav är en separat konturbana)
- `lager-accentlinje` (`accent-primar`, `accent-guld`)

Inga typsnitt, inga inbäddade rasterbilder och inga externa resurser krävs.
SVG är RGB-original; tryckeriet konverterar vid behov till CMYK/Pantone enligt sin ICC-profil och kontrollerar provtryck, kontrast och minsta läsbara storlek.
Den vita färgen (`#FFFFFF`) är vit yta, inte automatisk utskärning för färgade underlag.
Wordmarkens fontlicens finns i `../docs/branding-font-license.txt`.
Digitala varianter (inkl. `mailoffer-logo-light.svg` för mörk bakgrund) finns i `../icons/`.
