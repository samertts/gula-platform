"""GULA Platform Foundation — standardized reusable modules for all platforms."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("gula.platform")


class PlatformRegistry:
    """Central registry for all platform modules.

    Every platform module registers itself at import time so the
    platform can enumerate capabilities, health, and module metadata.
    """

    _modules: dict[str, Any] = {}
    _capabilities: dict[str, list[dict]] = {}
    _availability: dict[str, tuple[bool, str | None]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        module,
        capabilities: list[dict] | None = None,
        *,
        available: bool = True,
        unavailable_reason: str | None = None,
    ) -> None:
        """Register a module and say whether its capabilities can actually run.

        IA-058. ``available`` defaults to True so existing registrations are
        unchanged, but a module that cannot serve a request must pass False and
        a reason: registering is not the same as working, and the capability
        listing is read as a statement about what the platform can do.
        """
        if not available and not unavailable_reason:
            raise ValueError(
                f"module {name!r} registered as unavailable without a reason; "
                "an unexplained outage in the capability listing is worse than "
                "none, because it cannot be acted on",
            )
        cls._modules[name] = module
        if capabilities:
            cls._capabilities[name] = capabilities
        cls._availability[name] = (available, unavailable_reason)
        if available:
            logger.debug("[PLATFORM] Registered module: %s", name)
        else:
            logger.warning("[PLATFORM] Registered UNAVAILABLE module %s: %s", name, unavailable_reason)

    @classmethod
    def get(cls, name: str) -> Any:
        return cls._modules.get(name)

    @classmethod
    def list_modules(cls) -> list[str]:
        return list(cls._modules.keys())

    @classmethod
    def get_capabilities(cls) -> list[dict]:
        """Every registered capability, each saying whether it can be invoked.

        IA-058. This used to mutate the stored capability dicts in place
        (``cap["module"] = name``) and hand out references to registry state,
        so a caller editing a returned dict edited the registry. Each entry is
        now a copy.

        The ``available`` and ``unavailable_reason`` fields are additive, so
        existing readers keep working while gaining the ability to tell a
        capability that runs from one that only exists.
        """
        result = []
        for name, caps in cls._capabilities.items():
            available, reason = cls._availability.get(name, (True, None))
            for cap in caps:
                entry = dict(cap)
                entry["module"] = name

                # IA-079, correcting IA-058. This was
                # ``entry["available"] = available``, which overwrote a
                # capability's own declaration with the module-level default —
                # so a module that works overall silently republished one of
                # its broken capabilities as available. The more specific
                # statement wins, and never the other way round: a module
                # marked unavailable makes every capability unavailable, and a
                # capability may declare itself unavailable inside a working
                # module.
                cap_available = bool(cap.get("available", True))
                entry["available"] = available and cap_available
                if not entry["available"]:
                    entry["unavailable_reason"] = (
                        cap.get("unavailable_reason")
                        if not cap_available
                        else reason
                    ) or reason or (
                        f"capability {cap.get('name', '?')!r} is marked "
                        f"unavailable but gave no reason"
                    )
                result.append(entry)
        return result

    @classmethod
    def health(cls) -> dict[str, str]:
        """Per-module state.

        IA-058. This returned "registered" for every module unconditionally,
        including modules whose every entry point raises. "registered" was
        true but read as healthy, so a module that cannot run reported the
        same string as one that can.
        """
        return {
            name: ("registered" if cls._availability.get(name, (True, None))[0] else "unavailable")
            for name in cls._modules
        }


import logging

logger = logging.getLogger("gula.platform")
