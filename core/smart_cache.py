"""Conservative daily cleanup of old Python bytecode, never user documents.

Only known application __pycache__ directories are inspected. No recursive
search, global temporary-directory sweep, or directory deletion is performed.
"""
from datetime import datetime, timezone
import logging
from pathlib import Path
import stat

log = logging.getLogger(__name__)
INTERVAL_SECONDS = 24 * 60 * 60
CACHE_DIRS = ("__pycache__", "core/__pycache__", "ui/__pycache__", "script/__pycache__")


def clean_smart_cache(base, *, now=None):
    """Remove regular .pyc files older than 24h. Never follow symlinks.

    Return counts and bytes; locked/unreadable files remain and are counted.
    """
    now = now or datetime.now(timezone.utc)
    base = Path(base).resolve(strict=True)
    result = {"removed": 0, "bytes": 0, "errors": 0}
    for relative in CACHE_DIRS:
        folder = base / relative
        # Check every component: even a symlinked core/ must not be traversed.
        parts = [folder, *folder.parents]
        if any(p.is_symlink() or getattr(p, "is_junction", lambda: False)()
               for p in parts[:parts.index(base)]):
            continue
        try:
            if not folder.is_dir():
                continue
            for path in folder.glob("*.pyc"):
                try:
                    info = path.lstat()
                    if not stat.S_ISREG(info.st_mode):
                        continue
                    if now.timestamp() - info.st_mtime < INTERVAL_SECONDS:
                        continue
                    path.unlink()
                    result["removed"] += 1
                    result["bytes"] += info.st_size
                except OSError:
                    result["errors"] += 1
                    log.warning("Kunde inte rensa cachefil: %s", path, exc_info=True)
        except OSError:
            result["errors"] += 1
            log.warning("Kunde inte läsa cachekatalog: %s", folder, exc_info=True)
    return result


def run_due_cleanup(base, settings, *, now=None, force=False):
    """Run at most once per 24h unless explicitly requested by the user."""
    if not force and not settings.get("auto_cache_cleanup", True):
        return None
    now = now or datetime.now(timezone.utc)
    if not force:
        try:
            last = datetime.fromisoformat(settings.get("cache_cleanup_last", ""))
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if 0 <= (now - last).total_seconds() < INTERVAL_SECONDS:
                return None
        except (ValueError, TypeError):
            pass
    result = clean_smart_cache(base, now=now)
    previous = settings.get("cache_cleanup_last", "")
    settings.set("cache_cleanup_last", now.isoformat())
    try:
        if not settings.save():
            raise OSError("Kunde inte spara tidpunkten för cacherensningen")
    except Exception:
        settings.set("cache_cleanup_last", previous)
        raise
    log.info("Smart cacherensning: %s", result)
    return result
