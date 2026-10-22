"""Scheduled, password-redacted local backups. Only runs while app is open."""
from datetime import datetime, timezone
from pathlib import Path
from core.user_backup import create_full_backup


def run_due_backup(base, settings, *, dir_sources=None, now=None):
    if not settings.get('auto_backup_enabled', False):
        return None
    now = now or datetime.now(timezone.utc)
    hours = max(1, min(8760, int(settings.get('auto_backup_hours', 24))))
    keep = max(1, min(100, int(settings.get('auto_backup_keep', 10))))
    try:
        last = datetime.fromisoformat(settings.get('auto_backup_last', ''))
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if 0 <= (now - last).total_seconds() < hours * 3600:
            return None
    except (ValueError, TypeError):
        pass
    root = Path(base) / '.data' / 'automatic-backups'
    root.mkdir(parents=True, exist_ok=True)
    dest = root / ('auto-' + now.strftime('%Y%m%d-%H%M%S-%f') + '.zip')
    partial = dest.with_suffix('.partial')
    try:
        create_full_backup(Path(base), getattr(settings, 'settings_path', None),
                           partial, dir_sources=dir_sources)
        partial.replace(dest)
    finally:
        partial.unlink(missing_ok=True)
    settings.set('auto_backup_last', now.isoformat())
    if hasattr(settings, 'save') and not settings.save():
        raise OSError('Kunde inte spara tidpunkten för säkerhetskopian')
    for old in sorted(root.glob('auto-*.zip'), reverse=True)[keep:]:
        old.unlink()
    return dest
