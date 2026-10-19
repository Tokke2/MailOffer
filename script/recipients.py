#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
script/recipients.py – Mottagarhantering för EmailApp (PyQt6)

Version: 5.5 – LÄGG TILL HELA GRUPPER I TO/BCC + GRUPPSORTERING

ÄNDRINGAR mot v5.4:
- ✅ LÄGG TILL HEL GRUPP: när en kategori är vald i adressboken
    (t.ex. "Bilrutor (10)") kan man med ETT klick lägga till alla
    mottagare i gruppen direkt i To eller Bcc
    * Knappar "➕ Alla (n) → To" / "➕ Alla (n) → Bcc" (visar antal)
    * Gäller även "Alla kontakter (n)" – hela adressboken på en gång
    * Kontextmeny på kategorilistan: "➕ Lägg till alla (n) som To/Bcc"
    * Dialogen stannar öppen; feedback visar antal tillagda
    * Använder on_add-callback → språk per kontakt (SV/EN) följer med
- ✅ GRUPPSORTERING: högerklick på kategorilistan → "↕ Sortera A-Ö"
    eller "↕ Sortera efter antal (flest först)" – kategorierna visas
    t.ex. "Bilrutor (10), Reservdelar (4)" i valfri ordning
- ✅ Gruppåtgärdsraden uppdateras vid kategoriändring och CRUD

Fixar mot v5.3:
- ✅ Korrupt markdown/inklistringssyntax borttagen
- ✅ BUGG: AddressBookDialog._selected_contacts() saknades
    * Kontextmenyn "Kopiera namn + e-post" kraschade med
      AttributeError – metoden är tillagd
- ✅ BUGG: EventBus-prenumeration med lambdas (GC:as av weakrefs)
    * recipients.updated / contacts.updated nådde ALDRIG fliken
    * Nu: bundna metoder _on_recipients_updated / _on_contacts_updated
- ✅ BUGG: _color_for_category använde hash() (slumpas per process)
    * Avatarfärger ändrades vid varje start
    * Nu: deterministisk färg via sum(ord) – stabila färger varje start
- ✅ SNABBARE: _StoreAdapter.count() använder _store.count() om det finns
- ✅ SNABBARE: RecipientStore._notify() – läser lista-längder utan
  extra låsningar
- ✅ SNABBARE: AddressBookDialog – avatarer skapas bara för synliga
  kontakter, sortering görs en gång
- ✅ _set_feedback() visar tydlig status – "Dialogen stannar öppen"

ÄNDRINGAR mot v5.2 (bevarade):
- AddressBookDialog stängs INTE när användaren trycker på "Lägg till"
- Adresser läggs till direkt i To/Bcc via callback när sådan finns
- Statusfeedback i adressboken efter "Lägg till"
- "Klar"-knapp för att användaren själv ska stänga adressboken
- Bevarad kategorisidopanel + avatarer + tom-state
- Snyggare sortering i adressboken: Namn/E-post/Företag/Kategori + A-Ö / Ö-A
- Kontextmeny i adressboken: Lägg till i To/Bcc, Redigera, Ta bort, Kopiera e-post
- Enklare kontaktadministration direkt i adressboken
- Bättre bevarande av vald kategori vid uppdatering
- RecipientsTab kvar som 3-stegsflöde
- Hjälpmetoder för default_bcc tillagda för bättre kompatibilitet

Klasser:
- Contact:           Dataclass
- _StoreAdapter:     Adapter
- ContactStore:      Lokal kontaktdatabas
- AddContactDialog:  QDialog för ny/redigera kontakt
- AddressBookDialog: QDialog med kategorisidopanel + lista
- RecipientStore:    To/Bcc i minnet
- RecipientsTab:     QWidget med 3-stegs wizard

REGLER:
- Ingen Tkinter-kod
- StyleEngine används för färger om tillgänglig
- QDialog.exec() för modal visning
- Adressboken ska inte stängas när man trycker på "Lägg till"

FIL: script/recipients.py
"""

from __future__ import annotations

# stdlib
import csv
import json
import logging
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# PyQt6
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QClipboard, QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# ui
from ui.styles import StyleEngine, get_colors

log = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

try:
    from email_validator import (  # type: ignore
        EmailNotValidError,
        validate_email as _ext_validate,
    )
    _HAS_EMAIL_VALIDATOR = True
except ImportError:
    _HAS_EMAIL_VALIDATOR = False
    _ext_validate = None  # type: ignore[assignment]
    EmailNotValidError = Exception


def validate_email_address(email: str) -> bool:
    """Validera e-postadress via email-validator eller regex-fallback."""
    if not email or not isinstance(email, str):
        return False
    candidate = email.strip()
    if _HAS_EMAIL_VALIDATOR:
        try:
            _ext_validate(candidate, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False
    return bool(_EMAIL_RE.match(candidate))


# ═══════════════════════════════════════════════════════════════════════════
# Contact dataclass
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Contact:
    email: str
    name: str = ""
    company: str = ""
    group: str = ""
    categories: List[str] = field(default_factory=list)

    def normalize(self) -> "Contact":
        self.email = self.email.strip().lower()
        self.name = self.name.strip()
        self.company = self.company.strip()
        self.group = self.group.strip()
        self.categories = [
            category.strip()
            for category in self.categories
            if category.strip()
        ]
        if self.group and self.group not in self.categories:
            self.categories.append(self.group)
        return self

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"email": self.email}
        if self.name:
            data["name"] = self.name
        if self.company:
            data["company"] = self.company
        if self.group:
            data["group"] = self.group
        if self.categories:
            data["categories"] = self.categories
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contact":
        categories = list(data.get("categories", []))
        group = data.get("group") or ""
        if group and group not in categories:
            categories.append(group)
        return cls(
            email=data.get("email", ""),
            name=data.get("name", ""),
            company=data.get("company", ""),
            group=group,
            categories=categories,
        ).normalize()

    def display_name(self) -> str:
        return f"{self.name} <{self.email}>" if self.name else self.email

    def initials(self) -> str:
        """Returnera 1–2 initialer för avatar."""
        source = self.name or self.email
        parts = [
            part
            for part in source.replace(".", " ").replace("_", " ").split()
            if part
        ]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Contact):
            return NotImplemented
        return self.email == other.email

    def __hash__(self) -> int:
        return hash(self.email)


# ═══════════════════════════════════════════════════════════════════════════
# _StoreAdapter
# ═══════════════════════════════════════════════════════════════════════════

class _StoreAdapter:
    """Adapter – garanterar grouped_by_category() oavsett underliggande store."""

    def __init__(self, store: Any) -> None:
        self._store = store

    def all(self) -> List[Contact]:
        try:
            return [self._to_contact(contact) for contact in self._store.all()]
        except Exception:
            log.exception("StoreAdapter.all()")
            return []

    def count(self) -> int:
        try:
            if hasattr(self._store, "count"):
                return int(self._store.count())
            return len(self.all())
        except Exception:
            return 0

    def get(self, email: str) -> Optional[Contact]:
        try:
            raw = self._store.get(email)
            return self._to_contact(raw) if raw is not None else None
        except Exception:
            return None

    def categories(self) -> Set[str]:
        try:
            if hasattr(self._store, "categories"):
                return set(self._store.categories())
        except Exception:
            pass

        result: Set[str] = set()
        for contact in self.all():
            result.update(contact.categories)
        result.discard("")
        return result

    def grouped_by_category(self) -> Dict[str, List[Contact]]:
        if hasattr(self._store, "grouped_by_category"):
            try:
                raw = self._store.grouped_by_category()
                return {
                    category: [self._to_contact(contact) for contact in items]
                    for category, items in raw.items()
                }
            except Exception:
                log.warning(
                    "grouped_by_category() kastade – fallback", exc_info=True
                )

        result: Dict[str, List[Contact]] = {}
        for contact in self.all():
            categories = [
                cat for cat in contact.categories if cat
            ] or ["Okategoriserad"]
            for category in categories:
                result.setdefault(category, []).append(contact)
        for category in result:
            result[category].sort(
                key=lambda c: (c.name or c.email).lower()
            )
        return result

    def upsert(
        self,
        email: str,
        name: str = "",
        company: str = "",
        group: str = "",
        categories: Optional[List[str]] = None,
    ) -> Optional[Contact]:
        try:
            cats = list(categories) if categories else []
            if group and group not in cats:
                cats.append(group)
            if hasattr(self._store, "upsert"):
                result = self._store.upsert(
                    email=email,
                    name=name,
                    company=company,
                    group=group,
                    categories=cats,
                )
                return self._to_contact(result)
        except Exception:
            log.exception("StoreAdapter.upsert()")
        return None

    def delete(self, email: str) -> bool:
        try:
            if hasattr(self._store, "delete"):
                return bool(self._store.delete(email))
        except Exception:
            log.exception("StoreAdapter.delete()")
        return False

    def save(self) -> None:
        try:
            if hasattr(self._store, "save"):
                self._store.save()
        except Exception:
            log.exception("StoreAdapter.save()")

    def reload(self) -> None:
        try:
            if hasattr(self._store, "reload"):
                self._store.reload()
            elif hasattr(self._store, "load"):
                self._store.load()
        except Exception:
            log.exception("StoreAdapter.reload()")

    @property
    def path(self) -> Optional[Path]:
        try:
            raw = None
            if hasattr(self._store, "path"):
                raw = getattr(self._store, "path")
            elif hasattr(self._store, "_path"):
                raw = getattr(self._store, "_path")
            return Path(raw) if raw else None
        except Exception:
            return None

    @staticmethod
    def _to_contact(raw: Any) -> Contact:
        if isinstance(raw, Contact):
            return raw
        if raw is None:
            return Contact(email="")
        if hasattr(raw, "to_dict"):
            try:
                return Contact.from_dict(raw.to_dict())
            except Exception:
                pass
        if isinstance(raw, dict):
            try:
                return Contact.from_dict(raw)
            except Exception:
                pass
        try:
            return Contact(
                email=getattr(raw, "email", ""),
                name=getattr(raw, "name", ""),
                company=getattr(raw, "company", ""),
                group=getattr(raw, "group", ""),
                categories=list(getattr(raw, "categories", [])),
            ).normalize()
        except Exception:
            return Contact(email=str(raw)).normalize()


# ═══════════════════════════════════════════════════════════════════════════
# ContactStore (lokal)
# ═══════════════════════════════════════════════════════════════════════════

class ContactStore:
    """Läser/skriver contacts.json. Ingen UI-kod."""

    def __init__(self, path: Path, event_bus: Any = None) -> None:
        self._path = Path(path)
        self._bus = event_bus
        self._lock = threading.RLock()
        self._contacts: Dict[str, Contact] = {}
        self.load()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> None:
        with self._lock:
            self._contacts = {}
            if not self._path.exists():
                log.warning("ContactStore: %s saknas", self._path)
                self._create_empty()
                return

            try:
                data = json.loads(
                    self._path.read_text(encoding="utf-8-sig")
                )
                items = (
                    data.get("contacts", [])
                    if isinstance(data, dict)
                    else data
                    if isinstance(data, list)
                    else []
                )
                count = 0
                for item in items:
                    if isinstance(item, dict) and item.get("email"):
                        try:
                            contact = Contact.from_dict(item)
                            self._contacts[contact.email] = contact
                            count += 1
                        except Exception as exc:
                            log.warning(
                                "ContactStore: hoppar över trasig post: %s",
                                exc,
                            )
                log.info("ContactStore: %d kontakter laddade", count)
            except json.JSONDecodeError as exc:
                log.error("ContactStore JSON-fel: %s", exc)
            except Exception:
                log.exception("ContactStore: läsfel %s", self._path)

    def _create_empty(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps({"contacts": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            log.exception("ContactStore: kunde inte skapa tom fil")

    def reload(self) -> None:
        self.load()
        self._notify("reload")

    def save(self) -> None:
        with self._lock:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                ordered = sorted(
                    self._contacts.values(),
                    key=lambda c: (c.name or c.email).lower(),
                )
                tmp = self._path.with_suffix(".tmp")
                tmp.write_text(
                    json.dumps(
                        {
                            "contacts": [
                                contact.to_dict() for contact in ordered
                            ]
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                tmp.replace(self._path)
                log.info(
                    "ContactStore: sparade %d kontakter",
                    len(self._contacts),
                )
            except Exception:
                log.exception("ContactStore: sparfel")

    def upsert(
        self,
        email: str,
        name: str = "",
        company: str = "",
        group: str = "",
        categories: Optional[List[str]] = None,
    ) -> Contact:
        cats = list(categories) if categories else []
        if group and group not in cats:
            cats.append(group)
        contact = Contact(
            email=email,
            name=name,
            company=company,
            group=group,
            categories=cats,
        ).normalize()
        with self._lock:
            self._contacts[contact.email] = contact
        self._notify("upsert")
        return contact

    def add(self, contact: Contact) -> bool:
        contact.normalize()
        with self._lock:
            if contact.email in self._contacts:
                return False
            self._contacts[contact.email] = contact
        self._notify("add")
        return True

    def delete(self, email: str) -> bool:
        normalized = email.strip().lower()
        with self._lock:
            if normalized in self._contacts:
                del self._contacts[normalized]
                self._notify("delete")
                return True
        return False

    def get(self, email: str) -> Optional[Contact]:
        with self._lock:
            return self._contacts.get(email.strip().lower())

    def all(self) -> List[Contact]:
        with self._lock:
            return list(self._contacts.values())

    def count(self) -> int:
        with self._lock:
            return len(self._contacts)

    def search(self, query: str) -> List[Contact]:
        needle = query.lower().strip()
        if not needle:
            return self.all()
        with self._lock:
            return [
                contact
                for contact in self._contacts.values()
                if needle in contact.email.lower()
                or needle in contact.name.lower()
                or needle in contact.company.lower()
                or any(
                    needle in category.lower()
                    for category in contact.categories
                )
            ]

    def categories(self) -> Set[str]:
        result: Set[str] = set()
        with self._lock:
            for contact in self._contacts.values():
                result.update(contact.categories)
        result.discard("")
        return result

    def grouped_by_category(self) -> Dict[str, List[Contact]]:
        result: Dict[str, List[Contact]] = {}
        with self._lock:
            for contact in self._contacts.values():
                categories = [
                    category for category in contact.categories if category
                ] or ["Okategoriserad"]
                for category in categories:
                    result.setdefault(category, []).append(contact)
        for category in result:
            result[category].sort(
                key=lambda c: (c.name or c.email).lower()
            )
        return result

    def import_csv(self, path: Path, encoding: str = "utf-8") -> Dict[str, int]:
        counts = {"imported": 0, "skipped": 0, "errors": 0}
        try:
            with Path(path).open(encoding=encoding, newline="") as handle:
                for row in csv.DictReader(handle):
                    email = row.get("email", "").strip()
                    if not email or not validate_email_address(email):
                        counts["skipped"] += 1
                        continue
                    try:
                        self.upsert(
                            email=email,
                            name=row.get("name", ""),
                            company=row.get("company", ""),
                            group=row.get("group", ""),
                            categories=[
                                part.strip()
                                for part in row.get("categories", "").split(",")
                                if part.strip()
                            ],
                        )
                        counts["imported"] += 1
                    except Exception:
                        counts["errors"] += 1
                self.save()
        except Exception:
            log.exception("ContactStore: CSV-import")
        return counts

    def export_csv(self, path: Path, encoding: str = "utf-8") -> None:
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with Path(path).open("w", encoding=encoding, newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["email", "name", "company", "group", "categories"],
                )
                writer.writeheader()
                for contact in self.all():
                    writer.writerow(
                        {
                            "email": contact.email,
                            "name": contact.name,
                            "company": contact.company,
                            "group": contact.group,
                            "categories": ",".join(contact.categories),
                        }
                    )
        except Exception:
            log.exception("ContactStore: CSV-export")

    def clear(self) -> None:
        with self._lock:
            self._contacts.clear()
        self._notify("clear")
        self.save()

    def _notify(self, action: str) -> None:
        if self._bus:
            try:
                self._bus.publish(
                    "contacts.updated",
                    {"count": len(self._contacts), "action": action},
                )
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# RecipientStore – TO + BCC (CC BORTTAGEN)
# ═══════════════════════════════════════════════════════════════════════════

class RecipientStore:
    """Hanterar To och Bcc i minnet."""

    def __init__(self, event_bus: Any = None) -> None:
        self._bus = event_bus
        self._lock = threading.RLock()
        self._to: List[str] = []
        self._bcc: List[str] = []

    # ── To ─────────────────────────────────────────────────────────────
    def get_to_list(self) -> List[str]:
        with self._lock:
            return list(self._to)

    def add_to_list(self, email: str) -> int:
        candidate = email.strip()
        if not candidate:
            return 0
        with self._lock:
            if candidate not in self._to:
                self._to.append(candidate)
                self._notify()
                return 1
        return 0

    def remove_from_to(self, email: str) -> bool:
        with self._lock:
            if email in self._to:
                self._to.remove(email)
                self._notify()
                return True
        return False

    # ── Bcc ────────────────────────────────────────────────────────────
    def get_bcc_list(self) -> List[str]:
        with self._lock:
            return list(self._bcc)

    def add_to_bcc(self, email: str) -> int:
        candidate = email.strip()
        if not candidate:
            return 0
        with self._lock:
            if candidate not in self._bcc:
                self._bcc.append(candidate)
                self._notify()
                return 1
        return 0

    def remove_from_bcc(self, email: str) -> bool:
        with self._lock:
            if email in self._bcc:
                self._bcc.remove(email)
                self._notify()
                return True
        return False

    # ── Generella ──────────────────────────────────────────────────────
    def clear_all(self) -> None:
        with self._lock:
            self._to.clear()
            self._bcc.clear()
        self._notify()

    def get_all(self) -> Dict[str, List[str]]:
        with self._lock:
            return {"to": list(self._to), "bcc": list(self._bcc)}

    def load_from_file(self, path: Path, target: str = "to") -> int:
        path = Path(path)
        emails: List[str] = []
        if not path.exists():
            log.warning("load_from_file: %s saknas", path)
            return 0

        try:
            ext = path.suffix.lower()
            if ext == ".json":
                data = json.loads(path.read_text(encoding="utf-8-sig"))
                if isinstance(data, dict):
                    items = data.get("contacts", [])
                    if not items:
                        for key in ("to", "bcc", "emails"):
                            for email in data.get(key, []):
                                if isinstance(email, str) and email.strip():
                                    emails.append(email.strip())
                    for item in items:
                        email = (
                            item.get("email", "").strip()
                            if isinstance(item, dict)
                            else str(item).strip()
                        )
                        if email:
                            emails.append(email)
                elif isinstance(data, list):
                    for item in data:
                        email = (
                            item.get("email", "").strip()
                            if isinstance(item, dict)
                            else str(item).strip()
                        )
                        if email:
                            emails.append(email)
            elif ext == ".txt":
                for line in path.read_text(encoding="utf-8-sig").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        emails.append(line)
        except Exception:
            log.exception("load_from_file: %s", path)
            return 0

        count = 0
        for email in emails:
            if validate_email_address(email):
                if target == "bcc":
                    count += self.add_to_bcc(email)
                else:
                    count += self.add_to_list(email)
        log.info(
            "load_from_file: %d → %s från %s", count, target, path.name
        )
        return count

    def save_to_file(self, path: Path, target: str = "to") -> int:
        path = Path(path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            values = self.get_bcc_list() if target == "bcc" else self.get_to_list()
            path.write_text("\n".join(values), encoding="utf-8")
            return len(values)
        except Exception:
            log.exception("save_to_file: %s", path)
            return 0

    def validate(self, remove_invalid: bool = True) -> Dict[str, List[str]]:
        invalid: Dict[str, List[str]] = {"to": [], "bcc": []}
        with self._lock:
            if remove_invalid:
                good_to: List[str] = []
                good_bcc: List[str] = []
                for email in self._to:
                    (good_to if validate_email_address(email) else invalid["to"]).append(email)
                for email in self._bcc:
                    (good_bcc if validate_email_address(email) else invalid["bcc"]).append(email)
                self._to = good_to
                self._bcc = good_bcc
        return invalid

    def add_default_recipients(self, default_bcc: Optional[List[str]]) -> int:
        """Lägg till standard-Bcc, deduplicerat."""
        count = 0
        for email in default_bcc or []:
            if validate_email_address(email):
                count += self.add_to_bcc(email)
        return count

    def _notify(self) -> None:
        if self._bus:
            try:
                self._bus.publish(
                    "recipients.updated",
                    {
                        "to_count": len(self._to),
                        "bcc_count": len(self._bcc),
                        "total": len(self._to) + len(self._bcc),
                    },
                )
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# AddContactDialog (PyQt6)
# ═══════════════════════════════════════════════════════════════════════════

class AddContactDialog(QDialog):
    """Lägg till / Redigera kontakt via QDialog."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        store_adapter: Optional[_StoreAdapter] = None,
        theme_engine: Optional[StyleEngine] = None,
        edit_contact: Optional[Contact] = None,
    ) -> None:
        super().__init__(parent)
        self._adapter = store_adapter
        self._style = theme_engine
        self._edit = edit_contact
        self._result: Optional[Contact] = None
        self._checks: Dict[str, QCheckBox] = {}

        is_edit = edit_contact is not None
        self.setWindowTitle("✏️ Redigera kontakt" if is_edit else "➕ Ny kontakt")
        self.setModal(True)
        self.setMinimumWidth(440)

        self._build_ui()
        if is_edit and edit_contact is not None:
            self._prefill(edit_contact)

    def _c(self) -> Dict[str, str]:
        if self._style:
            return self._style.get_colors()
        return get_colors("dark")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("<b>✉️ E-postadress (krävs)</b>"))
        self._email = QLineEdit()
        self._email.setPlaceholderText("namn@example.com")
        self._email.setMinimumHeight(32)
        layout.addWidget(self._email)

        layout.addWidget(QLabel("<b>👤 Namn</b>"))
        self._name = QLineEdit()
        self._name.setPlaceholderText("Förnamn Efternamn")
        self._name.setMinimumHeight(32)
        layout.addWidget(self._name)

        layout.addWidget(QLabel("<b>🏢 Företag</b>"))
        self._company = QLineEdit()
        self._company.setPlaceholderText("Företagsnamn (valfritt)")
        self._company.setMinimumHeight(32)
        layout.addWidget(self._company)

        cat_box = QGroupBox("🏷️ Kategorier")
        cat_layout = QGridLayout(cat_box)
        cat_layout.setSpacing(8)

        existing = sorted(self._adapter.categories()) if self._adapter else []
        if existing:
            row = 0
            col = 0
            for category in existing:
                checkbox = QCheckBox(category)
                cat_layout.addWidget(checkbox, row, col)
                self._checks[category] = checkbox
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
        else:
            cat_layout.addWidget(QLabel("Inga kategorier ännu."), 0, 0)
        layout.addWidget(cat_box)

        layout.addWidget(QLabel("<b>➕ Lägg till ny kategori</b>"))
        self._new_cat = QLineEdit()
        self._new_cat.setPlaceholderText("t.ex. Kund, Partner (kommaseparera)")
        self._new_cat.setMinimumHeight(32)
        layout.addWidget(self._new_cat)

        layout.addSpacing(8)

        buttons = QHBoxLayout()
        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.setProperty("cssClass", "danger")
        btn_cancel.setMinimumHeight(36)
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)
        buttons.addStretch()

        btn_save = QPushButton("💾 Spara kontakt")
        btn_save.setProperty("cssClass", "success")
        btn_save.setDefault(True)
        btn_save.setMinimumHeight(36)
        btn_save.clicked.connect(self._on_save)
        buttons.addWidget(btn_save)
        layout.addLayout(buttons)

    def _prefill(self, contact: Contact) -> None:
        self._email.setText(contact.email)
        self._email.setReadOnly(True)
        self._name.setText(contact.name)
        self._company.setText(contact.company)
        for category, checkbox in self._checks.items():
            checkbox.setChecked(category in contact.categories)

    def _collect_categories(self) -> List[str]:
        categories = [
            category
            for category, checkbox in self._checks.items()
            if checkbox.isChecked()
        ]
        for part in self._new_cat.text().split(","):
            part = part.strip()
            if part and part not in categories:
                categories.append(part)
        return categories

    def _on_save(self) -> None:
        email = self._email.text().strip()
        if not email:
            QMessageBox.warning(self, "E-post saknas", "Ange en e-postadress.")
            return
        if not validate_email_address(email):
            QMessageBox.warning(
                self,
                "Ogiltig e-post",
                f"'{email}' är inte en giltig e-postadress.",
            )
            return

        categories = self._collect_categories()
        if self._adapter:
            self._result = self._adapter.upsert(
                email=email,
                name=self._name.text().strip(),
                company=self._company.text().strip(),
                categories=categories,
            )
            self._adapter.save()
        log.info("AddContactDialog: sparade %s", email)
        self.accept()

    def show(self) -> Optional[Contact]:
        """
        Visa dialog modalt och returnera resultatet.

        (API-kompatibilitet: kör exec() och returnerar Contact eller None.
        Anropas enbart från applikationskod – Qt:s interna show-anrop
        påverkas inte, då QWidget.show() inte är en virtuell metod.)
        """
        self.exec()
        return self._result


# ═══════════════════════════════════════════════════════════════════════════
# Avatar-hjälpare
# ═══════════════════════════════════════════════════════════════════════════

def _make_avatar(initials: str, color_hex: str, size: int = 32) -> QIcon:
    """Skapa en rund avatar med initialer."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color_hex))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    painter.setPen(QColor("#FFFFFF"))
    font = QFont()
    font.setBold(True)
    font.setPointSize(int(size * 0.4))
    painter.setFont(font)
    painter.drawText(pixmap.rect(), int(Qt.AlignmentFlag.AlignCenter), initials)
    painter.end()
    return QIcon(pixmap)


def _color_for_category(category: str, colors: Dict[str, str]) -> str:
    """Konsekvent färg per kategori (deterministisk – v5.4).

    Använder sum(ord) istället för hash() så att färgerna är stabila
    mellan processstarter (hash() slumpas per process i Python).
    """
    palette = [
        colors.get("accent", "#5C9EFF"),
        colors.get("success", "#2ECC71"),
        colors.get("warning", "#F5A623"),
        colors.get("error", "#E74C3C"),
        "#9B59B6",
        "#1ABC9C",
        "#E67E22",
        "#3498DB",
    ]
    if not category:
        return palette[0]
    stable = sum(ord(ch) for ch in category)
    return palette[stable % len(palette)]


# ═══════════════════════════════════════════════════════════════════════════
# AddressBookDialog (PyQt6) – FÖRBÄTTRAD
# ═══════════════════════════════════════════════════════════════════════════

class AddressBookDialog(QDialog):
    """Förbättrad adressbok med kategorier, avatarer och kvarstående dialog.

    Viktig regel:

    - Dialogen stängs INTE när användaren trycker på "Lägg till som To/Bcc".
    - Om on_add-callback finns läggs adresser till direkt i mottagarlistan.
    - Användaren stänger själv dialogen via "Klar" eller "Avbryt".
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        contact_store: Any = None,
        theme_engine: Optional[StyleEngine] = None,
        on_add: Optional[Callable[[List[str], str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self._adapter = _StoreAdapter(contact_store)
        self._style = theme_engine
        self._on_add_callback = on_add
        self._result: Dict[str, List[str]] = {"to": [], "bcc": []}
        self._current_category: str = "__all__"

        self.setWindowTitle("📒 Adressbok")
        self.setModal(True)
        self.setMinimumSize(820, 600)
        self.resize(900, 640)

        self._adapter.reload()
        # (v5.5) Gruppsortering: "alpha" (A-Ö) eller "count" (flest först)
        self._categories_sort: str = "alpha"
        self._build_ui()
        self._populate_categories()
        self._populate_contacts()
        self._update_group_actions()

    def _c(self) -> Dict[str, str]:
        if self._style:
            return self._style.get_colors()
        return get_colors("dark")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        top = QHBoxLayout()
        search_label = QLabel("🔍")
        search_label.setStyleSheet("font-size: 14pt;")
        top.addWidget(search_label)

        self._search = QLineEdit()
        self._search.setPlaceholderText(
            "Sök namn, e-post, företag eller kategori…"
        )
        self._search.setMinimumHeight(34)
        self._search.textChanged.connect(self._populate_contacts)
        top.addWidget(self._search, stretch=1)

        top.addWidget(QLabel("Sortera:"))
        self._sort_cb = QComboBox()
        self._sort_cb.addItems([
            "Namn (A-Ö)",
            "Namn (Ö-A)",
            "E-post (A-Ö)",
            "E-post (Ö-A)",
            "Företag (A-Ö)",
            "Företag (Ö-A)",
            "Kategori (A-Ö)",
            "Kategori (Ö-A)",
        ])
        self._sort_cb.setMinimumHeight(34)
        self._sort_cb.currentIndexChanged.connect(
            lambda *_: self._populate_contacts()
        )
        top.addWidget(self._sort_cb)

        btn_new = QPushButton("➕ Ny kontakt")
        btn_new.setProperty("cssClass", "success")
        btn_new.setMinimumHeight(34)
        btn_new.clicked.connect(self._add_new)
        top.addWidget(btn_new)

        layout.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._cat_list = QListWidget()
        self._cat_list.setMinimumWidth(200)
        self._cat_list.setMaximumWidth(280)
        self._cat_list.currentItemChanged.connect(
            lambda *_: self._on_category_changed()
        )
        # (v5.5) Högerklick på kategori: lägg till hela gruppen / sortera
        self._cat_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._cat_list.customContextMenuRequested.connect(
            self._show_category_context_menu
        )
        splitter.addWidget(self._cat_list)

        self._right_stack = QStackedWidget()

        self._contact_list = QListWidget()
        self._contact_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )
        self._contact_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._contact_list.customContextMenuRequested.connect(
            self._show_contact_context_menu
        )
        self._contact_list.itemSelectionChanged.connect(self._update_info)
        self._contact_list.itemDoubleClicked.connect(self._on_double_click)
        self._right_stack.addWidget(self._contact_list)

        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon = QLabel("📭")
        empty_icon.setStyleSheet("font-size: 64pt;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)
        empty_title = QLabel("Inga kontakter att visa")
        empty_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)
        empty_hint = QLabel("Klicka <b>➕ Ny kontakt</b> för att lägga till.")
        empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_hint)
        self._right_stack.addWidget(empty_widget)

        splitter.addWidget(self._right_stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, stretch=1)

        info_row = QHBoxLayout()
        self._info_lbl = QLabel("")
        info_row.addWidget(self._info_lbl, stretch=1)

        btn_all = QPushButton("☑ Markera alla")
        btn_all.clicked.connect(self._select_all)
        info_row.addWidget(btn_all)

        btn_none = QPushButton("☐ Avmarkera")
        btn_none.clicked.connect(self._select_none)
        info_row.addWidget(btn_none)

        btn_edit = QPushButton("✏️ Redigera")
        btn_edit.clicked.connect(self._edit_selected)
        info_row.addWidget(btn_edit)

        btn_delete = QPushButton("🗑️ Ta bort")
        btn_delete.setProperty("cssClass", "danger")
        btn_delete.clicked.connect(self._delete_selected)
        info_row.addWidget(btn_delete)

        layout.addLayout(info_row)

        # (v5.5) Lägg till HELA kategorin/adressboken direkt i To/Bcc
        group_row = QHBoxLayout()
        self._group_actions_label = QLabel("")
        self._group_actions_label.setStyleSheet("font-weight: bold;")
        group_row.addWidget(self._group_actions_label, stretch=1)

        self._btn_all_bcc = QPushButton("➕ Alla → Bcc")
        self._btn_all_bcc.setMinimumHeight(34)
        self._btn_all_bcc.clicked.connect(
            lambda: self._emit_add_all("bcc")
        )
        group_row.addWidget(self._btn_all_bcc)

        self._btn_all_to = QPushButton("➕ Alla → To")
        self._btn_all_to.setProperty("cssClass", "accent")
        self._btn_all_to.setMinimumHeight(34)
        self._btn_all_to.clicked.connect(
            lambda: self._emit_add_all("to")
        )
        group_row.addWidget(self._btn_all_to)

        layout.addLayout(group_row)

        self._feedback_lbl = QLabel(
            "Välj kontakter och klicka på Lägg till som To/Bcc. "
            "Dialogen stannar öppen."
        )
        self._feedback_lbl.setWordWrap(True)
        self._feedback_lbl.setProperty("cssClass", "subtext")
        layout.addWidget(self._feedback_lbl)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)

        button_bar = QHBoxLayout()
        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.setProperty("cssClass", "danger")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.clicked.connect(self._on_cancel)
        button_bar.addWidget(btn_cancel)

        btn_done = QPushButton("✅ Klar")
        btn_done.setMinimumHeight(38)
        btn_done.clicked.connect(self._on_done)
        button_bar.addWidget(btn_done)

        button_bar.addStretch()

        btn_bcc = QPushButton("➕ Lägg till som Bcc")
        btn_bcc.setMinimumHeight(38)
        btn_bcc.clicked.connect(self._on_add_bcc)
        button_bar.addWidget(btn_bcc)

        btn_to = QPushButton("➕ Lägg till som To")
        btn_to.setProperty("cssClass", "accent")
        btn_to.setMinimumHeight(38)
        btn_to.setDefault(True)
        btn_to.clicked.connect(self._on_add_to)
        button_bar.addWidget(btn_to)

        layout.addLayout(button_bar)

    # ── Kategorisidopanel ──────────────────────────────────────────
    def _populate_categories(self) -> None:
        previous_category = getattr(self, "_current_category", "__all__")
        self._cat_list.clear()
        colors = self._c()

        grouped = self._adapter.grouped_by_category()
        total = sum(len(items) for items in grouped.values())

        all_item = QListWidgetItem(f"👥  Alla kontakter  ({total})")
        all_item.setData(Qt.ItemDataRole.UserRole, "__all__")
        font = all_item.font()
        font.setBold(True)
        all_item.setFont(font)
        self._cat_list.addItem(all_item)

        # (v5.5) Gruppsortering: A-Ö eller flest mottagare först
        if getattr(self, "_categories_sort", "alpha") == "count":
            sorted_categories = sorted(
                grouped.keys(),
                key=lambda category: -len(grouped[category]),
            )
        else:
            sorted_categories = sorted(
                grouped.keys(),
                key=lambda category: (category or "").lower(),
            )
        for category in sorted_categories:
            count = len(grouped[category])
            color = _color_for_category(category, colors)
            initials = category[:2].upper() if category else "?"
            icon = _make_avatar(initials, color, size=24)
            item = QListWidgetItem(icon, f"  {category}  ({count})")
            item.setData(Qt.ItemDataRole.UserRole, category)
            self._cat_list.addItem(item)

        # Försök behålla tidigare vald kategori om den fortfarande finns.
        target_row = 0
        for row in range(self._cat_list.count()):
            item = self._cat_list.item(row)
            if item and item.data(Qt.ItemDataRole.UserRole) == previous_category:
                target_row = row
                break
        self._cat_list.setCurrentRow(target_row)
        self._update_group_actions()

    # ── (v5.5) Hela grupper: lägg till alla i To/Bcc + gruppsortering ──
    def _category_emails(self, category: str) -> List[str]:
        """E-postadresser för en hel kategori (eller alla kontakter)."""
        if category == "__all__":
            return [contact.email for contact in self._adapter.all()]
        grouped = self._adapter.grouped_by_category()
        return [
            contact.email
            for contact in grouped.get(category, [])
        ]

    def _update_group_actions(self) -> None:
        """Uppdatera gruppåtgärdsraden med namn + antal för vald grupp."""
        category = self._current_category
        emails = self._category_emails(category)
        count = len(emails)
        name = "Alla kontakter" if category == "__all__" else category
        self._group_actions_label.setText(
            f"📚 {name}: {count} mottagare"
        )
        self._btn_all_to.setEnabled(count > 0)
        self._btn_all_bcc.setEnabled(count > 0)
        self._btn_all_to.setText(f"➕ Alla ({count}) → To")
        self._btn_all_bcc.setText(f"➕ Alla ({count}) → Bcc")

    def _emit_add_all(self, target: str) -> None:
        """Lägg till HELA den valda gruppen i To/Bcc (dialogen stannar)."""
        emails = self._category_emails(self._current_category)
        if not emails:
            QMessageBox.warning(
                self,
                "Ingen grupp",
                "Välj en kategori med kontakter först "
                "(eller Alla kontakter).",
            )
            return
        self._emit_add(emails, target)

    def _show_category_context_menu(self, pos: Any) -> None:
        """Högerklick på kategorilistan: lägg till grupp / sortera."""
        item = self._cat_list.itemAt(pos)
        if item is None:
            return
        category = item.data(Qt.ItemDataRole.UserRole) or "__all__"
        emails = self._category_emails(category)
        self._cat_list.setCurrentItem(item)

        menu = QMenu(self)
        if emails:
            act_to = menu.addAction(
                f"➕ Lägg till alla ({len(emails)}) som To"
            )
            act_bcc = menu.addAction(
                f"➕ Lägg till alla ({len(emails)}) som Bcc"
            )
            menu.addSeparator()
        act_alpha = menu.addAction("↕ Sortera A-Ö")
        act_count = menu.addAction("↕ Sortera efter antal (flest först)")

        chosen = menu.exec(self._cat_list.viewport().mapToGlobal(pos))
        if chosen is None:
            return
        if chosen in (act_to, act_bcc):
            self._current_category = category
            self._emit_add(emails, "to" if chosen == act_to else "bcc")
        elif chosen == act_alpha:
            self._categories_sort = "alpha"
            self._populate_categories()
        elif chosen == act_count:
            self._categories_sort = "count"
            self._populate_categories()

    def _on_category_changed(self) -> None:
        item = self._cat_list.currentItem()
        if item:
            self._current_category = (
                item.data(Qt.ItemDataRole.UserRole) or "__all__"
            )
            self._populate_contacts()
            self._update_group_actions()

    # ── Kontaktlista ───────────────────────────────────────────────
    def _populate_contacts(self) -> None:
        self._contact_list.clear()
        colors = self._c()

        if self._current_category == "__all__":
            contacts = self._adapter.all()
        else:
            grouped = self._adapter.grouped_by_category()
            contacts = grouped.get(self._current_category, [])

        query = self._search.text().strip().lower()
        if query:
            contacts = [
                contact
                for contact in contacts
                if query in contact.email.lower()
                or query in contact.name.lower()
                or query in contact.company.lower()
                or any(
                    query in category.lower()
                    for category in contact.categories
                )
            ]

        contacts = self._sorted_contacts(contacts)

        if not contacts:
            self._right_stack.setCurrentIndex(1)
            self._update_info()
            return

        self._right_stack.setCurrentIndex(0)
        for contact in contacts:
            category_for_color = (
                contact.categories[0] if contact.categories else "Okategoriserad"
            )
            color = _color_for_category(category_for_color, colors)
            icon = _make_avatar(contact.initials(), color, size=36)

            display = contact.name or contact.email
            sub_parts: List[str] = []
            if contact.name and contact.email:
                sub_parts.append(contact.email)
            if contact.company:
                sub_parts.append(contact.company)
            if contact.categories:
                sub_parts.append(", ".join(contact.categories[:2]))
            sub = "  ·  ".join(sub_parts)
            text = f"  {display}\n  {sub}" if sub else f"  {display}"

            item = QListWidgetItem(icon, text)
            item.setData(Qt.ItemDataRole.UserRole, contact.email)
            item.setToolTip(contact.display_name())
            self._contact_list.addItem(item)

        self._update_info()

    def _sorted_contacts(self, contacts: List[Contact]) -> List[Contact]:
        """Sortera kontakter enligt vald sorteringsmodell i adressboken."""
        mode = (
            self._sort_cb.currentText()
            if hasattr(self, "_sort_cb")
            else "Namn (A-Ö)"
        )
        reverse = "Ö-A" in mode

        if mode.startswith("E-post"):
            return sorted(
                contacts,
                key=lambda contact: contact.email.lower(),
                reverse=reverse,
            )
        if mode.startswith("Företag"):
            return sorted(
                contacts,
                key=lambda contact: (
                    (contact.company or "zzz").lower(),
                    (contact.name or contact.email).lower(),
                ),
                reverse=reverse,
            )
        if mode.startswith("Kategori"):
            return sorted(
                contacts,
                key=lambda contact: (
                    (contact.categories[0].lower() if contact.categories else "zzz"),
                    (contact.name or contact.email).lower(),
                ),
                reverse=reverse,
            )
        return sorted(
            contacts,
            key=lambda contact: (contact.name or contact.email).lower(),
            reverse=reverse,
        )

    def _update_info(self) -> None:
        selected = len(self._get_selected_emails())
        total = self._adapter.count()
        visible = self._contact_list.count()
        current_category = (
            self._current_category
            if self._current_category != "__all__"
            else "Alla"
        )
        sort_mode = (
            self._sort_cb.currentText()
            if hasattr(self, "_sort_cb")
            else "Namn (A-Ö)"
        )
        self._info_lbl.setText(
            f"📊  {selected} markerade · {visible} synliga · "
            f"{total} totalt · Kategori: {current_category} · "
            f"Sortering: {sort_mode}"
        )

    def _get_selected_emails(self) -> List[str]:
        emails: List[str] = []
        for item in self._contact_list.selectedItems():
            email = item.data(Qt.ItemDataRole.UserRole)
            if email and validate_email_address(email):
                emails.append(email)
        return emails

    def _get_selected_contact(self) -> Optional[Contact]:
        emails = self._get_selected_emails()
        return self._adapter.get(emails[0]) if len(emails) == 1 else None

    def _selected_contacts(self) -> List[Contact]:
        """Returnera Contact-objekt för markerade e-postadresser (v5.4)."""
        contacts: List[Contact] = []
        seen: Set[str] = set()
        for email in self._get_selected_emails():
            key = email.lower()
            if key in seen:
                continue
            seen.add(key)
            contact = self._adapter.get(key)
            if contact is not None:
                contacts.append(contact)
        return contacts

    def _select_all(self) -> None:
        self._contact_list.selectAll()

    def _select_none(self) -> None:
        self._contact_list.clearSelection()

    def _set_feedback(self, message: str, success: bool = True) -> None:
        colors = self._c()
        feedback_color = (
            colors.get("success", "#2ECC71")
            if success
            else colors.get("warning", "#E67E22")
        )
        self._feedback_lbl.setText(message)
        self._feedback_lbl.setStyleSheet(
            f"font-weight: bold; color: {feedback_color};"
        )

    def _add_new(self) -> None:
        dialog = AddContactDialog(self, self._adapter, self._style)
        result = dialog.show()
        if result:
            self._populate_categories()
            self._populate_contacts()
            self._set_feedback(f"✅ {result.display_name()} har lagts till.")

    def _edit_selected(self) -> None:
        contact = self._get_selected_contact()
        if contact is None:
            QMessageBox.warning(
                self,
                "Ingen vald",
                "Markera exakt en kontakt att redigera.",
            )
            return
        dialog = AddContactDialog(
            self, self._adapter, self._style, edit_contact=contact
        )
        if dialog.show():
            self._populate_categories()
            self._populate_contacts()
            self._set_feedback(f"✅ {contact.email} har uppdaterats.")

    def _delete_selected(self) -> None:
        emails = self._get_selected_emails()
        if not emails:
            return
        count = len(emails)
        prompt = (
            f"Ta bort {emails[0]}?"
            if count == 1
            else f"Ta bort {count} kontakter?"
        )
        reply = QMessageBox.question(
            self,
            "Bekräfta",
            prompt,
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        for email in emails:
            self._adapter.delete(email)
        self._adapter.save()
        self._populate_categories()
        self._populate_contacts()
        self._set_feedback(f"🗑️ {count} kontakt(er) togs bort.")

    def _on_double_click(self, _item: QListWidgetItem) -> None:
        contact = self._get_selected_contact()
        if not contact:
            return
        dialog = AddContactDialog(
            self, self._adapter, self._style, edit_contact=contact
        )
        dialog.show()
        self._populate_categories()
        self._populate_contacts()

    def _show_contact_context_menu(self, pos: Any) -> None:
        if self._contact_list.count() == 0:
            return

        item = self._contact_list.itemAt(pos)
        if item is not None and not item.isSelected():
            self._contact_list.setCurrentItem(item)
            item.setSelected(True)

        emails = self._get_selected_emails()

        menu = QMenu(self)
        act_to = menu.addAction("➕ Lägg till som To")
        act_bcc = menu.addAction("➕ Lägg till som Bcc")
        menu.addSeparator()
        act_copy = menu.addAction("📋 Kopiera e-post")
        act_copy_all = menu.addAction("📋 Kopiera namn + e-post")
        menu.addSeparator()
        act_edit = menu.addAction("✏️ Redigera kontakt")
        act_delete = menu.addAction("🗑️ Ta bort kontakt")

        chosen = menu.exec(self._contact_list.viewport().mapToGlobal(pos))

        if chosen == act_to:
            self._emit_add(emails, "to")
        elif chosen == act_bcc:
            self._emit_add(emails, "bcc")
        elif chosen == act_copy:
            if emails:
                QApplication.clipboard().setText(
                    "\n".join(emails), QClipboard.Mode.Clipboard
                )
                self._set_feedback(
                    f"📋 {len(emails)} adress(er) kopierade."
                )
        elif chosen == act_copy_all:
            contacts = self._selected_contacts()
            if contacts:
                lines = [contact.display_name() for contact in contacts]
                QApplication.clipboard().setText(
                    "\n".join(lines), QClipboard.Mode.Clipboard
                )
                self._set_feedback(
                    f"📋 {len(lines)} kontakt(er) kopierade."
                )
        elif chosen == act_edit:
            self._edit_selected()
        elif chosen == act_delete:
            self._delete_selected()

    def _emit_add(self, emails: List[str], target: str) -> None:
        if not emails:
            QMessageBox.warning(
                self, "Ingen markerad", "Välj minst en kontakt."
            )
            return

        deduped: List[str] = []
        seen: Set[str] = set()
        for email in emails:
            key = email.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(email)

        # Om callback finns, lägg till direkt i mottagarlistan
        # utan att stänga dialogen.
        if self._on_add_callback is not None:
            try:
                self._on_add_callback(deduped, target)
            except Exception:
                log.exception(
                    "AddressBookDialog on_add_callback misslyckades"
                )
                QMessageBox.critical(
                    self, "Fel", "Kunde inte lägga till mottagare."
                )
                return
            self._set_feedback(
                f"✅ {len(deduped)} adress(er) lades till i "
                f"{target.upper()}."
            )
            return

        # Fallback/kompatibilitet: spara resultat lokalt
        # men håll dialogen öppen.
        bucket = self._result["bcc" if target == "bcc" else "to"]
        existing = {email.lower() for email in bucket}
        added = 0
        for email in deduped:
            if email.lower() not in existing:
                bucket.append(email)
                existing.add(email.lower())
                added += 1
        self._set_feedback(
            f"✅ {added} adress(er) markerades för {target.upper()}."
        )

    def _on_add_to(self) -> None:
        self._emit_add(self._get_selected_emails(), "to")

    def _on_add_bcc(self) -> None:
        self._emit_add(self._get_selected_emails(), "bcc")

    def _on_done(self) -> None:
        self.accept()

    def _on_cancel(self) -> None:
        self._result = {"to": [], "bcc": []}
        self.reject()

    def show(self) -> Dict[str, List[str]]:
        """
        Visa dialog modalt och returnera ackumulerat resultat.

        (API-kompatibilitet: kör exec() och returnerar resultat-dict.
        Anropas enbart från applikationskod – Qt:s interna show-anrop
        påverkas inte, då QWidget.show() inte är en virtuell metod.)
        """
        self.exec()
        return self._result


# ═══════════════════════════════════════════════════════════════════════════
# Steg-header (återanvändbar)
# ═══════════════════════════════════════════════════════════════════════════

def _make_step_header(num: int, title: str, emoji: str, css_class: str) -> QFrame:
    """Skapa en färgglad steg-header."""
    circled = {1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤"}
    frame = QFrame()
    frame.setProperty("cssClass", css_class)
    frame.setFixedHeight(40)
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(16, 0, 16, 0)
    label = QLabel(f"  {circled.get(num, str(num))}   {emoji}   {title}")
    label.setStyleSheet(
        "color: #FFFFFF; font-size: 12pt; font-weight: bold; "
        "background: transparent;"
    )
    layout.addWidget(label)
    return frame


# ═══════════════════════════════════════════════════════════════════════════
# RecipientsTab (PyQt6) – STEG-FÖR-STEG, INGEN CC
# ═══════════════════════════════════════════════════════════════════════════

class RecipientsTab(QWidget):
    """Mottagare-tab med 3-stegs wizard:

    ① Importera – Adressbok / fil-import
    ② Lägg till – Snabb-input för To/Bcc
    ③ Granska – To/Bcc-listor sida vid sida
    """

    recipientsChanged = pyqtSignal(dict)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        store: Optional[RecipientStore] = None,
        event_bus: Any = None,
        theme_engine: Optional[StyleEngine] = None,
        address_dir: Optional[Path] = None,
        contact_store: Any = None,
    ) -> None:
        super().__init__(parent)
        self._store = store or RecipientStore(event_bus=event_bus)
        self._bus = event_bus
        self._style = theme_engine
        self._adr_dir = Path(address_dir) if address_dir else None
        self._cs = contact_store

        self._build_ui()
        self._bind_events()
        self._refresh_file_combo()
        self._refresh()

    def _c(self) -> Dict[str, str]:
        if self._style:
            return self._style.get_colors()
        return get_colors("dark")

    # ── UI-bygge ────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 12)

        # STEG ① Importera
        layout.addWidget(
            _make_step_header(1, "Importera kontakter", "📥", "step-blue")
        )
        step1 = QHBoxLayout()
        step1.setContentsMargins(16, 8, 16, 8)

        btn_ab = QPushButton("📒  Öppna adressbok")
        btn_ab.setProperty("cssClass", "accent")
        btn_ab.setMinimumHeight(36)
        btn_ab.clicked.connect(self._open_ab)
        step1.addWidget(btn_ab)

        btn_new_contact = QPushButton("➕ Ny kontakt")
        btn_new_contact.setProperty("cssClass", "success")
        btn_new_contact.setMinimumHeight(36)
        btn_new_contact.clicked.connect(self._add_new_contact_from_tab)
        step1.addWidget(btn_new_contact)

        step1.addSpacing(20)
        step1.addWidget(QLabel("eller importera fil:"))

        self._file_cb = QComboBox()
        self._file_cb.setMinimumWidth(180)
        self._file_cb.setMinimumHeight(32)
        step1.addWidget(self._file_cb)

        btn_to = QPushButton("→ To")
        btn_to.setMinimumHeight(32)
        btn_to.clicked.connect(lambda: self._import("to"))
        step1.addWidget(btn_to)

        btn_bcc = QPushButton("→ Bcc")
        btn_bcc.setMinimumHeight(32)
        btn_bcc.clicked.connect(lambda: self._import("bcc"))
        step1.addWidget(btn_bcc)

        step1.addStretch()
        layout.addLayout(step1)

        # STEG ② Lägg till manuellt
        layout.addWidget(
            _make_step_header(2, "Lägg till manuellt", "✍️", "step-green")
        )
        step2 = QHBoxLayout()
        step2.setContentsMargins(16, 8, 16, 8)
        step2.addWidget(QLabel("E-postadress:"))

        self._manual_email = QLineEdit()
        self._manual_email.setPlaceholderText("namn@example.com")
        self._manual_email.setMinimumHeight(32)
        self._manual_email.returnPressed.connect(self._add_manual_to)
        step2.addWidget(self._manual_email, stretch=1)

        btn_add_to = QPushButton("➕  Lägg till To")
        btn_add_to.setProperty("cssClass", "accent")
        btn_add_to.setMinimumHeight(32)
        btn_add_to.clicked.connect(self._add_manual_to)
        step2.addWidget(btn_add_to)

        btn_add_bcc = QPushButton("➕  Lägg till Bcc")
        btn_add_bcc.setMinimumHeight(32)
        btn_add_bcc.clicked.connect(self._add_manual_bcc)
        step2.addWidget(btn_add_bcc)
        layout.addLayout(step2)

        # STEG ③ Granska
        layout.addWidget(
            _make_step_header(3, "Granska mottagare", "📋", "step-orange")
        )
        review = QHBoxLayout()
        review.setContentsMargins(16, 8, 16, 8)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._to_list = self._make_list(
            "📨 To – direktmottagare", "Synliga för alla mottagare"
        )
        self._bcc_list = self._make_list(
            "🔒 Bcc – dold kopia", "Dolda för andra mottagare"
        )
        splitter.addWidget(self._to_list["frame"])
        splitter.addWidget(self._bcc_list["frame"])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        review.addWidget(splitter, stretch=1)
        layout.addLayout(review)

        bottom = QHBoxLayout()
        bottom.setContentsMargins(16, 8, 16, 8)
        bottom.addStretch()
        btn_clear = QPushButton("🗑  Rensa alla mottagare")
        btn_clear.setProperty("cssClass", "danger")
        btn_clear.setMinimumHeight(34)
        btn_clear.clicked.connect(self._clear_all)
        bottom.addWidget(btn_clear)
        layout.addLayout(bottom)

        layout.addStretch()
        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _make_list(self, title: str, hint: str) -> Dict[str, Any]:
        frame = QGroupBox(title)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(4)

        hint_label = QLabel(hint)
        hint_label.setProperty("cssClass", "subtext")
        frame_layout.addWidget(hint_label)

        lst = QListWidget()
        lst.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        lst.setMinimumHeight(180)
        frame_layout.addWidget(lst, stretch=1)

        button_row = QHBoxLayout()
        btn_remove = QPushButton("➖ Ta bort markerade")
        btn_remove.setProperty("cssClass", "danger")
        btn_remove.setMinimumHeight(30)
        button_row.addWidget(btn_remove)

        btn_copy = QPushButton("📋 Kopiera")
        btn_copy.setMinimumHeight(30)
        button_row.addWidget(btn_copy)
        button_row.addStretch()

        count_label = QLabel("0 adresser")
        count_label.setStyleSheet("font-weight: bold;")
        button_row.addWidget(count_label)
        frame_layout.addLayout(button_row)

        return {
            "frame": frame,
            "list": lst,
            "rm": btn_remove,
            "cp": btn_copy,
            "count": count_label,
        }

    def _wire_list(
        self,
        data: Dict[str, Any],
        remove_fn: Callable[[str], bool],
    ) -> None:
        data["rm"].clicked.connect(
            lambda: self._remove_selected(data["list"], remove_fn)
        )
        data["cp"].clicked.connect(lambda: self._copy_list(data["list"]))

    def _bind_events(self) -> None:
        self._wire_list(self._to_list, self._store.remove_from_to)
        self._wire_list(self._bcc_list, self._store.remove_from_bcc)

        if self._bus:
            try:
                # Bundna metoder – lambdas GC:as av weakrefs (v5.4)
                self._bus.subscribe(
                    "recipients.updated", self._on_recipients_updated
                )
                self._bus.subscribe(
                    "contacts.updated", self._on_contacts_updated
                )
            except Exception:
                log.exception("RecipientsTab: subscribe")

    def _on_recipients_updated(
        self, data: Optional[Dict[str, Any]] = None
    ) -> None:
        QTimer.singleShot(0, self._refresh)

    def _on_contacts_updated(
        self, data: Optional[Dict[str, Any]] = None
    ) -> None:
        QTimer.singleShot(0, self._refresh_file_combo)

    # ── Manuell input ──────────────────────────────────────────────
    def _add_manual_to(self) -> None:
        self._add_manual(self._store.add_to_list)

    def _add_manual_bcc(self) -> None:
        self._add_manual(self._store.add_to_bcc)

    def _add_manual(self, add_fn: Callable[[str], int]) -> None:
        email = self._manual_email.text().strip()
        if not email:
            return
        if validate_email_address(email):
            add_fn(email)
            self._manual_email.clear()
            self._manual_email.setFocus()
            self._refresh()
        else:
            QMessageBox.warning(
                self,
                "Ogiltig",
                f"'{email}' är inte en giltig e-postadress.",
            )

    # ── Lista-åtgärder ────────────────────────────────────────────
    def _remove_selected(
        self,
        lst: QListWidget,
        remove_fn: Callable[[str], bool],
    ) -> None:
        for item in reversed(lst.selectedItems()):
            remove_fn(item.text())
        self._refresh()

    def _copy_list(self, lst: QListWidget) -> None:
        items = [lst.item(index).text() for index in range(lst.count())]
        if items:
            try:
                QApplication.clipboard().setText(
                    "\n".join(items), QClipboard.Mode.Clipboard
                )
                QMessageBox.information(
                    self, "Kopierat", f"✅ {len(items)} adresser kopierade."
                )
            except Exception:
                pass

    # ── Fil-import ────────────────────────────────────────────────
    def _refresh_file_combo(self) -> None:
        if not self._adr_dir or not self._adr_dir.exists():
            return
        try:
            files = sorted(
                path.name
                for path in self._adr_dir.iterdir()
                if path.suffix.lower() in (".json", ".txt")
            )
            current = self._file_cb.currentText()
            self._file_cb.clear()
            self._file_cb.addItems(files)
            if current in files:
                self._file_cb.setCurrentText(current)
        except Exception:
            pass

    def _import(self, target: str) -> None:
        filename = self._file_cb.currentText()
        if not filename or not self._adr_dir:
            QMessageBox.warning(self, "Ingen fil", "Välj en fil i listan.")
            return
        count = self._store.load_from_file(self._adr_dir / filename, target)
        self._refresh()
        QMessageBox.information(
            self,
            "Import klar",
            f"✅ {count} adresser → {target.upper()} från {filename}",
        )

    def _on_address_book_add(self, emails: List[str], target: str) -> None:
        """Direkt tillägg från adressboken utan att dialogen stängs."""
        added = 0
        for email in emails:
            if target == "bcc":
                added += self._store.add_to_bcc(email)
            else:
                added += self._store.add_to_list(email)
        self._refresh()
        if added:
            log.info(
                "AddressBook → %d adresser lades till i %s",
                added, target.upper(),
            )
        else:
            log.info(
                "AddressBook → inga nya adresser lades till i %s",
                target.upper(),
            )

    def _add_new_contact_from_tab(self) -> None:
        """Snabbknapp i mottagarflödet för att skapa ny kontakt direkt."""
        if not self._cs or AddContactDialog is None or _StoreAdapter is None:
            QMessageBox.warning(
                self, "Kontakter", "Kontaktredigering är inte tillgänglig."
            )
            return
        try:
            adapter = _StoreAdapter(self._cs)
            dialog = AddContactDialog(self, adapter, self._style)
            result = dialog.show()
            if result:
                self._refresh_file_combo()
                QMessageBox.information(
                    self,
                    "Kontakt sparad",
                    f"✅ {result.display_name()} har lagts till i adressboken.",
                )
        except Exception:
            log.exception("_add_new_contact_from_tab misslyckades")
            QMessageBox.critical(
                self, "Kontakter", "Kunde inte skapa ny kontakt."
            )

    def _open_ab(self) -> None:
        if not self._cs:
            QMessageBox.warning(
                self,
                "Ingen adressbok",
                "contacts.json är inte laddad.\n"
                "Kontrollera att filen finns i adresslistor/.",
            )
            return
        try:
            # Ladda om adressboken precis innan öppning så dialogen
            # alltid visar aktuell data.
            if hasattr(self._cs, "reload"):
                self._cs.reload()
            dialog = AddressBookDialog(
                self, self._cs, self._style, on_add=self._on_address_book_add
            )
            dialog.show()
            # Resultatet används främst för kompatibilitet;
            # on_add hanterar direkt tillägg.
        except Exception:
            log.exception("_open_ab misslyckades")
            QMessageBox.critical(
                self, "Fel", "Kunde inte öppna adressboken. Se loggen."
            )

    # ── Refresh / rensa ───────────────────────────────────────────
    def _refresh(self) -> None:
        def fill(bucket: Dict[str, Any], items: List[str]) -> None:
            bucket["list"].clear()
            for email in items:
                bucket["list"].addItem(email)
            count = len(items)
            bucket["count"].setText(
                f"{count} adress{'er' if count != 1 else ''}"
            )

        fill(self._to_list, self._store.get_to_list())
        fill(self._bcc_list, self._store.get_bcc_list())

        payload = self._store.get_all()
        self.recipientsChanged.emit(payload)

    def _clear_all(self) -> None:
        reply = QMessageBox.question(
            self,
            "Rensa alla",
            "Är du säker på att du vill ta bort ALLA mottagare?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._store.clear_all()
            self._refresh()

    # ── Publikt API ──────────────────────────────────────────────────
    def get_to_list(self) -> List[str]:
        return self._store.get_to_list()

    def get_bcc_list(self) -> List[str]:
        return self._store.get_bcc_list()

    def add_to_list(self, email: str) -> int:
        result = self._store.add_to_list(email)
        self._refresh()
        return result

    def add_to_bcc(self, email: str) -> int:
        result = self._store.add_to_bcc(email)
        self._refresh()
        return result

    def load_defaults(self, default_bcc: Optional[List[str]]) -> int:
        count = self._store.add_default_recipients(default_bcc)
        self._refresh()
        if self._bus:
            try:
                self._bus.publish(
                    "recipients.default_loaded",
                    {"bcc_count": len(self._store.get_bcc_list())},
                )
            except Exception:
                pass
        return count

    def set_address_dir(self, path: Path) -> None:
        self._adr_dir = Path(path) if path else None
        self._refresh_file_combo()

    def set_contact_store(self, store: Any) -> None:
        self._cs = store


# ═══════════════════════════════════════════════════════════════════════════
# Hjälpfunktioner
# ═══════════════════════════════════════════════════════════════════════════

def load_legacy_txt(txt_path: Path) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    """Ladda enkel legacy .txt-lista till To-format."""
    result: Dict[str, List[str]] = {"to": [], "bcc": []}
    stats: Dict[str, int] = {"loaded": 0, "invalid": 0}
    try:
        for line in Path(txt_path).read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if validate_email_address(line):
                result["to"].append(line)
                stats["loaded"] += 1
            else:
                stats["invalid"] += 1
    except Exception:
        log.exception("load_legacy_txt: %s", txt_path)
    return result, stats


# ═══════════════════════════════════════════════════════════════════════════
# Publikt API
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "Contact",
    "ContactStore",
    "RecipientStore",
    "RecipientsTab",
    "AddressBookDialog",
    "AddContactDialog",
    "validate_email_address",
    "load_legacy_txt",
    "_StoreAdapter",
]
