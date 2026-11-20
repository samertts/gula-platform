"""Unified logical language runtime.

The runtime resolves language preferences, applies the English fallback,
exposes direction and formatting helpers, and prevents raw translation keys
from reaching end users. Formatting functions return display values only;
stored clinical values are never mutated.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .language_registry import LanguageRegistry

ENGINE_VERSION = "1.0.0"
TRANSLATION_KEY_RE = re.compile(
    r"^(ui|action|label|message|error|clinical)\.[a-z0-9_]+(?:\.[a-z0-9_-]+){0,4}$"
)

_DIGIT_MAPS: dict[str, dict[str, str]] = {
    "ar": dict(zip("0123456789", "٠١٢٣٤٥٦٧٨٩", strict=True)),
    "fa": dict(zip("0123456789", "۰۱۲۳۴۵۶۷۸۹", strict=True)),
    "ur": dict(zip("0123456789", "۰۱۲۳۴۵۶۷۸۹", strict=True)),
}
for _language in ("ckb", "PENDING_SYRIAC"):
    _DIGIT_MAPS[_language] = dict(zip("0123456789", "٠١٢٣٤٥٦٧٨٩", strict=True))


class RuntimeErrorGuls(ValueError):
    """Base error for GULS runtime failures."""


class MissingTranslationError(RuntimeErrorGuls):
    """Raised in strict mode when a catalog key is absent."""


class NoUsableLanguageError(RuntimeErrorGuls):
    """Raised when neither requested, preferred, nor fallback language is usable."""


class InvalidTranslationKeyError(RuntimeErrorGuls):
    """Raised when a key violates the approved translation key convention."""


@dataclass(frozen=True, slots=True)
class Resolution:
    requested: str | None
    selected: str
    fallback_used: bool
    direction: str
    locale_tag: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class StableMessage:
    """Backend contract: stable code and parameters, never translated prose."""

    code: str
    parameters: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "parameters": dict(self.parameters)}
        if self.correlation_id is not None:
            payload["correlation_id"] = self.correlation_id
        return payload


def is_valid_translation_key(key: str) -> bool:
    return bool(TRANSLATION_KEY_RE.fullmatch(key))


class LanguageRuntime:
    """Shared logical behavior used by every GULA interface."""

    def __init__(self, registry: LanguageRegistry) -> None:
        self.registry = registry

    def resolve(
        self,
        requested: str | None,
        available_language_ids: set[str],
        preferred: str | None = None,
    ) -> Resolution:
        """Resolve requested -> preferred -> mandatory English fallback."""
        requested_def = self.registry.resolve(requested) if requested else None
        preferred_def = self.registry.resolve(preferred) if preferred else None
        fallback = self.registry.fallback()

        if (
            requested_def
            and requested_def.is_active
            and requested_def.language_id in available_language_ids
        ):
            return Resolution(
                requested=requested,
                selected=requested_def.language_id,
                fallback_used=False,
                direction=requested_def.direction or fallback.direction or "ltr",
                locale_tag=requested_def.locale_tag,
                reason="requested_ready",
            )

        if (
            preferred_def
            and preferred_def.is_active
            and preferred_def.language_id in available_language_ids
        ):
            return Resolution(
                requested=requested,
                selected=preferred_def.language_id,
                fallback_used=True,
                direction=preferred_def.direction or "ltr",
                locale_tag=preferred_def.locale_tag,
                reason="preferred_ready",
            )

        if fallback.language_id in available_language_ids and fallback.is_active:
            return Resolution(
                requested=requested,
                selected=fallback.language_id,
                fallback_used=True,
                direction=fallback.direction or "ltr",
                locale_tag=fallback.locale_tag,
                reason="mandatory_fallback",
            )

        raise NoUsableLanguageError("no active usable language including English fallback")

    def direction(self, language_id: str) -> str:
        definition = self.registry.resolve(language_id)
        if definition is None or not definition.is_active or definition.direction is None:
            definition = self.registry.fallback()
        return "rtl" if definition.direction == "rtl" else "ltr"

    def translate(
        self,
        catalog: Mapping[str, str],
        key: str,
        *,
        fallback_catalog: Mapping[str, str] | None = None,
        parameters: Mapping[str, Any] | None = None,
        strict: bool = False,
    ) -> str:
        """Translate a key without ever returning the raw key to a user."""
        if not is_valid_translation_key(key):
            raise InvalidTranslationKeyError(f"invalid translation key: {key!r}")
        template = catalog.get(key)
        used_fallback = False
        if not template and fallback_catalog is not None:
            template = fallback_catalog.get(key)
            used_fallback = True
        if template is None:
            if strict:
                raise MissingTranslationError(key)
            # Empty display text is safe; a raw key is not.
            return ""
        if parameters:
            try:
                return template.format(**parameters)
            except (KeyError, IndexError, ValueError):
                if strict:
                    raise MissingTranslationError(f"unresolvable parameters for {key}") from None
                return ""
        return template if not used_fallback or template else ""

    def missing_keys(
        self, catalog: Mapping[str, str], reference_catalog: Mapping[str, str]
    ) -> tuple[str, ...]:
        return tuple(sorted(set(reference_catalog) - set(catalog)))

    @staticmethod
    def _localize_digits(value: str, language_id: str) -> str:
        digit_map = _DIGIT_MAPS.get(language_id)
        if not digit_map:
            return value
        return value.translate(str.maketrans(digit_map))

    def format_number(
        self,
        value: int | float | Decimal | str,
        language_id: str,
        *,
        group: bool = True,
        maximum_fraction_digits: int = 6,
    ) -> str:
        """Format a numeric display value; the caller's source value is untouched."""
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise RuntimeErrorGuls("invalid numeric value") from exc
        quantized = decimal_value.normalize()
        sign, _digits, exponent = quantized.as_tuple()
        if exponent < 0:
            places = min(maximum_fraction_digits, -exponent)
            text = f"{decimal_value:,.{places}f}" if group else f"{decimal_value:.{places}f}"
        else:
            text = f"{int(decimal_value):,}" if group else str(int(decimal_value))
        if sign:
            text = f"-{text.lstrip('-')}"
        return self._localize_digits(text, language_id)

    def format_identifier(self, value: str) -> str:
        """Medical, national, and laboratory identifiers are never transformed."""
        return value

    def format_date(
        self,
        value: date | datetime | str,
        language_id: str,
        *,
        style: str = "numeric",
    ) -> str:
        """Return a display date while preserving the ISO source value."""
        if isinstance(value, str):
            parsed = date.fromisoformat(value[:10])
        elif isinstance(value, datetime):
            parsed = value.date()
        else:
            parsed = value
        if style == "iso":
            return parsed.isoformat()
        if style == "long":
            # Month names are intentionally not invented; use numeric display.
            text = f"{parsed.day:02d}/{parsed.month:02d}/{parsed.year}"
        else:
            text = parsed.strftime("%Y-%m-%d")
        return self._localize_digits(text, language_id)

    @staticmethod
    def stable_message(
        code: str,
        parameters: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> StableMessage:
        """Build a backend error contract containing a code, not translated prose."""
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", code):
            raise RuntimeErrorGuls(f"invalid stable error code: {code!r}")
        return StableMessage(code=code, parameters=dict(parameters or {}), correlation_id=correlation_id)

    @staticmethod
    def plural_category(count: int, language_id: str) -> str:
        """Minimal CLDR-like categories for supported UI plural selection."""
        absolute = abs(count)
        if language_id in {"ar", "ckb"}:
            if absolute == 0:
                return "zero"
            if absolute == 1:
                return "one"
            if absolute == 2:
                return "two"
            if 3 <= absolute <= 10:
                return "few"
            return "many"
        if language_id == "en":
            return "one" if absolute == 1 else "other"
        return "other"

    @staticmethod
    def shape_for_display(text: str) -> str:
        """Produce a visual-only RTL presentation; never mutate stored text."""
        try:
            import arabic_reshaper  # type: ignore[import-not-found]
            from bidi.algorithm import get_display  # type: ignore[import-not-found]
        except ImportError:
            return text
        if not any("\u0600" <= char <= "\u06ff" for char in text):
            return text
        return get_display(arabic_reshaper.reshape(text))

    def runtime_contract(self) -> dict[str, Any]:
        return {
            "engine_version": ENGINE_VERSION,
            "fallback_language": self.registry.fallback_language,
            "key_convention": TRANSLATION_KEY_RE.pattern,
            "direction_values": ["ltr", "rtl"],
            "identifier_policy": "identifiers_and_clinical_values_are_never_translated",
        }
