"""خدمة مطابقة الهويات - Identity Matching Service.

Iraqi-context identity reconciliation:

- ``generate_health_id``      : deterministic HID-XXXXXXXX-YY derived from the national ID
- ``normalize_arabic_name``   : canonicalize Arabic/Iraqi names for comparison
- ``calculate_match_score``   : weighted similarity between two citizen records
- ``find_duplicates``         : exact-on-NID then probabilistic name+DOB search

The scoring is deterministic and pure (no DB access in the scoring path) so it
can be unit-tested and benchmarked outside of a request cycle.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import unicodedata
from datetime import date, datetime
from typing import Any

try:  # Optional — only needed by ``find_duplicates``.
    from sqlalchemy.orm import Session
except Exception:  # pragma: no cover - SQLAlchemy is always present in runtime
    Session = Any  # type: ignore[assignment,misc]


# ─────────────────────────── Arabic normalization ────────────────────────────

# Hamza / alef variants → plain alef, ta-marbuta → ha, alef-maksura → ya, etc.
_ARABIC_LETTER_MAP = {
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    "ة": "ه",
    "ى": "ي",
    "ؤ": "و",
    "ئ": "ي",
    "ـ": "",  # tatweel (kashida)
}

# Arabic tashkeel (diacritics) range + tatweel, removed entirely.
_ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC"
    r"\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]",
)

_MULTI_WHITESPACE = re.compile(r"\s+")


def normalize_arabic_name(name: str | None) -> str:
    """Canonicalize an Arabic or Latin name for matching.

    Steps:
      1. Strip tashkeel (diacritics).
      2. Unify Arabic letter variants (ى→ي، ة→ه، أإآ→ا، ؤ→و، ئ→ي).
      3. Collapse whitespace.
      4. Lowercase (for any Latin characters).

    Returns an empty string for ``None`` or blank input.
    """
    if not name:
        return ""

    # Unicode NFC normalization so composed/decomposed forms compare equal.
    text = unicodedata.normalize("NFC", str(name))
    text = _ARABIC_DIACRITICS.sub("", text)

    for src, dst in _ARABIC_LETTER_MAP.items():
        text = text.replace(src, dst)

    text = _MULTI_WHITESPACE.sub(" ", text).strip()
    return text.lower()


# ─────────────────────────── Health ID generation ────────────────────────────

_HID_PREFIX = "HID-"
_HID_HASH_LEN = 8  # hex chars of the body
_HID_CHECKSUM_LEN = 2  # chars of the checksum
# Base-32 alphabet (Crockford-like) — no 0/1/O/I to avoid transcription errors.
_BASE32_ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _clean_national_id(national_id: str) -> str:
    cleaned = re.sub(r"\D", "", str(national_id or ""))
    if not cleaned:
        raise ValueError("national_id must contain at least one digit")
    return cleaned


def _hid_checksum(body: str) -> str:
    """Two-character checksum over the HID body (base-32, avoids ambiguous chars).

    Uses SHA-256 so the checksum is deterministic but non-trivial to forge
    without the original body.
    """
    digest = hashlib.sha256(body.encode("utf-8")).digest()
    n = (digest[0] << 8) | digest[1]
    return _BASE32_ALPHA[(n >> 5) & 0x1F] + _BASE32_ALPHA[n & 0x1F]


def generate_health_id(national_id: str) -> str:
    """Derive a stable, unique health ID from an Iraqi national ID.

    Format: ``HID-<8-hex>-<2-char checksum>``  →  e.g. ``HID-A3F8B2C1-K7``.

    The body is the first 8 hex chars of an HMAC-SHA256 over the cleaned
    national ID (digits only). We prefer HMAC over raw SHA-256 because it
    keyed via ``NID_HMAC_KEY`` so the HID cannot be reversed by brute-forcing
    a 10-digit national ID with a public hash function. The checksum guards
    against single-character transcription errors.
    """
    cleaned = _clean_national_id(national_id)

    # Keyed hash: derive via HMAC-SHA256 with the app's NID key when available,
    # otherwise fall back to plain SHA-256 so the function remains usable from
    # scripts and unit tests without app config loaded.
    try:
        from ..config import NID_HMAC_KEY  # type: ignore

        digest = hmac.new(
            NID_HMAC_KEY.encode("utf-8"), cleaned.encode("utf-8"), hashlib.sha256,
        ).hexdigest()
    except Exception:
        digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

    body = digest[:_HID_HASH_LEN].upper()
    return f"{_HID_PREFIX}{body}-{_hid_checksum(body)}"


def verify_health_id(hid: str) -> bool:
    """Validate the structure + checksum of a previously issued HID."""
    if not hid or not hid.startswith(_HID_PREFIX):
        return False
    parts = hid[len(_HID_PREFIX) :].split("-")
    if len(parts) != 2:
        return False
    body, checksum = parts
    if len(body) != _HID_HASH_LEN or len(checksum) != _HID_CHECKSUM_LEN:
        return False
    if not re.fullmatch(r"[0-9A-F]{8}", body):
        return False
    return _hid_checksum(body) == checksum


# ─────────────────────────────── Match scoring ───────────────────────────────

# Feature weights (must sum to 1.0).
W_NAME = 0.40
W_DOB = 0.30
W_MOTHER = 0.20
W_GOVERNORATE = 0.10

MATCH_THRESHOLD = 0.85  # ≥ 0.85 → treated as the same person


def _get(obj: Any, key: str) -> Any:
    """Read ``key`` from a dict or an object (SQLAlchemy model / dataclass)."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _as_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(value), fmt).date()
        except ValueError:
            continue
    return None


def _name_similarity(n1: str, n2: str) -> float:
    """Token-level similarity on normalized names.

    Uses Jaccard over tokens plus a Jaro-Winkler fallback on the concatenated
    string so reorderings ("علي محمد حسن" vs "محمد علي حسن") still score high
    while typos degrade gracefully.
    """
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0

    t1, t2 = set(n1.split()), set(n2.split())
    jaccard = len(t1 & t2) / len(t1 | t2) if (t1 or t2) else 0.0

    try:
        from .identity import jaro_winkler

        jw = jaro_winkler(n1, n2)
    except Exception:
        jw = 0.0

    return max(jaccard, jw)


def _dob_score(d1: Any, d2: Any) -> float:
    a, b = _as_date(d1), _as_date(d2)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    # Transposed day/month is a common data-entry error in Iraqi civil records.
    if a.year == b.year and a.day == b.month and a.month == b.day:
        return 0.5
    if a.year == b.year and a.month == b.month:
        return 0.2
    return 0.0


def _equal_score(v1: Any, v2: Any, *, normalize: bool = False) -> float:
    if not v1 or not v2:
        return 0.0
    if normalize:
        return 1.0 if normalize_arabic_name(v1) == normalize_arabic_name(v2) else 0.0
    return 1.0 if str(v1).strip().lower() == str(v2).strip().lower() else 0.0


def calculate_match_score(citizen1: Any, citizen2: Any) -> float:
    """Weighted similarity between two citizen records in [0.0, 1.0].

    Fields read (dict keys or attributes): ``full_name``, ``birth_date``,
    ``mother_name``, ``governorate``. Missing fields contribute 0 to their
    component — they do not reduce the weight of other components, so a
    partial record can still reach ``MATCH_THRESHOLD`` on strong signals.
    """
    n1 = normalize_arabic_name(_get(citizen1, "full_name") or _get(citizen1, "name"))
    n2 = normalize_arabic_name(_get(citizen2, "full_name") or _get(citizen2, "name"))
    name = _name_similarity(n1, n2)

    dob = _dob_score(_get(citizen1, "birth_date"), _get(citizen2, "birth_date"))
    mother = _equal_score(
        _get(citizen1, "mother_name"), _get(citizen2, "mother_name"), normalize=True,
    )
    gov = _equal_score(_get(citizen1, "governorate"), _get(citizen2, "governorate"), normalize=True)

    score = W_NAME * name + W_DOB * dob + W_MOTHER * mother + W_GOVERNORATE * gov
    return round(min(max(score, 0.0), 1.0), 4)


# ─────────────────────────── Duplicate discovery ─────────────────────────────


def find_duplicates(db: Session, citizen_data: Any, *, limit: int = 20) -> list[tuple[Any, float]]:
    """Return (citizen, match_score) pairs ranked by descending score.

    Resolution order:
      1. Exact match on hashed national ID → score 1.0 and short-circuits.
      2. Probabilistic search on normalized name + birth year, filtered
         through ``calculate_match_score``; only pairs ≥ ``MATCH_THRESHOLD``
         are returned.

    The caller is responsible for scoping by ``lab_id`` if multi-tenant
    isolation is required — this function intentionally leaves tenancy to
    the caller to keep the matcher reusable across contexts (citizen
    directory vs. lab-local patient book).
    """
    from ..models.patient import Patient  # local import avoids circular deps

    full_name = _get(citizen_data, "full_name") or _get(citizen_data, "name")
    birth_date = _as_date(_get(citizen_data, "birth_date"))
    national_id = _get(citizen_data, "national_id")
    lab_id = _get(citizen_data, "lab_id")

    base_query = db.query(Patient)
    if lab_id is not None:
        base_query = base_query.filter(Patient.lab_id == lab_id)

    # 1. Exact match on hashed national ID.
    if national_id:
        try:
            from .identity import hash_national_id

            nid_hash = hash_national_id(str(national_id))
        except Exception:
            nid_hash = None
        if nid_hash:
            exact = base_query.filter(Patient.national_id_hash == nid_hash).all()
            if exact:
                return [(p, 1.0) for p in exact]

    # 2. Probabilistic name + birth-year prefilter.
    if not full_name:
        return []

    normalized = normalize_arabic_name(full_name)
    first_token = normalized.split()[0] if normalized else ""

    candidates_q = base_query
    if first_token:
        candidates_q = candidates_q.filter(Patient.full_name.ilike(f"%{first_token}%"))
    if birth_date:
        try:
            from sqlalchemy import extract

            candidates_q = candidates_q.filter(
                extract("year", Patient.birth_date) == birth_date.year,
            )
        except Exception:
            pass

    results: list[tuple[Any, float]] = []
    for candidate in candidates_q.limit(200).all():
        score = calculate_match_score(citizen_data, candidate)
        if score >= MATCH_THRESHOLD:
            results.append((candidate, score))

    results.sort(key=lambda pair: pair[1], reverse=True)
    return results[:limit]


__all__ = [
    "MATCH_THRESHOLD",
    "calculate_match_score",
    "find_duplicates",
    "generate_health_id",
    "normalize_arabic_name",
    "verify_health_id",
]
