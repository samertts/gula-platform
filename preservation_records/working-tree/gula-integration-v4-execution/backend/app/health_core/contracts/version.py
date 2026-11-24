"""Contract versioning for synthetic Health Core development.

The version is explicit and additive-only, mirroring contract rule R-VER-1 of the
national service contracts: a new surface is additive, existing names are never
renamed, and a breaking re-shape requires a new major version (plus the owner's
ADR before it could ever be presented as a national contract). These constants
describe a LOCAL, SYNTHETIC-ONLY contract family. They are not an OpenAPI version
and are not served by any application route.
"""

from __future__ import annotations

HEALTH_CORE_CONTRACT_VERSION = "1.0.0-alpha1"

#: Contract family classification. This is deliberately NOT a national status.
CONTRACT_STATUS = "LOCAL_SYNTHETIC_ONLY"

#: Only versions with this major number are wire-compatible with this module.
COMPATIBLE_MAJOR = 1


def contract_major(version: str) -> int:
    """Return the numeric major component of a semantic version string.

    Prerelease suffixes (e.g. ``-alpha1``) are ignored. A malformed version
    raises ``ValueError`` so the contract cannot be silently mis-versioned.
    """
    if not isinstance(version, str):
        raise ValueError("contract version must be a string")
    core = version.split("-", 1)[0]
    parts = core.split(".")
    if len(parts) != 3:
        raise ValueError(f"contract version must have three components: {version!r}")
    try:
        return int(parts[0])
    except ValueError as exc:
        raise ValueError(f"contract major must be numeric: {version!r}") from exc


def is_compatible_version(version: str) -> bool:
    """True when ``version`` is wire-compatible with this contract module."""
    return contract_major(version) == COMPATIBLE_MAJOR
