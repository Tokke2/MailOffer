# E-postofferten – grafiskt original

© 2026 Rickard Längkvist.

Ny symbol: kuvert med turkos offertetikett och bock. Enkel geometri för små
ikoner och tryck. Wordmarken använder produktnamnet E-postofferten.

## Leverans
- `icons/mailoffer-logo.svg`: horisontell färglogotyp, vektor, 180 × 45 mm.
- `icons/mailoffer-logo-black.svg`: svart variant för ljust underlag.
- `icons/app_icon.svg`: kvadratisk vektorsymbol, 128 × 128 mm.
- `icons/mailoffer-logo.png`: transparent förhandsbild, 2560 px bred.
- `icons/app_icon.png`: 1024 × 1024, transparent.
- `icons/app_icon.ico`: Windows, 16–256 px.
- `icons/app_icon.icns`: macOS.
- `thunderbird/icon.png`: 256 × 256, även inbyggd i MailOffer.xpi.

SVG-originalen innehåller banor/geometri, inte en bitmap inbakad i SVG.
Bokstäverna är omvandlade till banor. Inga externa bilder, länkar eller
installerade typsnitt behövs. Skala proportionerligt till önskat mått.
DejaVu Sans Bold används som grund för bokstavsbanorna; dess licensnotiser
medföljer i branding-font-license.txt. Inget separat typsnitt krävs för tryck.

Färger: marinblå #123247, turkos #00A996, vit #FFFFFF.
SVG är RGB-original, inte en CMYK/PDF-X-certifierad tryckfil. Be tryckeriet
konvertera enligt sin ICC-profil och kontrollera provtryck/färger och minsta
läsbara storlek. Svartvarianten är avsedd för ljust underlag. Vitt i symbolen
är vitt, inte en automatisk utskärning för alla underlagsfärger.

## Återskapa rasterexporter
Byggverktyg (inte appberoenden): Pillow och resvg-py.
Kör `python tools/make_icon.py` och sedan `python tools/build_thunderbird.py`.
SVG-filerna är original; ändringar i dem kräver nya rasterexporter.
