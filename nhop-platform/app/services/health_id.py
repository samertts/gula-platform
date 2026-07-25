"""Health ID generator.

Format: ``HID-YYYY-NNNNNNNN`` where NNNNNNNN is an 8-character cryptographically
random base32 suffix (Crockford alphabet, minus I/L/O/U). That gives ~40 bits
of entropy — sufficient that a uniqueness check plus one retry is effectively
never expected to collide at national scale.
"""
import secrets
from datetime import datetime

from sqlalchemy.orm import Session

from datetime import UTC

from ..models.citizen import Citizen

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"   # Crockford base32
_SUFFIX_LEN = 8
_MAX_ATTEMPTS = 5


def _random_suffix() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(_SUFFIX_LEN))


def generate_health_id(db: Session) -> str:
    """Return a unique ``HID-YYYY-XXXXXXXX`` identifier.

    Retries up to _MAX_ATTEMPTS times if the generated value collides with an
    existing row. At ~1.1e12 possibilities per year, collisions are effectively
    impossible in practice.
    """
    year = datetime.now(UTC).year
    for _ in range(_MAX_ATTEMPTS):
        hid = f"HID-{year}-{_random_suffix()}"
        exists = db.query(Citizen.id).filter(Citizen.health_id == hid).first()
        if exists is None:
            return hid
    raise RuntimeError("failed to generate unique health_id after retries")
