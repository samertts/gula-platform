"""PROGRAM-STABLE-004 — Domain versioning (Phase 5 + DOMAIN_VERSIONING).

Every Domain is versioned independently (SemVer MAJOR.MINOR.PATCH) and is
independently certifiable. Backward compatibility is a hard rule: a version
bump may never break a published contract's consumers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.domain_platform.core import utcnow

_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class InvalidVersionError(ValueError):
    pass


@dataclass(frozen=True)
class DomainVersion:
    """An immutable, independently versioned Domain release."""

    domain_code: str
    version: str
    semver: tuple[int, int, int]
    certified: bool
    compatibility: dict[str, str]
    changelog: str
    created_at: str = field(default_factory=lambda: utcnow().isoformat())

    @property
    def major(self) -> int:
        return self.semver[0]

    @property
    def minor(self) -> int:
        return self.semver[1]

    @property
    def patch(self) -> int:
        return self.semver[2]

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_code": self.domain_code,
            "version": self.version,
            "semver": list(self.semver),
            "certified": self.certified,
            "compatibility": self.compatibility,
            "changelog": self.changelog,
            "created_at": self.created_at,
        }


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse a SemVer string into (major, minor, patch)."""
    match = _SEMVER_RE.match(version.strip())
    if not match:
        raise InvalidVersionError(f"invalid semantic version '{version}'")
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def compare_versions(a: str, b: str) -> int:
    """SemVer comparison: -1 when a < b, 0 when equal, 1 when a > b."""
    av = parse_version(a)
    bv = parse_version(b)
    if av < bv:
        return -1
    if av > bv:
        return 1
    return 0


def is_compatible(previous: str, next_version: str) -> bool:
    """Backward-compatibility gate.

    A version is backward compatible when the MAJOR number does not
    increase. A breaking change requires a MAJOR bump, and MAJOR increases
    are only permitted when the previous version is explicitly certified
    compatible (the gate is enforced by DomainCertification).
    """
    prev = parse_version(previous)
    nxt = parse_version(next_version)
    if nxt[0] > prev[0]:
        return False
    if nxt[0] == prev[0] and nxt[1] > prev[1]:
        return True
    if nxt[0] == prev[0] and nxt[1] == prev[1]:
        return nxt[2] >= prev[2]
    return False


class DomainVersionRegistry:
    """Version history for a single Domain (independent versioning)."""

    def __init__(self, domain_code: str) -> None:
        self.domain_code = domain_code
        self.versions: list[DomainVersion] = []

    def add(
        self,
        version: str,
        certified: bool = False,
        compatibility: dict[str, str] | None = None,
        changelog: str = "",
    ) -> DomainVersion:
        semver = parse_version(version)
        if self.versions:
            current = self.versions[-1]
            if compare_versions(version, current.version) <= 0:
                raise InvalidVersionError(
                    f"version '{version}' must be greater than current "
                    f"'{current.version}'"
                )
            if not is_compatible(current.version, version) and not certified:
                raise InvalidVersionError(
                    f"version '{version}' breaks backward compatibility with "
                    f"'{current.version}' and is not certified"
                )
        record = DomainVersion(
            domain_code=self.domain_code,
            version=version,
            semver=semver,
            certified=certified,
            compatibility=compatibility or {},
            changelog=changelog,
        )
        self.versions.append(record)
        return record

    @property
    def latest(self) -> DomainVersion | None:
        return self.versions[-1] if self.versions else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_code": self.domain_code,
            "versions": [v.to_dict() for v in self.versions],
        }
