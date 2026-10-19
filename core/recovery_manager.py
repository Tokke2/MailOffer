#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RecoveryManager – Hanterar modulfel och automatisk avaktivering.

Version: 3.5 – SNABB STATUSKONTROLL + PUTSAD OCH KÖRBAR (spec §16 / §14.1)

Fixar mot v3.4:
- Korrupt markdown/inklistringssyntax borttagen
  (__init__, __repr__, __all__, __future__, log.info,
   recovery_mgr.is_disabled, >=)
- SNABBARE: is_disabled() utan lås
    * @safe_module anropar is_disabled() vid VARJE wrappat anrop.
      Nu: O(1)-check mot _disabled_cache (set-membership är atomärt
      i CPython) – ingen RLock per anrop.
- SNABBARE: publish sker EFTER att låset släppts
    * record_failure()/reset()/reset_all() höll tidigare RLock under
      hela bus.publish() (inkl. alla UI-handlers) = onödig
      lock-kontention för andra trådar. Nu: samla status under lås,
      publicera utanför.
- SNABBARE: debug-loggning guardad med log.isEnabledFor()
- Korrekt docstring-filnamn: core/recovery_manager.py
- Event-payload "module.error" följer spec: {module, error, count}
  och behåller "disable" för bakåtkompatibilitet
- Event-payload "module.disabled" innehåller även "count"
- record_error() alias för record_failure()
- Pylance/type-fix för global recovery_manager
- Korrekt safe_module()-dekorerare
- Robust loggning och trådsäker statusåtkomst

Funktioner:
- Spårar fel per modul i minnet
- Inaktiverar modul automatiskt efter 3 misslyckanden
- Publicerar händelser via EventBus
- Thread-safe statushantering (RLock för mutationer, lås-fri läsning)
- Dekorator @safe_module för enkel och säker felhantering

FIL: core/recovery_manager.py
"""

from __future__ import annotations

import logging
import threading
from functools import wraps
from typing import Any, Callable, Dict, Optional, Set, TypeVar, cast

from core.event_bus import EventBus

log = logging.getLogger(__name__)

FAILURE_THRESHOLD = 3

F = TypeVar("F", bound=Callable[..., Any])


class RecoveryManager:
    """Hanterar livscykel och felförebyggande för applikationsmoduler.

    - Spårar antal misslyckanden per modul
    - Inaktiverar moduler automatiskt vid upprepade fel (3-strike)
    - Publicerar händelser till EventBus för UI-notifikationer
    - Thread-safe via threading.RLock (mutationer) + lås-fri
      O(1)-kontroll av disabled-status via _disabled_cache (v3.5)
    - Status hålls enbart i minnet (rensas vid omstart)
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus
        self._lock = threading.RLock()
        self._modules: Dict[str, Dict[str, Any]] = {}
        # Lås-fri snabbkoll: namnen på inaktiverade moduler (v3.5)
        self._disabled_cache: Set[str] = set()
        log.debug("RecoveryManager initierad (v3.5)")

    # ------------------------------------------------------------------
    # Registrering
    # ------------------------------------------------------------------

    def register_module(self, name: str) -> None:
        """Registrera en modul för felövervakning.

        Auto-registrering sker även i record_failure(); denna metod är för
        explicit pre-registrering.
        """
        module_name = (name or "").strip()
        if not module_name:
            return

        with self._lock:
            if module_name not in self._modules:
                self._modules[module_name] = {
                    "failures": 0,
                    "disabled": False,
                    "last_error": None,
                }
                log.debug(
                    "Modul registrerad för övervakning: %s", module_name
                )

    # ------------------------------------------------------------------
    # Felhantering
    # ------------------------------------------------------------------

    def record_failure(self, module: str, error: Exception) -> None:
        """Registrera ett fel för en modul och uppdatera status.

        Vid 3 fel inaktiveras modulen och händelser publiceras.

        Publicerar (efter att låset släppts – v3.5):
        - module.error: {module, error, count, disable}
        - module.disabled: {module, reason, count}
        """
        module_name = (module or "").strip() or "unknown_module"

        # ── Samla ny status under lås ──────────────────────────────
        with self._lock:
            if module_name not in self._modules:
                self._modules[module_name] = {
                    "failures": 0,
                    "disabled": False,
                    "last_error": None,
                }

            state = self._modules[module_name]
            state["failures"] += 1
            state["last_error"] = str(error)
            count = int(state["failures"])
            disabled_now = count >= FAILURE_THRESHOLD

            error_msg = (
                f"Modul '{module_name}' misslyckades "
                f"({count}/{FAILURE_THRESHOLD}): {error}"
            )
            log.error(error_msg, exc_info=error)

            was_disabled = bool(state["disabled"])
            if disabled_now and not was_disabled:
                state["disabled"] = True
                self._disabled_cache.add(module_name)
                reason = (
                    f"Automatiskt inaktiverad efter {FAILURE_THRESHOLD} "
                    f"upprepade fel."
                )
                log.warning(
                    "Modul '%s' inaktiverad: %s", module_name, reason
                )

            # Ögonblicksbild för publicering utanför låset
            publish_error = {
                "module": module_name,
                "error": str(error),
                "count": count,
                "disable": disabled_now,
            }
            publish_disabled = None
            if disabled_now and not was_disabled:
                publish_disabled = {
                    "module": module_name,
                    "reason": reason,
                    "count": count,
                }

        # ── Publicera UTANFÖR låset (v3.5 – ingen lock-kontention) ──
        try:
            self._bus.publish("module.error", publish_error)
        except Exception:
            log.debug("module.error publish misslyckades", exc_info=True)

        if publish_disabled is not None:
            try:
                self._bus.publish("module.disabled", publish_disabled)
            except Exception:
                log.debug(
                    "module.disabled publish misslyckades", exc_info=True
                )

    # Alias enligt spec/API
    record_error = record_failure

    # ------------------------------------------------------------------
    # Statuskontroll
    # ------------------------------------------------------------------

    def is_disabled(self, module: str) -> bool:
        """Returnera True om modulen är inaktiverad.

        Lås-fri O(1)-kontroll (v3.5): anropas av @safe_module vid varje
        wrappat anrop, därför får den aldrig ta RLock.
        """
        module_name = (module or "").strip()
        if not module_name:
            return False
        return module_name in self._disabled_cache

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Returnera aktuell status för alla moduler."""
        with self._lock:
            return {
                module: dict(state) for module, state in self._modules.items()
            }

    # ------------------------------------------------------------------
    # Återställning
    # ------------------------------------------------------------------

    def reset(self, module: str) -> None:
        """Återställ en specifik modul till ursprungsläge."""
        module_name = (module or "").strip()
        if not module_name:
            return

        with self._lock:
            if module_name in self._modules:
                self._modules[module_name].update(
                    {
                        "failures": 0,
                        "disabled": False,
                        "last_error": None,
                    }
                )
                self._disabled_cache.discard(module_name)
                log.info("Modul '%s' återställd manuellt.", module_name)
                should_publish = True
            else:
                log.debug(
                    "Modul '%s' är inte registrerad, ingen återställning.",
                    module_name,
                )
                should_publish = False

        if should_publish:
            try:
                self._bus.publish("module.reset", {"module": module_name})
            except Exception:
                log.debug("module.reset publish misslyckades", exc_info=True)

    def reset_all(self) -> None:
        """Återställ alla registrerade moduler."""
        with self._lock:
            for state in self._modules.values():
                state.update(
                    {
                        "failures": 0,
                        "disabled": False,
                        "last_error": None,
                    }
                )
            self._disabled_cache.clear()
            log.info("Alla moduler återställda.")

        try:
            self._bus.publish("module.reset", {"module": "*"})
        except Exception:
            log.debug("module.reset (*) publish misslyckades", exc_info=True)

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        with self._lock:
            active = sum(
                1 for state in self._modules.values()
                if not state["disabled"]
            )
            disabled = sum(
                1 for state in self._modules.values()
                if state["disabled"]
            )
            return (
                f"RecoveryManager(total={len(self._modules)}, "
                f"active={active}, disabled={disabled})"
            )


def safe_module(
    recovery_mgr: RecoveryManager,
    module_name: str,
    *,
    suppress: bool = True,
    fallback: Any = None,
) -> Callable[[F], F]:
    """Dekorator som omsluter funktioner med säker felhantering.

    Funktioner:
    - Kontrollerar om modulen är inaktiverad innan anrop (lås-fri, v3.5)
    - Fångar exceptions, loggar och registrerar fel
    - Inaktiverar automatiskt modulen vid upprepade krascher
    - Returnerar fallback-värde vid fel om suppress=True
    - Låter undantag bubbla vidare om suppress=False
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if recovery_mgr.is_disabled(module_name):
                log.warning(
                    "Ignorerar anrop till inaktiverad modul: %s",
                    module_name,
                )
                return fallback

            try:
                return func(*args, **kwargs)
            except Exception as exc:
                recovery_mgr.record_failure(module_name, exc)
                if not suppress:
                    raise
                log.warning(
                    "Fel i modul %s hanterad säkert, returnerar fallback.",
                    module_name,
                )
                return fallback

        return cast(F, wrapper)

    return decorator


recovery_manager: Optional[RecoveryManager] = None


def init_recovery_manager(event_bus: EventBus) -> RecoveryManager:
    """Initiera och returnera global RecoveryManager-instans."""
    global recovery_manager
    if recovery_manager is None:
        recovery_manager = RecoveryManager(event_bus)
        log.info("Global RecoveryManager initierad.")
    return recovery_manager


__all__ = [
    "RecoveryManager",
    "safe_module",
    "recovery_manager",
    "init_recovery_manager",
    "FAILURE_THRESHOLD",
]
