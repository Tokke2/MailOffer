# E-postofferten – grafiskt original & ikonsystem

© 2026 Rickard Längkvist.

Skarp nordisk kuvert- och offertsymbol: djup kobaltsblå platta med isblå innerkant,
vitt offertblad med specifikationsrader, öppet kuvert med exakt geometrisk fals
samt gyllene offertsigill med bock. Ordbilden `E-postofferten` har en tvådelad
accentlinje i himmelsblått och guld under `offerten`.

## Leverans (tryck & digitalt)
Tryckoriginal ligger i **`tryck/`** i den vanliga release-nedladdningen:
- `tryck/E-postofferten-farg.svg`: redigerbar plan färglogotyp utan gradienter, filter, strokes eller transparens (`180 × 45 mm`).
- `tryck/E-postofferten-svart.svg`: redigerbar svart/vit 1-färgslogotyp för ljust underlag (`180 × 45 mm`).
- `tryck/E-postofferten-symbol.svg`: fristående symbol med vektorgradienter (`128 × 128 mm`).
- `tryck/E-postofferten-symbol-farg-plan.svg`: fristående plan trycksymbol utan gradienter (`128 × 128 mm`).
- `icons/mailoffer-logo.svg` + `icons/mailoffer-logo.png` (`2560 × 640`): horisontell färglogotyp för ljust underlag.
- `icons/mailoffer-logo-light.svg` + `icons/mailoffer-logo-light.png` (`2560 × 640`): horisontell logotyp med vit ordbild för mörkt/blått underlag (bl.a. appens hero-huvud och donationsdialog).
- `icons/mailoffer-logo-black.svg`: monokrom svart vektorlogotyp.
- `icons/app_icon.svg`: kvadratisk vektorsymbol (`128 × 128 mm`, `viewBox="0 0 512 512"`).
- `icons/app_icon.png`: `1024 × 1024` RGBA.
- `icons/app_icon.ico`: Windows-ikon där varje ram (`16, 24, 32, 48, 64, 128, 256 px`) renderats direkt från vektororiginalet för maximal skärpa i aktivitetsfält och systemfält.
- `icons/app_icon.icns`: macOS.
- `thunderbird/icon.png`: `256 × 256`, även inbyggd i `thunderbird/MailOffer.xpi`.

## Redigerbarhet & färgkoder
Alla SVG-original består uteslutande av slutna Bézier-banor (`<path>`) i namngivna lager (`lager-symbolplatta`, `lager-kuvert-bak`, `lager-offertblad`, `lager-kuvert-fram`, `lager-offertsigill`, `lager-ordbild`, `lager-accentlinje`) utan typsnittsberoenden, rasterbilder eller externa länkar.
DejaVu Sans Bold används som grund för bokstavsbanorna; licensnotis medföljer i `branding-font-license.txt`.

Grundfärger (plana tryckoriginal):
- Marinblå kontur / ordbild: `#0F1E54`
- Koboltblå basplatta: `#18368C`
- Himmelsblå kuvert/accent: `#0EA5E9` / `#38BDF8`
- Ljus isblå sidovingar: `#DBEAFE`
- Offertguld: `#FBBF24` / `#F59E0B`
- Vit: `#FFFFFF`

SVG är RGB-original, inte en CMYK/PDF-X-certifierad tryckfil. Be tryckeriet konvertera enligt sin ICC-profil och kontrollera provtryck och minsta storlek.

## Återskapa vektorer & rasterexporter
Byggverktyg (endast vid generering, inte appberoenden): `Pillow` och `resvg-py`.
Kör `python tools/make_icon.py` och sedan `python tools/build_thunderbird.py`.
