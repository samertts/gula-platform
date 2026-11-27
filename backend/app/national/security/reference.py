from __future__ import annotations

import hashlib


def pseudonymous_reference(value: str | None) -> str | None:
    """Return a short, non-reversible reference suitable for audit metadata."""
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
