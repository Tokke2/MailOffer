#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Native messaging-host: Thunderbird → E-postofferten contacts.json."""
from __future__ import annotations

import json
import os
import re
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

APP_ROOT = Path(__file__).resolve().parents[1]
CONTACTS_PATH = APP_ROOT / "adresslistor" / "contacts.json"
_EMAIL_RE = re.compile(r"[^<\s@]+@[^>\s@]+\.[^>\s@]+")


def _read() -> Dict[str, Any] | None:
    raw = sys.stdin.buffer.read(4)
    if not raw or len(raw) < 4:
        return None
    length = struct.unpack("<I", raw)[0]
    payload = sys.stdin.buffer.read(length)
    if not payload:
        return None
    return json.loads(payload.decode("utf-8"))


def _write(obj: Dict[str, Any]) -> None:
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def _load() -> List[Dict[str, Any]]:
    if not CONTACTS_PATH.is_file():
        return []
    try:
        raw = json.loads(CONTACTS_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return []
    if isinstance(raw, dict) and isinstance(raw.get("contacts"), list):
        return [c for c in raw["contacts"] if isinstance(c, dict)]
    if isinstance(raw, list):
        return [c for c in raw if isinstance(c, dict)]
    if isinstance(raw, dict):
        rows = []
        for email, value in raw.items():
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("email", email)
                rows.append(item)
        return rows
    return []


def _save(contacts: List[Dict[str, Any]]) -> None:
    CONTACTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"contacts": contacts}, ensure_ascii=False, indent=2)
    fd, tmp = tempfile.mkstemp(
        suffix=".tmp", dir=str(CONTACTS_PATH.parent), text=True
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, CONTACTS_PATH)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _upsert(contacts: List[Dict[str, Any]], item: Dict[str, Any]) -> str:
    email = str(item.get("email") or "").strip().lower()
    if not email or not _EMAIL_RE.search(email):
        return "skip"
    name = str(item.get("name") or "").strip()
    company = str(item.get("company") or "").strip()
    for existing in contacts:
        if str(existing.get("email") or "").strip().lower() == email:
            if name and not existing.get("name"):
                existing["name"] = name
            if company and not existing.get("company"):
                existing["company"] = company
            return "updated"
    row: Dict[str, Any] = {"email": email}
    if name:
        row["name"] = name
    if company:
        row["company"] = company
    contacts.append(row)
    return "added"


def handle(msg: Dict[str, Any]) -> Dict[str, Any]:
    action = str(msg.get("action") or "add_contacts")
    if action == "ping":
        return {"ok": True, "contacts_path": str(CONTACTS_PATH)}
    if action != "add_contacts":
        return {"ok": False, "error": "okänd åtgärd"}
    incoming = msg.get("contacts") or []
    if not isinstance(incoming, list):
        return {"ok": False, "error": "contacts måste vara en lista"}
    contacts = _load()
    added = updated = skipped = 0
    for item in incoming:
        if not isinstance(item, dict):
            skipped += 1
            continue
        result = _upsert(contacts, item)
        if result == "added":
            added += 1
        elif result == "updated":
            updated += 1
        else:
            skipped += 1
    _save(contacts)
    return {
        "ok": True,
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "path": str(CONTACTS_PATH),
    }


def main() -> None:
    try:
        msg = _read()
        if not msg:
            _write({"ok": False, "error": "tomt meddelande"})
            return
        _write(handle(msg))
    except Exception as exc:
        try:
            _write({"ok": False, "error": str(exc)})
        except Exception:
            pass


if __name__ == "__main__":
    main()
