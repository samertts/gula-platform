"""Canonical language registry for the GULA Universal Language System (GULS).

The registry is data, not code: adding a language does not require changing the
runtime engine. Language identifiers, BCP 47 locale tags, scripts, and writing
directions are deliberately separate concepts.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOCALE_TAG_RE = re.compile(
    r"^[A-Za-z]{2,3}"
    r"(?:-[A-Za-z]{4})?"
    r"(?:-(?:[A-Za-z]{2}|[0-9]{3}))?"
    r"(?:-[A-Za-z0-9]{5,8})*$"
)


class RegistryError(ValueError):
    """Raised when the registry data is invalid."""


@dataclass(frozen=True, slots=True)
class LanguageDefinition:
    language_id: str
    locale_tag: str | None
    native_name: str | None
    english_name: str
    language: str
    dialect: str | None
    region: str | None
    script: str | None
    direction: str | None
    classification: str
    is_active: bool
    is_publishable: bool
    approval_status: str
    linguistic_approval_status: str
    clinical_approval_status: str
    pack_version: str
    minimum_engine_version: str
    translation_coverage: float
    terminology_version: str | None
    catalogs: tuple[str, ...]
    notes: str

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> LanguageDefinition:
        required = (
            "language_id", "english_name", "language", "classification",
            "is_active", "is_publishable", "approval_status",
            "linguistic_approval_status", "clinical_approval_status",
            "pack_version", "minimum_engine_version", "translation_coverage",
        )
        if not isinstance(data, dict):
            raise RegistryError("language entry must be an object")
        for key in required:
            if key not in data:
                raise RegistryError(f"language entry is missing required field: {key}")

        locale_tag = data.get("locale_tag")
        if locale_tag is not None and not is_valid_locale_tag(locale_tag):
            raise RegistryError(f"invalid BCP 47 locale tag: {locale_tag!r}")
        direction = data.get("direction")
        if direction not in (None, "ltr", "rtl"):
            raise RegistryError(f"invalid writing direction: {direction!r}")
        if data["classification"] not in ("core", "downloadable"):
            raise RegistryError(f"invalid classification: {data['classification']!r}")
        for key in ("is_active", "is_publishable"):
            if not isinstance(data[key], bool):
                raise RegistryError(f"{key} must be a boolean")
        approval_values = ("approved", "blocked", "pending", "not_applicable", "approved_source")
        for key in ("approval_status", "linguistic_approval_status", "clinical_approval_status"):
            if data[key] not in approval_values:
                raise RegistryError(f"invalid {key}: {data[key]!r}")
        if not data["is_active"] and data.get("locale_tag") is not None:
            raise RegistryError("inactive language must not declare a locale tag")
        if not isinstance(data["translation_coverage"], (int, float)) or not 0.0 <= data["translation_coverage"] <= 1.0:
            raise RegistryError("translation_coverage must be between 0 and 1")
        catalogs = data.get("catalogs", [])
        if not isinstance(catalogs, list) or not all(isinstance(item, str) for item in catalogs):
            raise RegistryError("catalogs must be a list of strings")
        return cls(
            language_id=str(data["language_id"]),
            locale_tag=locale_tag,
            native_name=data.get("native_name"),
            english_name=str(data["english_name"]),
            language=str(data["language"]),
            dialect=data.get("dialect"),
            region=data.get("region"),
            script=data.get("script"),
            direction=direction,
            classification=str(data["classification"]),
            is_active=data["is_active"],
            is_publishable=data["is_publishable"],
            approval_status=str(data["approval_status"]),
            linguistic_approval_status=str(data["linguistic_approval_status"]),
            clinical_approval_status=str(data["clinical_approval_status"]),
            pack_version=str(data["pack_version"]),
            minimum_engine_version=str(data["minimum_engine_version"]),
            translation_coverage=float(data["translation_coverage"]),
            terminology_version=data.get("terminology_version"),
            catalogs=tuple(catalogs),
            notes=str(data.get("notes", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "language_id": self.language_id,
            "locale_tag": self.locale_tag,
            "native_name": self.native_name,
            "english_name": self.english_name,
            "language": self.language,
            "dialect": self.dialect,
            "region": self.region,
            "script": self.script,
            "direction": self.direction,
            "classification": self.classification,
            "is_active": self.is_active,
            "is_publishable": self.is_publishable,
            "approval_status": self.approval_status,
            "linguistic_approval_status": self.linguistic_approval_status,
            "clinical_approval_status": self.clinical_approval_status,
            "pack_version": self.pack_version,
            "minimum_engine_version": self.minimum_engine_version,
            "translation_coverage": self.translation_coverage,
            "terminology_version": self.terminology_version,
            "catalogs": list(self.catalogs),
            "notes": self.notes,
        }

    def public_dict(self) -> dict[str, Any]:
        """Registry projection safe for the localization API and UI selectors."""
        return {
            "language_id": self.language_id,
            "locale_tag": self.locale_tag,
            "native_name": self.native_name,
            "english_name": self.english_name,
            "direction": self.direction,
            "script": self.script,
            "region": self.region,
            "classification": self.classification,
            "approval_status": self.approval_status,
            "is_active": self.is_active,
            "is_publishable": self.is_publishable,
            "pack_version": self.pack_version,
            "translation_coverage": self.translation_coverage,
        }


def is_valid_locale_tag(value: str) -> bool:
    """Validate the BCP 47 subset used by GULA without inventing new tags."""
    return bool(isinstance(value, str) and LOCALE_TAG_RE.fullmatch(value))


def _default_registry_path() -> Path:
    env_path = os.getenv("GULS_REGISTRY_PATH")
    if env_path:
        return Path(env_path)
    # backend/app/localization/language_registry.py -> repository root
    return Path(__file__).resolve().parents[3] / "shared" / "guls" / "language_registry.json"


class LanguageRegistry:
    """Immutable, validated in-memory view of the canonical registry data."""

    def __init__(self, languages: Iterable[LanguageDefinition], fallback_language: str = "en") -> None:
        self._languages = tuple(languages)
        self._by_id = {language.language_id: language for language in self._languages}
        if len(self._by_id) != len(self._languages):
            raise RegistryError("duplicate language_id in registry")
        if fallback_language not in self._by_id:
            raise RegistryError("fallback language missing from registry")
        self.fallback_language = fallback_language
        fallback = self._by_id[fallback_language]
        if not fallback.is_active or fallback.direction != "ltr":
            raise RegistryError("fallback language must be active and LTR")

    @classmethod
    def load(cls, path: Path | None = None) -> LanguageRegistry:
        registry_path = path or _default_registry_path()
        with registry_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise RegistryError("registry root must be an object")
        fallback = payload.get("fallback_language")
        if fallback != "en":
            raise RegistryError("GULS requires English as the mandatory fallback language")
        entries = payload.get("languages")
        if not isinstance(entries, list) or not entries:
            raise RegistryError("registry must contain a non-empty languages array")
        languages = [LanguageDefinition.from_mapping(item) for item in entries]
        return cls(languages, fallback_language=fallback)

    def all(self) -> tuple[LanguageDefinition, ...]:
        return self._languages

    def get(self, language_id: str) -> LanguageDefinition | None:
        return self._by_id.get(language_id)

    def require(self, language_id: str) -> LanguageDefinition:
        language = self.get(language_id)
        if language is None:
            raise RegistryError(f"unknown language_id: {language_id!r}")
        return language

    def resolve(self, identifier: str | None) -> LanguageDefinition | None:
        """Resolve either a stable internal ID or a BCP 47 locale tag."""
        if not identifier:
            return None
        if identifier in self._by_id:
            return self._by_id[identifier]
        lowered = identifier.lower()
        for language in self._languages:
            if language.locale_tag and language.locale_tag.lower() == lowered:
                return language
        return None

    def fallback(self) -> LanguageDefinition:
        return self._by_id[self.fallback_language]

    def core(self) -> tuple[LanguageDefinition, ...]:
        return tuple(item for item in self._languages if item.classification == "core")

    def downloadable(self) -> tuple[LanguageDefinition, ...]:
        return tuple(item for item in self._languages if item.classification == "downloadable")

    def active(self) -> tuple[LanguageDefinition, ...]:
        return tuple(item for item in self._languages if item.is_active)


def core_language_ids(registry: LanguageRegistry) -> set[str]:
    return {language.language_id for language in registry.core()}
