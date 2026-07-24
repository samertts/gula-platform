"""Blocking-key generator for MPI candidate search.

Rationale: at 48 M rows we cannot do O(N) probabilistic scoring on every
match. Blocking partitions the citizen table into buckets where any two
rows in different buckets are guaranteed to be non-matches, so we only
score within a bucket.

Key strategy:
  surname[:4] + given[0]

Examples:
  "محمد علي حسين"  → normalize → "muhamad ali hussein" → "husa m"  (whitespace dropped)
  "Mohammed Ali Hussein" → same canonical → same blocking key
  "Ahmad Hassan Jaber"   → "jabe a"

Complement: the blocking index in models.py is composite
(name_blocking_key, birth_year, gender) so candidates are pre-filtered
by three signals at once.

"""

import re

from ..identity import normalize_name

_BLOCKING_KEY_LEN = 5  # 4 chars of surname + 1 char of given


def blocking_key(full_name: str) -> str:
    """Compute the blocking key for a canonical name.

    Rules:
      - Name is normalized via identity.normalize_name() (Arabic folding,
        English alias map, lowercasing).
      - Surname is the LAST whitespace-separated token.
      - Given is the FIRST token.
      - We take surname[:4] + given[0], stripped of non-alphabetic chars.
      - If the name has only one token, the blocking key is token[:4] + token[0].
      - If the resulting key is < 2 chars, we pad with '_' (so empty names
        don't collide with single-letter keys).

    Returns a short, lowercase, ASCII-ish string suitable for indexing.
    """
    if not full_name or not full_name.strip():
        return "_____"

    canonical = normalize_name(full_name)
    # Keep only alphabetic characters in each token (drop digits, punctuation)
    tokens = [re.sub(r"[^a-z\u0600-\u06ff]", "", t) for t in canonical.split()]
    tokens = [t for t in tokens if t]

    if not tokens:
        return "_____"

    if len(tokens) == 1:
        t = tokens[0]
        key = (t[:4] + t[:1]).ljust(_BLOCKING_KEY_LEN, "_")
    else:
        given = tokens[0]
        surname = tokens[-1]
        key = (surname[:4] + given[:1]).ljust(_BLOCKING_KEY_LEN, "_")

    return key[:_BLOCKING_KEY_LEN]


def phone_last10(phone: str | None) -> str | None:
    """Extract the last 10 digits of a phone number (E.164 suffix).

    Returns None for empty input or fewer than 10 digits.
    """
    if not phone:
        return None
    digits = re.sub(r"[^\d]", "", phone)
    if len(digits) < 10:
        return None
    return digits[-10:]
