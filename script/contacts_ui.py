#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
script/contacts_ui.py – Kontakter & Grupper för EmailApp (PyQt6)

Version: 4.6 – LÄGG TILL ALLA VISADE KONTAKTER I TO/BCC

ÄNDRINGAR mot v4.5:
- ✅ Knappar "➕ Alla visade → To" / "➕ Alla visade → Bcc" i
    kontaktfliken – lägger till ALLA kontakter som för närvarande
    visas (sök + kategori + språkfilter gäller) med ett klick
- ✅ refresh_list() sparar self._last_visible (filtrerade kontakter)
    så att _push_all() vet exakt vilka som visas

ÄNDRINGAR mot v4.4:

ÄNDRINGAR mot v4.4:
- ✅ NATURLIG SORTERING (_natural_key): "Kund 2" kommer före "Kund 10",
    "Vindruta 3" före "Vindruta 12" – siffror sorteras numeriskt, inte
    bokstavligt. Gäller Namn, E-post, Företag, Kategorier.
- ✅ SVENSK ORDNING: lower-case-sortering ger å/ä/ö sist (Åberg efter
    Zetterlund) – korrekt svensk alfabetisk ordning.
- ✅ SORTERA MED KOLUMNKLICK: klicka på rubriken (👤 Namn, 📧 E-post,
    🏢 Företag, 🌐 Språk, 📁 Kategorier) → sortera stigande; klicka igen
    → fallande. Pil-indikator visas i rubriken. Dropdownen synkas.
- ✅ SPRÅKFILTER: ny dropdown "🌐 Språk" – (Alla) / 🇸🇪 SV / 🇬🇧 EN.
    Kombinera med kategori-filtret och sökningen.
- ✅ SMARTARE SPRÅKSORTERING: "Språk (SV först)" / "Språk (EN först)"
    ersätter de gamla "Språk (A-Ö)/(Ö-A)" – tydligare.
- ✅ SAMMANFATTNING: visar antal per språk (SV n · EN n) + filter +
    sortering – snabb överblick.

ÄNDRINGAR mot v4.3:
- ✅ Contact får fältet `language` ("sv"/"en", default "sv") – vilket
    språk mottagaren ska få mailet på
    * Spara: "language": "en" skrivs bara när avvikande (kompakt,
      bakåtkompatibelt JSON)
    * to_dict/from_dict/__post_init__ normaliserar till "sv"/"en"
- ✅ _ContactEditDialog: dropdown "🌐 Språk" (🇸🇪 Svenska / 🇬🇧 Engelska)
    * Sätts vid ny kontakt, förifylld vid redigering
    * Spara via store.upsert(..., language=...)
- ✅ ContactsTab: ny kolumn "🌐 Språk" (🇸🇪 SV / 🇬🇧 EN) + sorteringslägen
    "Språk (A-Ö)" / "Språk (Ö-A)"
- ✅ CSV: export inkluderar "language"-kolumn, import läser den
- ✅ ContactStore.upsert/update hanterar language

Fixar mot v4.2:
- ✅ Korrupt markdown/inklistringssyntax borttagen
  (__init__, __all__, __eq__, __hash__, __future__, log.info,
   self.email, self.name, self.company, self.group, contact.email,
   other.email, item.data, x.email, existing.name,
   _EMAIL_RE, _HAS_EMAIL_VALIDATOR, _ext_validate,
   _ContactEditDialog, _build_ui, _collect_categories, _on_save,
   _create_empty_file, _save_locked, _bind_events, _apply_theme,
   _update_sel_label, _selected_contacts, _get_selected_emails,
   _sorted_contacts, _show_context_menu, _add_contact,
   _edit_selected, _delete_selected, _push_selected, _import_csv,
   _export_csv, self.by_group, self._store.search, dialog.show,
   contact.to_dict, data_path.read_text, QMessageBox.StandardButton.No,
   "namn@example.com", <b>...</b>, &, <, >)
- ✅ SyntaxError fixad: itemDoubleClicked använde "lambda *item,* col:"
  → "lambda item, col:"
- ✅ EventBus-prenumeration med LAMBDAS fixad → bundna metoder
    * v4.2 använde lambda i subscribe() – weakrefs gör att de GC:as
      direkt och kontakter/UI-events ALDRIG nådde fliken
    * Nu: self._on_contacts_updated / self._on_theme_changed (bundna
      metoder lever så länge fliken lever)
- ✅ SNABBARE: reload() med mtime-cache
    * showEvent laddar om kontakter från disk VARJE gång fliken visas
    * Nu: endast om filen ändrats sedan senaste läsningen
- ✅ SNABBARE: kategori-dropdown byggs endast om kategorierna ändrats
- ✅ SNABBARE: setUniformRowHeights(True) – färre layout-beräkningar
- ✅ QAbstractItemView.SelectionMode.ExtendedSelection (explicit enum)
- ✅ show() för _ContactEditDialog behåller API:et men dokumenteras

Klasser:
- Contact:             Dataclass (stabil modell)
- ContactStore:        Persistenslager (ingen UI-kod)
- ContactsTab:         QWidget för kontaktfliken
- _ContactEditDialog:  QDialog för ny/redigera kontakt

Mål med denna version:
- enklare att lägga till / redigera / ta bort kontakter
- sökning medan man skriver
- filtrering per kategori
- sortering på namn / e-post / företag / kategori
- stigande och fallande sortering (A-Ö / Ö-A)
- högerklicksmeny på kontakter
- kontakter laddas om när fliken visas
- on_add_to-callback för att lägga markerade kontakter i To/Bcc
- tydligare status/sammanfattning i fliken

REGLER:
- Ingen Tkinter-kod
- StyleEngine för färger om tillgänglig
- QDialog.exec() för modal visning
- QTimer.singleShot() för EventBus-callbacks
- Ingen CC-specifik UI-logik i ny kod

FIL: script/contacts_ui.py
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
from typing import Any, Callable, Dict, List, Optional, Set

# PyQt6
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# core
from core.event_bus import EventBus

# ui
from ui.styles import StyleEngine, get_colors

log = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# (v4.5) Naturlig sorteringsnyckel – siffror sorteras numeriskt:
# "Kund 2" före "Kund 10", "Vindruta 3" före "Vindruta 12".
def _natural_key(text: Any) -> List[Any]:
    parts = re.split(r"(\d+)", str(text or "").lower())
    key: List[Any] = []
    for part in parts:
        if part.isdigit():
            key.append((1, int(part)))
        else:
            key.append((0, part))
    return key

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


# ═══════════════════════════════════════════════════════════════════════════
# Validering
# ═══════════════════════════════════════════════════════════════════════════

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
    """Representerar en kontakt i adressboken."""

    email: str
    name: str = ""
    company: str = ""
    group: str = ""
    # (v4.4) "sv"/"en" – vilken språkversion kontakten ska få
    language: str = "sv"
    categories: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()
        self.name = self.name.strip()
        self.company = self.company.strip()
        self.group = self.group.strip()
        self.language = (
            "en"
            if str(self.language or "sv").strip().lower() == "en"
            else "sv"
        )
        self.categories = [
            category.strip()
            for category in self.categories
            if category.strip()
        ]
        if self.group and self.group not in self.categories:
            self.categories.append(self.group)

    def normalize(self) -> "Contact":
        self.__post_init__()
        return self

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"email": self.email}
        if self.name:
            data["name"] = self.name
        if self.company:
            data["company"] = self.company
        if self.group:
            data["group"] = self.group
        # (v4.4) language sparas bara när avvikande (default = sv)
        if self.language == "en":
            data["language"] = "en"
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
            language=data.get("language", "sv"),
            categories=categories,
        )

    def display_name(self) -> str:
        return f"{self.name} <{self.email}>" if self.name else self.email

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Contact):
            return NotImplemented
        return self.email == other.email

    def __hash__(self) -> int:
        return hash(self.email)


# ═══════════════════════════════════════════════════════════════════════════
# ContactStore (ingen UI-kod)
# ═══════════════════════════════════════════════════════════════════════════

class ContactStore:
    """Hanterar persistens för kontakter.

    JSON-format:
        {"contacts": [{email, name, company, group, categories}]}

    Stöder även äldre email-keyed dict-format vid läsning men sparar alltid i
    unified format.
    """

    def __init__(
        self,
        data_path: Path,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self._data_path = Path(data_path)
        self._bus = event_bus
        self._lock = threading.RLock()
        self._contacts: Dict[str, Contact] = {}
        self._load()

    @property
    def path(self) -> Path:
        return self._data_path

    def _load(self) -> None:
        with self._lock:
            self._contacts = {}

        if not self._data_path.exists():
            log.warning("ContactStore: %s saknas", self._data_path)
            self._create_empty_file()
            return

        try:
            data = json.loads(
                self._data_path.read_text(encoding="utf-8-sig")
            )
            items: List[Any] = []

            if isinstance(data, dict):
                if "contacts" in data and isinstance(data["contacts"], list):
                    items = data["contacts"]
                else:
                    log.info("ContactStore: konverterar gammalt format")
                    for email, values in data.items():
                        if isinstance(values, dict):
                            item = dict(values)
                            item["email"] = email
                            items.append(item)
                        elif isinstance(values, str):
                            items.append({"email": email})
            elif isinstance(data, list):
                items = data

            count = 0
            with self._lock:
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    email = str(item.get("email", "")).strip().lower()
                    if not email:
                        continue
                    try:
                        contact = Contact.from_dict(item)
                        self._contacts[contact.email] = contact
                        count += 1
                    except Exception as exc:
                        log.warning("ContactStore: hoppar: %s", exc)

            log.info("ContactStore: %d kontakter", count)

            # Spara om vid legacy-format
            if isinstance(data, dict) and "contacts" not in data and items:
                self._save_locked()
        except json.JSONDecodeError as exc:
            log.error("ContactStore JSON-fel: %s", exc)
        except Exception:
            log.exception("ContactStore: läsfel %s", self._data_path)

    def _create_empty_file(self) -> None:
        try:
            self._data_path.parent.mkdir(parents=True, exist_ok=True)
            self._data_path.write_text(
                json.dumps({"contacts": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            log.exception("ContactStore: kunde inte skapa fil")

    def _save_locked(self) -> None:
        try:
            self._data_path.parent.mkdir(parents=True, exist_ok=True)
            ordered = sorted(
                self._contacts.values(),
                key=lambda c: (c.name or c.email).lower(),
            )
            tmp = self._data_path.with_suffix(".tmp")
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
            tmp.replace(self._data_path)
        except Exception:
            log.exception("ContactStore: sparfel")

    def save(self) -> None:
        with self._lock:
            self._save_locked()
        log.info("ContactStore: sparade %d", len(self._contacts))

    def reload(self) -> None:
        self._load()
        self._publish("reload")

    def add(self, contact: Contact) -> bool:
        contact.normalize()
        with self._lock:
            if contact.email in self._contacts:
                return False
            self._contacts[contact.email] = contact
            self._save_locked()
        self._publish("add")
        return True

    def upsert(
        self,
        email: str,
        name: str = "",
        company: str = "",
        group: str = "",
        language: str = "sv",
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
            language=language,
            categories=cats,
        )
        with self._lock:
            self._contacts[contact.email] = contact
            self._save_locked()
        self._publish("upsert")
        return contact

    def update(self, email: str, **kwargs: Any) -> Optional[Contact]:
        normalized = email.strip().lower()
        with self._lock:
            contact = self._contacts.get(normalized)
            if contact is None:
                return None
            for key, value in kwargs.items():
                if hasattr(contact, key):
                    setattr(contact, key, value)
            contact.__post_init__()
            self._save_locked()
        self._publish("update")
        return contact

    def delete(self, email: str) -> bool:
        normalized = email.strip().lower()
        with self._lock:
            if normalized not in self._contacts:
                return False
            del self._contacts[normalized]
            self._save_locked()
        self._publish("delete")
        return True

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
                if needle in contact.email
                or needle in (contact.name or "").lower()
                or needle in (contact.company or "").lower()
                or any(
                    needle in category.lower()
                    for category in contact.categories
                )
            ]

    def by_group(self, group: str) -> List[Contact]:
        with self._lock:
            return [
                contact
                for contact in self._contacts.values()
                if group in contact.categories
            ]

    def by_category(self, category: str) -> List[Contact]:
        return self.by_group(category)

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
                cats = [
                    value for value in contact.categories if value
                ] or ["Okategoriserad"]
                for category in cats:
                    result.setdefault(category, []).append(contact)
        for category in result:
            result[category].sort(
                key=lambda c: (c.name or c.email).lower()
            )
        return result

    def import_csv(self, path: str, encoding: str = "utf-8") -> Dict[str, int]:
        stats = {"added": 0, "updated": 0, "invalid": 0}
        try:
            with open(path, newline="", encoding=encoding) as handle:
                for row in csv.DictReader(handle):
                    email = row.get("email", "").strip()
                    if not email or not validate_email_address(email):
                        stats["invalid"] += 1
                        continue
                    cats_raw = row.get("categories", row.get("group", ""))
                    categories = [
                        part.strip()
                        for part in re.split(r"[;,]", cats_raw)
                        if part.strip()
                    ]
                    existing = self.get(email)
                    if existing:
                        self.update(
                            email,
                            name=row.get("name", existing.name),
                            company=row.get("company", existing.company),
                            language=row.get("language", existing.language),
                            categories=categories or existing.categories,
                        )
                        stats["updated"] += 1
                    else:
                        self.upsert(
                            email,
                            name=row.get("name", ""),
                            company=row.get("company", ""),
                            language=row.get("language", "sv"),
                            categories=categories,
                        )
                        stats["added"] += 1
        except Exception as exc:
            log.error("CSV-import: %s", exc)
            raise
        self._publish("import_csv")
        return stats

    def export_csv(self, path: str, encoding: str = "utf-8") -> None:
        with open(path, "w", newline="", encoding=encoding) as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["email", "name", "company", "group", "language", "categories"]
            )
            for contact in sorted(self.all(), key=lambda x: x.email):
                writer.writerow(
                    [
                        contact.email,
                        contact.name,
                        contact.company,
                        contact.group,
                        contact.language,
                        "; ".join(contact.categories),
                    ]
                )

    def clear(self) -> None:
        with self._lock:
            self._contacts.clear()
            self._save_locked()
        self._publish("clear")

    def _publish(self, action: str) -> None:
        if self._bus:
            try:
                self._bus.publish(
                    "contacts.updated",
                    {"count": self.count(), "action": action},
                )
            except Exception:
                log.exception("ContactStore: EventBus-fel")


# ═══════════════════════════════════════════════════════════════════════════
# _ContactEditDialog (PyQt6)
# ═══════════════════════════════════════════════════════════════════════════

class _ContactEditDialog(QDialog):
    """Intern dialog för att lägga till / redigera kontakt."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        store: Optional[ContactStore] = None,
        theme_engine: Optional[StyleEngine] = None,
        edit_contact: Optional[Contact] = None,
    ) -> None:
        super().__init__(parent)
        self._store = store
        self._style = theme_engine
        self._edit = edit_contact
        self._result: Optional[Contact] = None
        self._checks: Dict[str, QCheckBox] = {}

        is_edit = edit_contact is not None
        self.setWindowTitle("✏️ Redigera kontakt" if is_edit else "➕ Ny kontakt")
        self.setModal(True)
        self.setMinimumWidth(430)

        self._build_ui()
        if is_edit and edit_contact is not None:
            self._prefill(edit_contact)

    def _c(self) -> Dict[str, str]:
        if self._style:
            return self._style.get_colors()
        return get_colors("dark")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(QLabel("<b>✉️ E-post (krävs):</b>"))
        self._email = QLineEdit()
        self._email.setPlaceholderText("namn@example.com")
        layout.addWidget(self._email)

        layout.addWidget(QLabel("👤 Namn:"))
        self._name = QLineEdit()
        layout.addWidget(self._name)

        layout.addWidget(QLabel("🏢 Företag:"))
        self._company = QLineEdit()
        layout.addWidget(self._company)

        # (v4.4) Språk per kontakt – vilken version mailet ska få
        layout.addWidget(QLabel("🌐 Språk (mail-språk för denna kontakt):"))
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("🇸🇪 Svenska (SV)", "sv")
        self._lang_combo.addItem("🇬🇧 Engelska (EN)", "en")
        layout.addWidget(self._lang_combo)

        cat_box = QGroupBox("🏷️ Kategorier")
        cat_layout = QGridLayout(cat_box)
        cat_layout.setSpacing(6)

        existing = sorted(self._store.categories()) if self._store else []
        col = 0
        row = 0
        for category in existing:
            checkbox = QCheckBox(category)
            cat_layout.addWidget(checkbox, row, col)
            self._checks[category] = checkbox
            col += 1
            if col >= 3:
                col = 0
                row += 1
        layout.addWidget(cat_box)

        layout.addWidget(QLabel("Ny kategori (kommaseparera flera):"))
        self._new_cat = QLineEdit()
        self._new_cat.setPlaceholderText("t.ex. Kund, Partner")
        layout.addWidget(self._new_cat)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("💾 Spara")
        btn_save.setProperty("cssClass", "success")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)

        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.setProperty("cssClass", "danger")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _prefill(self, contact: Contact) -> None:
        self._email.setText(contact.email)
        self._email.setReadOnly(True)
        self._name.setText(contact.name)
        self._company.setText(contact.company)
        # (v4.4) Förifyll språkvalet vid redigering
        try:
            idx = self._lang_combo.findData(contact.language)
            self._lang_combo.setCurrentIndex(idx if idx >= 0 else 0)
        except Exception:
            pass
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
                f"'{email}' är inte en giltig adress.",
            )
            return

        categories = self._collect_categories()
        # (v4.4) Språkval från dropdownen
        try:
            language = str(self._lang_combo.currentData() or "sv")
        except Exception:
            language = "sv"
        if self._store:
            self._result = self._store.upsert(
                email=email,
                name=self._name.text().strip(),
                company=self._company.text().strip(),
                language=language,
                categories=categories,
            )
        log.info(
            "_ContactEditDialog: sparade %s språk=%s kategorier=%s",
            email, language, categories,
        )
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
# ContactsTab (PyQt6)
# ═══════════════════════════════════════════════════════════════════════════

class ContactsTab(QWidget):
    """Kontakter-tab som QWidget.

    Förbättringar i denna version (v4.5):
    - sortera med kolumnklick (rubrik → stigande/fallande, pil-indikator)
    - naturlig sortering ("Kund 2" före "Kund 10"), svensk å/ä/ö-ordning
    - språkfilter (Alla / SV / EN) + kategori-filter + sök
    - reload med mtime-cache när fliken visas
    - högerklicksmeny för snabb CRUD och Lägg i To/Bcc
    """

    # (v4.5) Kolumn → dropdown-lägen för header-klick-sortering
    _HEADER_SORT_MAP: Dict[int, Tuple[str, str, str]] = {
        0: ("Namn", "Namn (A-Ö)", "Namn (Ö-A)"),
        1: ("E-post", "E-post (A-Ö)", "E-post (Ö-A)"),
        2: ("Företag", "Företag (A-Ö)", "Företag (Ö-A)"),
        3: ("Språk", "Språk (SV först)", "Språk (EN först)"),
        4: ("Kategori", "Kategori (A-Ö)", "Kategori (Ö-A)"),
    }

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        store: Optional[ContactStore] = None,
        event_bus: Optional[EventBus] = None,
        on_add_to: Optional[Callable[[List[str], str], None]] = None,
        theme_engine: Optional[StyleEngine] = None,
    ) -> None:
        super().__init__(parent)
        self._store = store
        self._bus = event_bus
        self._on_add_to = on_add_to
        self._style = theme_engine
        self._last_mtime: float = -1.0
        self._cached_categories: List[str] = []

        self._build_ui()
        self._bind_events()
        self.refresh_list()

    def _c(self) -> Dict[str, str]:
        if self._style:
            return self._style.get_colors()
        return get_colors("dark")

    # ── UI-byggnad ──────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Sök & filter & sortering
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("🔍 Sök:"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Sök kontakt…")
        self._search.textChanged.connect(self.refresh_list)
        filter_row.addWidget(self._search, stretch=1)

        filter_row.addWidget(QLabel("📁 Kategori:"))
        self._group_cb = QComboBox()
        self._group_cb.addItem("(Alla)")
        self._group_cb.currentTextChanged.connect(self.refresh_list)
        filter_row.addWidget(self._group_cb)

        # (v4.5) Språkfilter – knyter an till språk per kontakt (SV/EN)
        filter_row.addWidget(QLabel("🌐 Språk:"))
        self._lang_filter_cb = QComboBox()
        self._lang_filter_cb.addItem("(Alla)")
        self._lang_filter_cb.addItem("🇸🇪 SV")
        self._lang_filter_cb.addItem("🇬🇧 EN")
        self._lang_filter_cb.currentTextChanged.connect(self.refresh_list)
        filter_row.addWidget(self._lang_filter_cb)

        filter_row.addWidget(QLabel("↕ Sortera:"))
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
            # (v4.5) Smartare språksortering: SV först / EN först
            "Språk (SV först)",
            "Språk (EN först)",
        ])
        self._sort_cb.currentTextChanged.connect(self.refresh_list)
        filter_row.addWidget(self._sort_cb)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedWidth(36)
        btn_refresh.clicked.connect(self.reload)
        filter_row.addWidget(btn_refresh)

        layout.addLayout(filter_row)

        # Huvudyta
        splitter = QSplitter(Qt.Orientation.Vertical)

        self._tree = QTreeWidget()
        self._tree.setColumnCount(5)
        self._tree.setHeaderLabels([
            "👤 Namn", "📧 E-post", "🏢 Företag", "🌐 Språk", "📁 Kategorier",
        ])
        self._tree.setAlternatingRowColors(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self._tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._tree.customContextMenuRequested.connect(
            self._show_context_menu
        )
        # (v4.5) Klick på kolumnrubrik → sortera (stigande/fallande)
        self._tree.header().setStretchLastSection(True)
        self._tree.header().setSectionsClickable(True)
        self._tree.header().setSortIndicatorShown(True)
        self._tree.header().sectionClicked.connect(self._on_header_clicked)
        self._tree.header().setToolTip(
            "Klicka på en rubrik för att sortera – klicka igen för "
            "fallande ordning"
        )
        self._tree.itemDoubleClicked.connect(
            lambda item, col: self._edit_selected()
        )
        self._tree.itemSelectionChanged.connect(self._update_sel_label)
        splitter.addWidget(self._tree)

        info_box = QGroupBox("Åtgärder")
        info_layout = QVBoxLayout(info_box)
        info_layout.setSpacing(8)

        crud_row = QHBoxLayout()
        for text, callback, css_class in [
            ("➕ Ny", self._add_contact, "success"),
            ("✏️ Redigera", self._edit_selected, "accent"),
            ("🗑️ Ta bort", self._delete_selected, "danger"),
        ]:
            button = QPushButton(text)
            button.setProperty("cssClass", css_class)
            button.clicked.connect(callback)
            crud_row.addWidget(button)
        crud_row.addStretch()
        info_layout.addLayout(crud_row)

        csv_row = QHBoxLayout()
        btn_import = QPushButton("📥 Importera CSV")
        btn_import.clicked.connect(self._import_csv)
        csv_row.addWidget(btn_import)

        btn_export = QPushButton("📤 Exportera CSV")
        btn_export.clicked.connect(self._export_csv)
        csv_row.addWidget(btn_export)
        csv_row.addStretch()
        info_layout.addLayout(csv_row)

        push_row = QHBoxLayout()
        push_row.addWidget(QLabel("Markerade kontakter:"))

        btn_to = QPushButton("📬 Lägg i To")
        btn_to.setProperty("cssClass", "accent")
        btn_to.clicked.connect(lambda: self._push_selected("to"))
        push_row.addWidget(btn_to)

        btn_bcc = QPushButton("🔒 Lägg i Bcc")
        btn_bcc.clicked.connect(lambda: self._push_selected("bcc"))
        push_row.addWidget(btn_bcc)

        # (v4.6) Lägg till ALLA visade kontakter (sök/filter gäller)
        btn_all_to = QPushButton("➕ Alla visade → To")
        btn_all_to.setProperty("cssClass", "accent")
        btn_all_to.clicked.connect(lambda: self._push_all("to"))
        push_row.addWidget(btn_all_to)

        btn_all_bcc = QPushButton("➕ Alla visade → Bcc")
        btn_all_bcc.setProperty("cssClass", "purple")
        btn_all_bcc.clicked.connect(lambda: self._push_all("bcc"))
        push_row.addWidget(btn_all_bcc)

        push_row.addStretch()
        self._sel_label = QLabel("")
        self._sel_label.setProperty("cssClass", "subtext")
        push_row.addWidget(self._sel_label)
        info_layout.addLayout(push_row)

        self._summary = QLabel("")
        self._summary.setProperty("cssClass", "subtext")
        self._summary.setWordWrap(True)
        info_layout.addWidget(self._summary)

        splitter.addWidget(info_box)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        layout.addWidget(splitter, stretch=1)

    # ── EventBus (v4.3: bundna metoder – lambdas GC:as av weakrefs) ────
    def _bind_events(self) -> None:
        if not self._bus:
            return
        try:
            self._bus.subscribe("contacts.updated", self._on_contacts_updated)
            self._bus.subscribe("ui.theme_changed", self._on_theme_changed)
        except Exception:
            log.exception("ContactsTab: subscribe")

    def _on_contacts_updated(self, data: Optional[Dict[str, Any]] = None) -> None:
        QTimer.singleShot(0, self.refresh_list)

    def _on_theme_changed(self, data: Optional[Dict[str, Any]] = None) -> None:
        QTimer.singleShot(0, self._apply_theme)

    def _apply_theme(self) -> None:
        """Tema ändrat – QSS appliceras globalt, ingen extra åtgärd krävs."""
        self._update_sel_label()

    # ── Hjälpmetoder ────────────────────────────────────────────────────
    def _update_sel_label(self) -> None:
        count = len(self._tree.selectedItems())
        self._sel_label.setText(f"{count} markerade" if count > 0 else "")

    def _selected_contacts(self) -> List[Contact]:
        if not self._store:
            return []
        contacts: List[Contact] = []
        seen: Set[str] = set()
        for item in self._tree.selectedItems():
            email = item.data(1, Qt.ItemDataRole.UserRole) or item.data(
                0, Qt.ItemDataRole.UserRole
            )
            if not email:
                continue
            key = str(email).strip().lower()
            if key in seen:
                continue
            seen.add(key)
            contact = self._store.get(key)
            if contact:
                contacts.append(contact)
        return contacts

    def _get_selected_emails(self) -> List[str]:
        return [contact.email for contact in self._selected_contacts()]

    def _sorted_contacts(self, contacts: List[Contact]) -> List[Contact]:
        """(v4.5) Naturlig + svensk sortering: siffror numeriskt,
        å/ä/ö sist, tomma fält faller till e-post/zzz."""
        mode = self._sort_cb.currentText()
        reverse = ("Ö-A" in mode) or ("EN först" in mode)
        if mode.startswith("E-post"):
            return sorted(
                contacts,
                key=lambda c: (
                    _natural_key(c.email),
                    _natural_key(c.name or c.email),
                ),
                reverse=reverse,
            )
        if mode.startswith("Företag"):
            return sorted(
                contacts,
                key=lambda c: (
                    _natural_key(c.company or "zzz"),
                    _natural_key(c.name or c.email),
                ),
                reverse=reverse,
            )
        if mode.startswith("Kategori"):
            return sorted(
                contacts,
                key=lambda c: (
                    _natural_key(
                        c.categories[0] if c.categories else "zzz"
                    ),
                    _natural_key(c.name or c.email),
                ),
                reverse=reverse,
            )
        if mode.startswith("Språk"):
            # "SV först" → sv=0/en=1 · "EN först" → en=0/sv=1.
            # Namnen sorteras alltid stigande inom gruppen.
            en_first = "EN först" in mode
            return sorted(
                contacts,
                key=lambda c: (
                    0 if (c.language == "en") == en_first else 1,
                    _natural_key(c.name or c.email),
                ),
            )
        # Namn (default) – svensk ordning: lower + naturlig
        return sorted(
            contacts,
            key=lambda c: (
                _natural_key(c.name or c.email),
                _natural_key(c.email),
            ),
            reverse=reverse,
        )

    # (v4.5) Header-klick → sortera kolumnen (igen = byt riktning)
    def _on_header_clicked(self, column: int) -> None:
        entry = self._HEADER_SORT_MAP.get(column)
        if not entry:
            return
        current = self._sort_cb.currentText()
        asc_text, desc_text = entry[1], entry[2]
        if current in (asc_text, desc_text):
            target = desc_text if current == asc_text else asc_text
        else:
            target = asc_text
        self._sort_cb.blockSignals(True)
        index = self._sort_cb.findText(target)
        self._sort_cb.setCurrentIndex(index if index >= 0 else 0)
        self._sort_cb.blockSignals(False)
        self.refresh_list()

    def _update_sort_indicator(self) -> None:
        """(v4.5) Visa pil i rubriken för aktuell sorteringskolumn."""
        mode = self._sort_cb.currentText()
        for column, entry in self._HEADER_SORT_MAP.items():
            if mode == entry[1]:
                self._tree.header().setSortIndicator(
                    column, Qt.SortOrder.AscendingOrder
                )
                return
            if mode == entry[2]:
                self._tree.header().setSortIndicator(
                    column, Qt.SortOrder.DescendingOrder
                )
                return

    # ── Reload / refresh (v4.3: mtime-cache) ────────────────────────────
    def reload(self) -> None:
        if self._store:
            try:
                p = self._store.path
                mtime = p.stat().st_mtime if p.exists() else 0.0
                if mtime != self._last_mtime:
                    self._last_mtime = mtime
                    self._store.reload()
            except Exception:
                log.exception("ContactsTab.reload()")
        self.refresh_list()

    def showEvent(self, event: Any) -> None:  # noqa: N802
        """Ladda om adressboken när fliken visas (endast om fil ändrats)."""
        try:
            self.reload()
        except Exception:
            log.debug("showEvent reload misslyckades", exc_info=True)
        super().showEvent(event)

    # ── Uppdatera lista ─────────────────────────────────────────────────
    def refresh_list(self) -> None:
        """Uppdatera kontaktlistan utifrån sök + kategori + sortering."""
        if not self._store:
            return

        self._tree.clear()

        query = self._search.text().strip()
        category = self._group_cb.currentText()
        # (v4.5) Språkfilter: (Alla) / SV / EN
        lang_filter = self._lang_filter_cb.currentText()
        contacts = self._store.search(query) if query else self._store.all()
        if category and category != "(Alla)":
            contacts = [
                contact
                for contact in contacts
                if category in contact.categories
            ]
        if lang_filter == "🇸🇪 SV":
            contacts = [
                contact for contact in contacts
                if contact.language != "en"
            ]
        elif lang_filter == "🇬🇧 EN":
            contacts = [
                contact for contact in contacts
                if contact.language == "en"
            ]

        contacts = self._sorted_contacts(contacts)

        # Uppdatera kategori-dropdown endast om kategorierna ändrats (v4.3)
        categories = sorted(
            self._store.categories(), key=lambda value: value.lower()
        )
        if categories != self._cached_categories:
            self._cached_categories = categories
            current = self._group_cb.currentText()
            self._group_cb.blockSignals(True)
            self._group_cb.clear()
            self._group_cb.addItem("(Alla)")
            self._group_cb.addItems(categories)
            if current in categories:
                self._group_cb.setCurrentText(current)
            else:
                self._group_cb.setCurrentIndex(0)
            self._group_cb.blockSignals(False)

        for contact in contacts:
            item = QTreeWidgetItem(
                [
                    contact.name or "",
                    contact.email,
                    contact.company or "",
                    # (v4.4) Språk-kolumn
                    ("🇬🇧 EN" if contact.language == "en" else "🇸🇪 SV"),
                    "; ".join(contact.categories),
                ]
            )
            item.setData(0, Qt.ItemDataRole.UserRole, contact.email)
            item.setData(1, Qt.ItemDataRole.UserRole, contact.email)
            self._tree.addTopLevelItem(item)

        self._tree.resizeColumnToContents(0)
        self._tree.resizeColumnToContents(1)
        self._tree.resizeColumnToContents(2)
        self._tree.resizeColumnToContents(3)

        # (v4.6) Spara de visade kontakterna för "Lägg till alla visade"
        self._last_visible = list(contacts)

        # (v4.5) Pil-indikator + sammanfattning med språkfördelning
        self._update_sort_indicator()

        current_sort = self._sort_cb.currentText()
        current_group = self._group_cb.currentText() or "(Alla)"
        current_lang = self._lang_filter_cb.currentText() or "(Alla)"
        all_contacts = self._store.all()
        sv_count = sum(1 for c in all_contacts if c.language != "en")
        en_count = len(all_contacts) - sv_count
        self._summary.setText(
            f"📒 {len(contacts)} kontakt(er) visas · "
            f"{self._store.count()} totalt · "
            f"🌐 SV {sv_count} · EN {en_count} · "
            f"Filter: {current_group} / {current_lang} · "
            f"Sortering: {current_sort}"
        )
        self._update_sel_label()

    # ── Kontextmeny ─────────────────────────────────────────────────────
    def _show_context_menu(self, pos: Any) -> None:
        item = self._tree.itemAt(pos)
        if item is not None and not item.isSelected():
            self._tree.setCurrentItem(item)
            item.setSelected(True)

        menu = QMenu(self)
        act_to = QAction("📬 Lägg i To", self)
        act_bcc = QAction("🔒 Lägg i Bcc", self)
        act_edit = QAction("✏️ Redigera", self)
        act_delete = QAction("🗑️ Ta bort", self)
        act_copy = QAction("📋 Kopiera e-post", self)
        act_copy_display = QAction("📋 Kopiera namn + e-post", self)

        menu.addAction(act_to)
        menu.addAction(act_bcc)
        menu.addSeparator()
        menu.addAction(act_edit)
        menu.addAction(act_delete)
        menu.addSeparator()
        menu.addAction(act_copy)
        menu.addAction(act_copy_display)

        chosen = menu.exec(self._tree.viewport().mapToGlobal(pos))
        if chosen == act_to:
            self._push_selected("to")
        elif chosen == act_bcc:
            self._push_selected("bcc")
        elif chosen == act_edit:
            self._edit_selected()
        elif chosen == act_delete:
            self._delete_selected()
        elif chosen == act_copy:
            emails = self._get_selected_emails()
            if emails:
                QApplication.clipboard().setText("\n".join(emails))
                QMessageBox.information(
                    self,
                    "Kopierat",
                    f"{len(emails)} adress(er) kopierade.",
                )
        elif chosen == act_copy_display:
            contacts = self._selected_contacts()
            if contacts:
                lines = [contact.display_name() for contact in contacts]
                QApplication.clipboard().setText("\n".join(lines))
                QMessageBox.information(
                    self,
                    "Kopierat",
                    f"{len(lines)} kontakt(er) kopierade.",
                )

    # ── CRUD ────────────────────────────────────────────────────────────
    def _add_contact(self) -> None:
        dialog = _ContactEditDialog(self, self._store, self._style)
        result = dialog.show()
        if result:
            self.refresh_list()

    def _edit_selected(self) -> None:
        contacts = self._selected_contacts()
        if not contacts:
            return
        contact = contacts[0]
        dialog = _ContactEditDialog(
            self, self._store, self._style, edit_contact=contact
        )
        result = dialog.show()
        if result:
            self.refresh_list()

    def _delete_selected(self) -> None:
        emails = self._get_selected_emails()
        if not emails:
            return
        count = len(emails)
        message = (
            f"Ta bort '{emails[0]}'?"
            if count == 1
            else f"Ta bort {count} kontakter?"
        )
        reply = QMessageBox.question(
            self,
            "Bekräfta",
            message,
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self._store:
            for email in emails:
                self._store.delete(email)
        self.refresh_list()

    def _push_all(self, target: str) -> None:
        """(v4.6) Skicka ALLA visade kontakter (sök/filter gäller)."""
        if not self._on_add_to:
            QMessageBox.warning(
                self,
                "Ej tillgängligt",
                "Ingen callback för att lägga till mottagare.",
            )
            return
        contacts = list(getattr(self, "_last_visible", []) or [])
        if not contacts:
            QMessageBox.warning(
                self, "Ingen vald", "Inga kontakter visas att lägga till."
            )
            return
        emails = [contact.email for contact in contacts]
        self._on_add_to(emails, target)
        QMessageBox.information(
            self,
            "✅ Tillagt",
            f"{len(emails)} kontakt(er) lades till i {target.upper()} "
            f"(alla visade).",
        )

    def _push_selected(self, target: str) -> None:
        """Skicka markerade kontakter till To/Bcc via callback."""
        if not self._on_add_to:
            QMessageBox.warning(
                self,
                "Ej tillgängligt",
                "Ingen callback för att lägga till mottagare.",
            )
            return
        emails = self._get_selected_emails()
        if not emails:
            QMessageBox.warning(
                self, "Ingen vald", "Markera minst en kontakt."
            )
            return
        self._on_add_to(emails, target)
        QMessageBox.information(
            self,
            "✅ Tillagt",
            f"{len(emails)} kontakt(er) lades till i {target.upper()}.",
        )

    def _import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importera kontakter",
            "",
            "CSV-filer (*.csv);;Alla filer (*.*)",
        )
        if not path or not self._store:
            return
        try:
            stats = self._store.import_csv(path)
            QMessageBox.information(
                self,
                "✅ Import klar",
                f"Tillagda: {stats['added']}\n"
                f"Uppdaterade: {stats['updated']}\n"
                f"Ogiltiga: {stats['invalid']}",
            )
            self.refresh_list()
        except Exception as exc:
            QMessageBox.critical(self, "❌ Import misslyckades", str(exc))

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportera kontakter",
            "",
            "CSV-filer (*.csv);;Alla filer (*.*)",
        )
        if not path or not self._store:
            return
        try:
            self._store.export_csv(path)
            QMessageBox.information(
                self,
                "✅ Export klar",
                f"Kontakter exporterade till {Path(path).name}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "❌ Export misslyckades", str(exc))

    def list_all(self) -> List[Contact]:
        """Returnera alla kontakter – för extern användning."""
        return self._store.all() if self._store else []


# ═══════════════════════════════════════════════════════════════════════════
# Publikt API
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "Contact",
    "ContactStore",
    "ContactsTab",
    "validate_email_address",
]
