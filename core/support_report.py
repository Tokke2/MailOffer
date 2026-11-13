"""Export only allowlisted diagnostic facts, never raw log lines or messages."""
import re
from datetime import datetime, timezone
from pathlib import Path
from core.version import __version__ as APP_VERSION, BUILD_ID

STAMP = re.compile(r'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d')


def _lines(path):
    if path.is_symlink() or not path.is_file():
        return []
    with path.open('rb') as stream:
        size = stream.seek(0, 2)
        stream.seek(max(0, size - 2 * 1024 * 1024))
        data = stream.read()
    encoding = 'utf-16-le' if b'\x00' in data[:200] else 'utf-8-sig'
    # UTF-16 seeking is aligned because the byte limit is even.
    return data.decode(encoding, errors='replace').splitlines()


def build_support_report(base):
    folder = Path(base) / 'logs'
    lines = _lines(folder / 'app.log')
    result = ['E-postofferten — senaste felsökningsrapport',
              'Exporterande appversion: ' + APP_VERSION, 'Exporterande bygg: ' + BUILD_ID,
              'Exporttid UTC: ' + datetime.now(timezone.utc).isoformat(),
              'Sekretess: adresser, sökvägar, mejltext och fria feltexter utelämnas helt.',
              'Endast tillåtna statusfält exporteras. Rapporten är inte en fullständig logg.',
              'Underlag: högst sista 2 MiB per aktiv logg; arkiv läses inte.', '']
    # Use strict patterns and bounded numeric/status tokens; no arbitrary captured text.
    for title, marker in [('Senaste start', 'PROCESS START Python='),
                          ('Senaste sändningsförsök', 'Förbereder sändning – ämne:')]:
        indices = [i for i, line in enumerate(lines) if marker in line]
        result.append(title + ':')
        if not indices:
            result.append('Ingen startmarkör i tillgängligt underlag.')
            continue
        selected = lines[indices[-1]:]
        for line in selected:
            time = STAMP.match(line)
            if not time:
                continue
            prefix = time.group() + ' | '
            if 'PROCESS START Python=' in line:
                version = re.search(r'Python=(\d{1,2}\.\d{1,2}\.\d{1,3})\b', line)
                result.append(prefix + 'Process start; Python=' + (version.group(1) if version else 'okänd'))
            if 'En annan instans kör' in line:
                result.append(prefix + 'Annan instans kör redan')
            match = re.search(r'Bygg=(\d{1,20}) \|', line)
            if match:
                result.append(prefix + 'Körande bygg=' + match.group(1))
            match = re.search(r'Autostart: ok=(True|False) wanted=(True|False) klass=(correct|missing|stale_console|stale_path|stale_args|different) blocked=(True|False)', line)
            if match:
                result.append(prefix + 'Autostart: ' + ', '.join(match.groups()))
            match = re.search(r'STAGE: shutdown complete exit_code=(-?\d{1,12})\b', line)
            if match:
                result.append(prefix + 'Avslutskod=' + match.group(1))
            if 'Förbereder sändning – ämne:' in line:
                result.append(prefix + 'Sändningsförsök påbörjat; innehåll och mottagare utelämnade')
            match = re.search(r'Batch (\d{1,8})/(\d{1,8}) skickad \((TO|BCC|TO-SV|TO-EN|BCC-SV|BCC-EN), (\d{1,8}) mottagare\)', line)
            if match:
                result.append(prefix + 'SMTP accepterade batch: ' + '/'.join(match.groups()))
            if 'Sändning klar. Batchar:' in line:
                result.append(prefix + 'Sändning avslutad; inte bevis på inkorgsleverans')
            if 'SEND_CHECK signature_not_configured' in line:
                result.append(prefix + 'Appsignatur ej konfigurerad (inte DKIM-resultat)')
            if re.search(r'\| (?:ERROR|CRITICAL)\s*\|', line):
                result.append(prefix + 'Fel registrerat; detaljer utelämnade av sekretesskäl')
        result.append('')
    result.append('Senaste startkedjehändelser:')
    startup = _lines(folder / 'startup.log')
    starts = [i for i, line in enumerate(startup) if 'Launcher started; folder=' in line]
    for line in startup[starts[-1] if starts else len(startup):]:
        stamp = STAMP.match(line)
        if stamp:
            code = re.search(r'(?:Process ended; exit code=|Python startup check ended; exit code=)(-?\d{1,12})\b', line)
            if code:
                kind = 'Process avslutad' if 'Process ended;' in line else 'Python-kontroll avslutad'
                result.append(stamp.group() + ' | ' + kind + '; kod=' + code.group(1))
    result.append('Samtidiga processer kan ha blandade loggrader. Frånvaro av fel bevisar inte lyckad autostart.')
    return '\n'.join(result) + '\n'
