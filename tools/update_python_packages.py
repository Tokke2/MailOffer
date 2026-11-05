"""Update app dependencies in the shared interpreter, before any Qt imports."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.process_utils import quiet_process_options


def update_packages(run=subprocess.run):
    if sys.prefix != sys.base_prefix:
        raise RuntimeError('En separat Python-miljo far inte anvandas.')
    specs = []
    for line in (ROOT / 'requirements.txt').read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            # Keep tested versions as minima, allow newer stable compatible releases.
            specs.append(line.replace('==', '>='))
    def invoke(arguments):
        return run([sys.executable, '-m', *arguments], timeout=900,
                   **quiet_process_options()).returncode
    if invoke(['pip', '--version']) != 0:
        if invoke(['ensurepip', '--upgrade']) != 0:
            return 1
    result = invoke(['pip', 'install', '--upgrade', '--disable-pip-version-check',
                     '--no-input', '--retries', '1', '--timeout', '30', *specs])
    if result:
        return result
    return invoke(['pip', 'check'])


if __name__ == '__main__':
    try:
        raise SystemExit(update_packages())
    except Exception as exc:
        print('Python-tillagg kunde inte uppdateras:', exc, file=sys.stderr)
        raise SystemExit(1)
