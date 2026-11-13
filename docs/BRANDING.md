# E-postofferten – grafiskt original

© 2026 Rickard Längkvist.

Prism-symbol: elektriskt blå/lila platta, cyan kuvert, gyllene offertetikett
och bock. Vektorbyggda högdagrar och glimt ger en mer färgstark digital profil. Wordmarken använder produktnamnet E-postofferten.

## Leverans
Tryckoriginal ligger i **tryck/** i den vanliga release-nedladdningen.
Ingen separat nedladdning eller grafik-ZIP behövs.
- `tryck/E-postofferten-farg.svg`: plan färglogotyp utan gradienter/transparens.
- `tryck/E-postofferten-svart.svg`: svart/vit logotyp för ljust underlag.
- `tryck/E-postofferten-symbol.svg`: symbol med vektorgradienter.
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

Grundfärger: indigo #182969, blå/lila #313CCB, cyan #51CDFA, guld #FFBD38, vit #FFFFFF.
Digitala original har vektorgradienter; den plana färglogotypen är förenklad för tryck.
SVG är RGB-original, inte en CMYK/PDF-X-certifierad tryckfil. Be tryckeriet
konvertera enligt sin ICC-profil och kontrollera provtryck/färger och minsta
läsbara storlek. Svartvarianten är avsedd för ljust underlag. Vitt i symbolen
är vitt, inte en automatisk utskärning för alla underlagsfärger.

## Återskapa rasterexporter
Byggverktyg (inte appberoenden): Pillow och resvg-py.
Kör `python tools/make_icon.py` och sedan `python tools/build_thunderbird.py`.
SVG-filerna är original; ändringar i dem kräver nya rasterexporter.
