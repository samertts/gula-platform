"""Pydantic validation for signed language packs and translation governance."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
SAFE_PACK_PATH_RE = re.compile(r"^(catalogs|terminology|formatting|metadata|fonts)/[A-Za-z0-9._/-]+$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PackFileEntry(StrictModel):
    path: str = Field(pattern=SAFE_PACK_PATH_RE.pattern)
    sha256: str = Field(pattern=HASH_RE.pattern)
    size: int = Field(ge=0)


class LanguagePackManifest(StrictModel):
    schema_version: Literal["1.0"]
    language_id: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")
    locale_tag: str = Field(pattern=r"^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$")
    native_name: str = Field(min_length=1)
    fallback_locale: Literal["en"]
    pack_version: str = Field(pattern=VERSION_RE.pattern)
    minimum_engine_version: str = Field(pattern=VERSION_RE.pattern)
    direction: Literal["rtl", "ltr"]
    script: str = Field(pattern=r"^[A-Z][a-z]{3}$")
    catalogs: list[Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]] = Field(min_length=1)
    terminology_version: str = Field(pattern=VERSION_RE.pattern)
    content_hash: str = Field(pattern=HASH_RE.pattern)
    content_size: int = Field(ge=0)
    publisher: str = Field(min_length=1, max_length=120)
    signer_key_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9._:-]+$")
    approval_status: Literal["approved", "synthetic_test_only"]
    created_at: datetime
    files: list[PackFileEntry] = Field(min_length=1)
    signature: str = Field(min_length=1, pattern=r"^[A-Za-z0-9+/]+={0,2}$")

    @model_validator(mode="after")
    def check_schema_invariants(self) -> LanguagePackManifest:
        if any(".." in item.path or item.path.startswith("/") for item in self.files):
            raise ValueError("unsafe file path in manifest")
        paths = [item.path for item in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("duplicate file path in manifest")
        if self.fallback_locale != "en":
            raise ValueError("English fallback is mandatory")
        return self

    def signing_payload(self) -> bytes:
        """Canonical bytes covered by the Ed25519 signature."""
        import json

        payload = self.model_dump(mode="json", exclude={"signature"})
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class ApprovalRecord(StrictModel):
    translation_key: str = Field(min_length=1)
    content_class: Literal["L1", "L2", "L3", "L4"]
    source_text: str
    translated_text: str
    translator: str = Field(min_length=1)
    linguistic_reviewer: str = Field(min_length=1)
    clinical_reviewer: str | None = None
    approved_at: datetime
    package_version: str = Field(pattern=VERSION_RE.pattern)
    change_reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_role_separation(self) -> ApprovalRecord:
        roles = {self.translator.lower(), self.linguistic_reviewer.lower()}
        if self.clinical_reviewer:
            roles.add(self.clinical_reviewer.lower())
        required_distinct = 3 if self.content_class == "L4" else 2
        if len(roles) < required_distinct:
            raise ValueError("approval roles must be distinct")
        if self.content_class == "L4" and not self.clinical_reviewer:
            raise ValueError("L4 content requires documented human clinical approval")
        return self


class TerminologyEntry(StrictModel):
    concept_id: str = Field(min_length=1)
    source_language: Literal["en"]
    loinc: str | None = None
    ucum: str | None = None
    code_system: str | None = None
    code: str | None = None
    original_value: str = Field(min_length=1)
    original_unit: str | None = None
    translated_display: str = Field(min_length=1)
    translated_display_language: str = Field(min_length=1)
    approval_class: Literal["L1", "L2", "L3", "L4"]
    approval_record_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_separation(self) -> TerminologyEntry:
        if self.translated_display == self.original_value and self.original_unit:
            raise ValueError("translated display must be a separate field from original clinical value and unit")
        return self


def parse_version(value: str) -> tuple[int, int, int]:
    if not VERSION_RE.fullmatch(value):
        raise ValueError(f"invalid semantic version: {value!r}")
    return tuple(int(part) for part in value.split("."))  # type: ignore[return-value]


def version_ge(left: str, right: str) -> bool:
    return parse_version(left) >= parse_version(right)
