# Vad saknas? – lägesanalys 2026-10-19 (efter 5.4)

## ✅ Gjort i 5.4 (denna omgång)

- **Mall-wizard** (`ui/template_wizard.py`) – skapa TXT/HTML/DOCX-mallar
  steg för steg i appen; Mall-fliken har nu wizard-knapp + klickbar lista.
  Tidigare fanns *ingen* möjlighet att skapa mallar i appen (fliken var en stub).
- **Appen på svenska/engelska** (`core/i18n.py`) – verktygsrad, menyer,
  flikar, stegrubriker, wizard, uppdatering, donation och Om-dialog går via
  `tr()`. Språkmeny + omstartserbjudande. (Se lucka P1-5 nedan.)
- **Autouppdatering från GitHub Releases** (`core/github_update.py`) –
  tyst sökning vid start (max 1/dygn, avstängbar) + manuell knapp i
  Arkiv-menyn, Hjälp-menyn och Inställningar. Zip-slip-skydd,
  `main.pyw`-validering av nedladdningen, och `Mallar/` + JSON +
  inställningar är skyddade användardata.
- **Donation via Ko-fi** (`core/donate.py`, `ui/donate.py`) –
  ❤️-knapp + dialog med kopiera-länk; länken redigeras i
  *Inställningar → ❤️ Stöd & om* och normaliseras automatiskt
  (”användarnamn” → `https://ko-fi.com/användarnamn`).
- **Versionen samlad** i `core/version.py` (5.4.0) + exempelmall i
  `Mallar/`, README på sv/en, CI-workflow som kör testerna, och 69
  enhetstester (tidigare 13).

## 🔴 P0 – gör snart (annars fungerar 5.4 inte fullt ut)

1. **Publicera första GitHub-releasen.** Det finns inga releases än, så
   autouppdateraren svarar korrekt ”ingen publicerad release”.
   Steg finns i `README.md` (”Uppdateringar & att publicera en release”):
   `gh release create v5.4.0 --title "E-postofferten 5.4.0" --generate-notes`
   – gör det när 5.4-koden mergats till `main`.
2. ~~**Fyll i Ko-fi-länken**~~ ✅ KLAR (5.4-uppföljning):
   ko-fi.com/tokke2 + paypal.me/Rickard3dPrint är inbyggda
   standardlänkar (kan bytas i *Inställningar → ❤️ Stöd & om*) och
   står i `README.md` + `.github/FUNDING.yml`. Kvar för ägaren:
   fyll i **Swish-numret** i inställningarna så dyker QR-koden upp
   på appens Stöd projektet-sida.
3. **LICENSE saknas.** Utan licens får andra juridiskt inte använda eller
   bidra till koden. Välj t.ex. MIT (tillåtande) eller GPL (copyleft) och
   lägg till filen `LICENSE`.
4. **SMTP-lösenordet sparas i klartext** i `email_settings.json`
   (”password”). Flytta till OS-nyckelring (`keyring`) eller krypterad
   lagring (Fernet) – punkten finns redan i specens backlog.

## 🟡 P1 – viktigt för kvalitet/skala

5. **Resten av UI:t är fortfarande hårdkodad svenska**: `ui/dialogs.py`,
   `ui/editors.py`, `ui/preview.py`, `script/contacts_ui.py` och de flesta
   formulär-/statusmeddelanden i `ui/main_window.py` (bl.a. sänddialogen,
   kontakttabellen, historik/logg). Infrastrukturen finns nu – migrera
   fil för fil till `tr()`-nycklar i `core/i18n.py`.
   Även Thunderbird-tilläggets `popup.html` är på svenska.
6. **Testtäckning för kärnflöden saknas**: `core/email_sender.py`
   (sändning, batchning, kvitton) och `script/recipients.py` saknar
   tester. En fake-SMTP-server i test vore högst värdefull. Autostartens
   registry-logik är otestad utanför Windows.
7. **Ingen paketering**: slutanvändare behöver Python + pip. Lägg till
   PyInstaller-bygge (`.spec` är gitignorerad i dag) och gärna
   NSIS-installer med signering för Windows.
8. **Release-integritet**: uppdateraren verifierar att zip:en innehåller
   `main.pyw`, men ingen checksumma/signatur kontrolleras. Publicera
   SHA256 per release och verifiera i `github_update.py`.
9. ~~**HTML-mallar escapas inte**~~ ✅ ÅTGÄRDAD (5.4-uppföljning):
   `create_template` escaper nu ämne + brödtext och `_parse_html`
   unescaper vid inläsning – roundtrip-test finns i testsuite.
10. **Dokumentations-/koddrift**: `spec.md` säger version 6.2 medan appen
    är 5.4.0; `SendConfirmDialog` finns i två kopior (`ui/dialogs.py`
    kanonisk, `ui/editors.py` för API-kompatibilitet) och
    `PLACEHOLDER_DROPDOWNS` dupliceras i `script/templates.py` och
    `ui/main_window.py`. Samla till en källa per begrepp.
11. **`E-postofferten-kontakter.xpi` i repo-roten** är en byggd binär utan
    bygginstruktion – dokumentera hur den byggs ur `thunderbird/` eller
    flytta den till Releases.

## 🟢 P2 – önskelista (från specens backlog §/§47, fortfarande öppen)

12. Schemalagd sändning; flera SMTP-konton; OAuth2 för Gmail/Outlook;
    signaturhantering per avsändare; kontaktimport `.vcf`/Google CSV;
    WYSIWYG-redigerare för HTML-mallar; loggfiltrering per nivå;
    avbryt-knapp för batch-sändning; global sök; PDF-rapporter;
    plugin-system med hot reload; To↔Bcc-dubblettvarning och
    bild-thumbnails (valda §47-punkter).
13. Tillgänglighet: skärmläsaretiketter, genomtänkt tabbordning och
    genvägar till de nya funktionerna (wizard/uppdatering/donation).
14. Vid språkbyte: i dag krävs omstart för redan byggda vyer (nya
    dialoger får rätt språk direkt). Äkta live-översättning kräver att
    vyerna byggs om – större jobb, bör vänta tills P1-5 är klar.
