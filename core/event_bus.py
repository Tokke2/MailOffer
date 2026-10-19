#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/event_bus.py – Central pub/sub-mekanism för EmailApp

Version: 3.5.1 – UNSUBSCRIBE-FIX för bundna metoder + putsad

Fixar mot v3.5:
- ✅ BUGG: unsubscribe() fungerade ALDRIG för bundna metoder
    * WeakMethod.__call__() skapar en NY bound method-instans varje
      gång → "current is handler" slog aldrig till → handlers kunde
      inte tas bort (t.ex. SystemTray.shutdown())
    * Nu: _remove_from_list() jämför även (__self__, __func__)

Fixar mot v3.4:
- Korrupt markdown/inklistringssyntax borttagen
  (__init__, __all__, __repr__, _make_ref, _is_pattern,
   _subscribe_pattern, _collect_handlers, _remove_from_list,
   log.info, [ui.tab]_changed-kommentarer)
- SNABBARE: snapshot-dispatch med copy-on-write
    * publish() = en dict-uppslagning + iteration, INGET lås i hot path
    * Förra versionen tog RLock + byggde om handler-listan + derefade
      weakrefs vid VARJE publish
- SNABBARE: wildcard-mönster matchas endast om mönster finns
    * Ingen regex-loop per publish i normal drift (inga mönster)
- SNABBARE: log_event-import löses EN gång (lazy-once)
    * Förra versionen gjorde "from core.logger import log_event"
      i try/except vid varje publish
- SNABBARE: debug-loggning guardad med log.isEnabledFor(logging.DEBUG)
- Rensning av döda weakrefs sker vid mutationer + var 256:e publish
  (periodisk – aldrig i hot path)
- __repr__ släpper lock innan f-string konstrueras
- clear(wildcard) jämför fnmatch-translated patterns korrekt
- get_subscribers() optimerad lock-tid
- Stabil singleton-instans via bus
- [EVENT]-loggning i dev-läge via core.logger om tillgänglig

All kommunikation mellan moduler sker via denna buss.
Inga direkta importberoenden mellan core/, ui/ och script/
för event-baserad kommunikation.

Funktioner:
- Thread-safe subscribe/unsubscribe/publish (threading.RLock
  för mutationer; lock-fri läsning via snapshot)
- Wildcard-stöd för eventmönster (t.ex. "mail.*")
- Weak references för att förhindra minnesläckor
- Async-publish i bakgrundstråd (ThreadPoolExecutor)
- Exceptionhantering som loggar men inte kraschar bussen
- Singleton-instans för global åtkomst
- [EVENT]-loggning i dev-läge via core.logger

FIL: core/event_bus.py
"""

from __future__ import annotations

import fnmatch
import logging
import re
import threading
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Tuple

log = logging.getLogger(__name__)

# ============================================================================
# Komplett event-katalog (sammanfattning från spec)
# ============================================================================
# MAIL-EVENTS:
#   "mail.sent"            -> data: {recipients, count, subject}
#   "mail.failed"          -> data: {error, recipients, subject}
#   "mail.progress"        -> data: {current, total, recipient/message}
#   "mail.test_ok"         -> data: {host, port}
#   "mail.test_failed"     -> data: {error}
#   "mail.send_requested"  -> data: {params, source}
#   "mail.form_reset"      -> data: {timestamp}
#
# TEMPLATE-EVENTS:
#   "template.loaded"              -> data: {path, name, placeholders}
#   "template.saved"               -> data: {path, name}
#   "template.error"               -> data: {error, path}
#   "template.placeholder_changed" -> data: {key, value, all_values}
#
# SETTINGS-EVENTS:
#   "settings.changed" -> data: {key, old_value, new_value}
#   "settings.saved"   -> data: {path}
#
# CONTACTS-EVENTS:
#   "contacts.updated" -> data: {count, action}
#
# RECIPIENTS-EVENTS:
#   "recipients.updated"        -> data: {to_count, bcc_count, total}
#   "recipients.default_loaded" -> data: {bcc_count}
#
# UI-EVENTS:
#   "ui.theme_changed"          -> data: {theme, was}
#   "ui.tab_changed"            -> data: {tab_name}
#   "ui.window_shown"           -> data: {}
#   "ui.window_hidden"          -> data: {}
#   "ui.form_reset"             -> data: {source}
#   "ui.tab_visibility_changed" -> data: {tab_key, visible}
#
# APP-EVENTS:
#   "app.startup"  -> data: {version, mode}
#   "app.shutdown" -> data: {reason}
#
# MODULE-EVENTS:
#   "module.error"    -> data: {module, error, count, disable?}
#   "module.disabled" -> data: {module, reason, count}
#   "module.reset"    -> data: {module}
# ============================================================================


# Lazy-once-upplösning av core.logger.log_event (kostar EN gång, ej per publish)
_log_event_fn:      Optional[Callable[..., Any]] = None
_log_event_resolved = False
_log_event_lock     = threading.Lock()


def _get_log_event() -> Optional[Callable[..., Any]]:
    """Returnera log_event-funktionen (eller None). Löses endast en gång."""
    global _log_event_fn, _log_event_resolved
    if _log_event_resolved:
        return _log_event_fn
    with _log_event_lock:
        if _log_event_resolved:
            return _log_event_fn
        try:
            from core.logger import log_event  # type: ignore
            _log_event_fn = log_event
        except Exception:
            _log_event_fn = None
        _log_event_resolved = True
        return _log_event_fn


class EventBus:
    """Central pub/sub-mekanism för thread-safe event-kommunikation.

    Använder weak references för att undvika minnesläckor när handlers är
    bundna till objekt som kan garbage-collectas.

    Wildcard-mönster stöds via fnmatch:
    - "mail.*" matchar "mail.sent", "mail.failed" etc.
    - "*" matchar alla events

    Prestanda (v3.5):
    publish() läser en förbyggd snapshot (copy-on-write) utan lås.
    Snapshot innehåller endast weakrefs (weak semantics bevaras) och
    byggs om vid mutationer (subscribe/unsubscribe/clear) samt
    periodiskt var _REFRESH_INTERVAL publish för att rensa döda refs.
    """

    # Hur ofta snapshot byggs om för att rensa döda weakrefs
    # (endast om inga mutationer skett dessförinnan)
    _REFRESH_INTERVAL = 256

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handlers: Dict[str, List[weakref.ReferenceType[Any]]] = {}
        self._patterns: Dict[Pattern[str], List[weakref.ReferenceType[Any]]] = {}
        # Snapshot: event -> tuple av WEAK refs (lock-fri läsning).
        # Endast weakrefs – aldrig starka referenser – så att döda
        # handlers fortfarande kan garbage-collectas (weak semantics).
        self._snapshot: Dict[str, Tuple[weakref.ReferenceType[Any], ...]] = {}
        self._executor = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="EventBus"
        )
        self._shutdown = False
        self._pub_since_refresh = 0
        log.debug("EventBus initierad (v3.5 snapshot-dispatch)")

    # ─────────────────────────────────────────────────────────────────────
    # Publikt API
    # ─────────────────────────────────────────────────────────────────────

    def subscribe(
        self,
        event:   str,
        handler: Callable[[Dict[str, Any]], None],
    ) -> None:
        """Prenumerera på ett event."""
        if not event or not callable(handler):
            log.warning(
                "Ogiltig subscribe: event=%r, handler=%r", event, handler
            )
            return

        with self._lock:
            if self._shutdown:
                log.warning("EventBus är avstängd – subscribe ignoreras")
                return

            ref = self._make_ref(handler)
            if ref is None:
                return

            if self._is_pattern(event):
                self._subscribe_pattern(event, ref)
            else:
                self._handlers.setdefault(event, []).append(ref)
                log.debug("Prenumererar på event %r", event)

            self._update_snapshot()

    def unsubscribe(
        self,
        event:   str,
        handler: Callable[[Dict[str, Any]], None],
    ) -> bool:
        """Avprenumerera från ett event.

        Returns:
            True om en prenumeration togs bort, annars False.
        """
        if not event or not callable(handler):
            return False

        with self._lock:
            removed = False
            if event in self._handlers:
                if self._remove_from_list(self._handlers[event], handler):
                    log.debug("Avprenumererar från %r", event)
                    if not self._handlers[event]:
                        del self._handlers[event]
                    removed = True

            if not removed:
                for pattern, refs in list(self._patterns.items()):
                    if self._remove_from_list(refs, handler):
                        log.debug(
                            "Avprenumererar från mönster %r", pattern.pattern
                        )
                        if not refs:
                            del self._patterns[pattern]
                        removed = True
                        break

            if removed:
                self._update_snapshot()
            return removed

    def publish(
        self,
        event: str,
        data:  Optional[Dict[str, Any]] = None,
    ) -> int:
        """Publicera ett event till alla prenumeranter (synkront).

        Hot path (v3.5):
          - ingen låsning
          - en dict-uppslagning i snapshot
          - wildcard matchas endast om mönster finns

        Returns:
            Antal handlers som anropades.
        """
        if self._shutdown:
            log.warning("EventBus är avstängd – publish ignoreras: %s", event)
            return 0

        payload: Dict[str, Any] = {} if data is None else data

        # Logga event i dev-läge om logger-modulen erbjuder detta.
        # (löses EN gång – inte vid varje publish som i v3.4)
        log_event = _get_log_event()
        if log_event is not None:
            try:
                log_event(event, payload)
            except Exception:
                pass  # Loggning får aldrig krascha bussen.

        # ── Snabb sökväg: snapshot-uppslagning utan lås ──────────────
        refs = self._snapshot.get(event, ())
        called = 0
        if refs:
            for ref in refs:
                handler = ref()
                if handler is None:
                    continue  # död weakref – hoppas över (rensas periodiskt)
                try:
                    handler(payload)
                    called += 1
                except Exception as exc:
                    log.exception(
                        "Fel i event-handler för %r: %s (handler: %r)",
                        event, exc, handler,
                    )

        # ── Wildcard (ovanligt – endast om mönster finns) ─────────────
        if self._patterns:
            called += self._dispatch_patterns(event, payload)

        # ── Periodisk rensning av döda weakrefs (aldrig i hot path) ──
        self._pub_since_refresh += 1
        if self._pub_since_refresh >= self._REFRESH_INTERVAL:
            self._refresh()

        if called == 0:
            if log.isEnabledFor(logging.DEBUG):
                log.debug("Inga aktiva handlers för event: %s", event)
        else:
            if log.isEnabledFor(logging.DEBUG):
                log.debug(
                    "Event %s skickat till %d handler(s)", event, called
                )

        return called

    def publish_async(
        self,
        event: str,
        data:  Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publicera ett event i en bakgrundstråd (asynkront)."""
        if self._shutdown:
            log.warning(
                "EventBus är avstängd – publish_async ignoreras: %s", event
            )
            return
        self._executor.submit(self.publish, event, data)

    def clear(self, event: Optional[str] = None) -> int:
        """Rensa prenumerationer.

        Args:
            event: Specifikt event att rensa, eller None för alla.

        Returns:
            Antal borttagna prenumerationer.
        """
        with self._lock:
            removed = 0

            # Rensa allt
            if event is None:
                removed += sum(len(refs) for refs in self._handlers.values())
                removed += sum(len(refs) for refs in self._patterns.values())
                self._handlers.clear()
                self._patterns.clear()
                self._update_snapshot()
                log.info("Alla event-handlers rensade")
                return removed

            # Rensa wildcard-mönster
            if self._is_pattern(event):
                try:
                    translated = fnmatch.translate(event)
                    to_remove = [
                        pattern for pattern in self._patterns
                        if pattern.pattern == translated
                    ]
                    for pattern in to_remove:
                        removed += len(self._patterns[pattern])
                        del self._patterns[pattern]
                    if removed:
                        self._update_snapshot()
                        log.debug(
                            "Rensade %d handlers för mönster %r", removed, event
                        )
                except re.error as exc:
                    log.warning(
                        "Ogiltigt wildcard vid clear(%r): %s", event, exc
                    )
                return removed

            # Rensa exakt event
            if event in self._handlers:
                removed = len(self._handlers[event])
                del self._handlers[event]
                self._update_snapshot()
                log.debug("Rensade %d handlers för event %r", removed, event)

            return removed

    def shutdown(self) -> None:
        """Stäng ner EventBus och vänta på pågående async-tasks."""
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True
            log.info("EventBus stänger ner...")

        self._executor.shutdown(wait=True, cancel_futures=True)
        self.clear()
        log.debug("EventBus nedstängd")

    def get_subscribers(self, event: str) -> int:
        """Returnera antal aktiva prenumeranter för ett event."""
        # Samla refs under lock (snabbt), evaluera utanför (kan ta tid)
        with self._lock:
            exact_refs: List[weakref.ReferenceType[Any]] = list(
                self._handlers.get(event, [])
            )
            pattern_refs: List[weakref.ReferenceType[Any]] = []
            for pattern, refs in self._patterns.items():
                if pattern.match(event):
                    pattern_refs.extend(refs)

        count = 0
        seen: Set[int] = set()
        for ref in exact_refs + pattern_refs:
            handler = ref()
            if handler is not None:
                handler_id = id(handler)
                if handler_id not in seen:
                    seen.add(handler_id)
                    count += 1
        return count

    # ─────────────────────────────────────────────────────────────────────
    # Interna hjälpmetoder
    # ─────────────────────────────────────────────────────────────────────

    def _make_ref(
        self,
        handler: Callable[..., Any],
    ) -> Optional[weakref.ReferenceType[Any]]:
        """Skapa en weak reference till en handler.

        Hanterar bundna metoder (WeakMethod) och vanliga funktioner.
        """
        try:
            if hasattr(handler, "__self__") and hasattr(handler, "__func__"):
                return weakref.WeakMethod(handler)
            return weakref.ref(handler)
        except TypeError as exc:
            log.debug(
                "Kunde inte skapa weakref för handler %r: %s", handler, exc
            )
            return None

    def _is_pattern(self, event: str) -> bool:
        """Returnera True om event innehåller wildcard-tecken."""
        return any(char in event for char in ("*", "?", "["))

    def _subscribe_pattern(
        self,
        event: str,
        ref:   weakref.ReferenceType[Any],
    ) -> None:
        """Lägg till en wildcard-prenumeration."""
        try:
            pattern = re.compile(fnmatch.translate(event))
            self._patterns.setdefault(pattern, []).append(ref)
            log.debug("Prenumererar på mönster %r", event)
        except re.error as exc:
            log.error("Ogiltigt wildcard-mönster %r: %s", event, exc)

    def _update_snapshot(self) -> None:
        """(kallad med self._lock hållen) Bygg om dispatch-snapshot."""
        self._snapshot = self._build_snapshot()
        self._pub_since_refresh = 0

    def _refresh(self) -> None:
        """Bygg om snapshot för att rensa döda weakrefs (periodisk)."""
        with self._lock:
            self._update_snapshot()

    def _build_snapshot(
        self,
    ) -> Dict[str, Tuple[weakref.ReferenceType[Any], ...]]:
        """
        (kallad med self._lock hållen)

        Bygg ny snapshot från handlers + patterns och rensa döda refs.

        Snapshotten innehåller endast weakrefs (aldrig starka referenser)
        så att handlers som ägaren släppt kan garbage-collectas.
        """
        snap: Dict[str, Tuple[weakref.ReferenceType[Any], ...]] = {}

        # Exakta handlers
        for event, refs in list(self._handlers.items()):
            alive = [ref for ref in refs if ref() is not None]
            if alive:
                self._handlers[event] = alive
                snap[event] = tuple(alive)
            else:
                del self._handlers[event]

        # Mönster: rensa döda refs på plats (expanderas ej – matchas live)
        for pattern, refs in list(self._patterns.items()):
            alive = [ref for ref in refs if ref() is not None]
            if alive:
                self._patterns[pattern] = alive
            else:
                del self._patterns[pattern]

        return snap

    def _dispatch_patterns(
        self,
        event:   str,
        payload: Dict[str, Any],
    ) -> int:
        """Anropa wildcard-handlers som matchar event (ovanlig sökväg)."""
        called = 0
        # Kopiera under lås för att undvika mutation under iteration
        with self._lock:
            items = list(self._patterns.items())

        for pattern, refs in items:
            if not pattern.match(event):
                continue
            for ref in list(refs):
                handler = ref()
                if handler is None:
                    continue
                try:
                    handler(payload)
                    called += 1
                except Exception as exc:
                    log.exception(
                        "Fel i event-handler för %r (wildcard): %s "
                        "(handler: %r)",
                        event, exc, handler,
                    )
        return called

    @staticmethod
    def _remove_from_list(
        refs:    List[weakref.ReferenceType[Any]],
        handler: Callable[..., Any],
    ) -> bool:
        """Ta bort en handler från en ref-lista.

        Hanterar WeakMethod korrekt (v3.5.1):
        WeakMethod.__call__() skapar en NY bound method-instans varje
        gång – så "current is handler" slår aldrig till för bundna
        metoder. Därför jämförs även (__self__, __func__).
        """
        for index, ref in enumerate(refs):
            current = ref()
            if current is handler:
                refs.pop(index)
                return True
            # WeakMethod-fall: jämför funktion + bunden instans
            if (
                hasattr(handler, "__self__")
                and hasattr(handler, "__func__")
                and hasattr(current, "__self__")
                and hasattr(current, "__func__")
                and current.__self__ is handler.__self__
                and current.__func__ is handler.__func__
            ):
                refs.pop(index)
                return True
        return False

    def __repr__(self) -> str:
        # Hämta data under lock, släpp innan f-string
        with self._lock:
            exact    = sum(len(refs) for refs in self._handlers.values())
            wildcard = sum(len(refs) for refs in self._patterns.values())
            shutdown = self._shutdown

        return (
            f"EventBus(exact={exact}, wildcard={wildcard}, "
            f"shutdown={shutdown})"
        )


# ============================================================================
# Singleton-instans
# ============================================================================

bus: EventBus = EventBus()


def get_bus() -> EventBus:
    """Returnera den globala EventBus-singleton-instansen."""
    return bus


# ============================================================================
# Publikt API
# ============================================================================

__all__ = [
    "EventBus",
    "bus",
    "get_bus",
]
