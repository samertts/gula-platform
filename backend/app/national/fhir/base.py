from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FHIRMeta:
    version_id: str = ""
    last_updated: str = ""
    source: str = ""
    profile: list[str] = field(default_factory=list)
    tag: list[dict] = field(default_factory=list)
    security: list[dict] = field(default_factory=list)


@dataclass
class FHIRIdentifier:
    use: str = "usual"
    type: dict | None = None
    system: str = ""
    value: str = ""
    period: dict | None = None
    assigner: dict | None = None


@dataclass
class FHIRCoding:
    system: str = ""
    version: str = ""
    code: str = ""
    display: str = ""
    user_selected: bool = False


@dataclass
class FHIRCodeableConcept:
    coding: list[FHIRCoding] = field(default_factory=list)
    text: str = ""


@dataclass
class FHIRReference:
    reference: str = ""
    type: str = ""
    identifier: FHIRIdentifier | None = None
    display: str = ""


@dataclass
class FHIRPeriod:
    start: str = ""
    end: str = ""


@dataclass
class FHIRHumanName:
    use: str = "official"
    text: str = ""
    family: str = ""
    given: list[str] = field(default_factory=list)
    prefix: list[str] = field(default_factory=list)
    suffix: list[str] = field(default_factory=list)


@dataclass
class FHIRContactPoint:
    system: str = ""
    value: str = ""
    use: str = ""
    rank: int = 1


@dataclass
class FHIRAddress:
    use: str = "home"
    type: str = "physical"
    text: str = ""
    line: list[str] = field(default_factory=list)
    city: str = ""
    district: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""


class FHIRResource:
    resource_type: str = ""
    id: str = ""
    meta: FHIRMeta | None = None
    implicit_rules: str = ""
    language: str = "ar"

    def to_dict(self) -> dict[str, Any]:
        result = {"resourceType": self.resource_type, "id": self.id}
        if self.meta:
            result["meta"] = {k: v for k, v in self.meta.__dict__.items() if v}
        if self.language:
            result["language"] = self.language
        return result
