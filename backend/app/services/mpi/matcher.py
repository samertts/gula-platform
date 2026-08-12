"""Probabilistic patient matcher — Fellegi-Sunter weighted scoring.

Inputs a candidate Citizen row and a submitted identity profile, returns
a score in [0, 1] plus a per-feature breakdown for audit.

Short-circuit: if nid_hash matches byte-for-byte, score is 1.0 (deterministic).

Otherwise features are summed with these weights:

  phone_last10 exact           +0.30
  birth date exact             +0.25
  birth date day↔month swap    +0.10   (only if not exact)
  name Jaro-Winkler ≥ 0.95     +0.25
  name Jaro-Winkler ≥ 0.85     +0.15   (mutually exclusive with above)
  gender equal                 +0.05
  family_id_hash equal         +0.15

Decision thresholds (applied by resolver.py, not here):
  score ≥ 0.90 → auto-claim to existing citizen
  0.70–0.90    → pending_review claim (no auto-merge)
  < 0.70       → create new citizen

This module contains NO database access and NO side effects — it is a
pure function of its inputs. That makes it unit-testable and safe to call
inside tight loops across hundreds of candidates.
"""

from dataclasses import dataclass, field

from ..identity import jaro_winkler, normalize_name

# ── Weights (keep in sync with docs in architecture/FOUNDATION.md §6) ────────
W_PHONE = 0.30
W_DOB_EXACT = 0.25
W_DOB_SWAP = 0.10
W_NAME_HIGH = 0.25  # JW ≥ 0.95
W_NAME_MID = 0.15  # JW ≥ 0.85
W_GENDER = 0.05
W_FAMILY = 0.15

NAME_JW_HIGH = 0.95
NAME_JW_MID = 0.85

# Decision thresholds (exposed for resolver + tests)
THRESHOLD_AUTO = 0.90
THRESHOLD_REVIEW = 0.70


@dataclass
class IdentityProfile:
    """Submitted identity — the thing we are trying to match.

    Values are already normalized at input time:
      - `name_canonical` is the output of normalize_name()
      - `phone_last10`   is the output of blocking.phone_last10()
      - `nid_hash`       is the output of identity.hash_national_id()
      - `family_id_hash` is the output of identity.hash_family_id()
    """

    name_canonical: str
    phone_last10: str | None = None
    birth_year: int | None = None
    birth_month: int | None = None
    birth_day: int | None = None
    gender: str | None = None
    nid_hash: str | None = None
    family_id_hash: str | None = None


@dataclass
class Candidate:
    """Minimal projection of a Citizen row for matching.

    We carry only the columns the matcher needs — constructed in resolver.py
    from the blocking query result.
    """

    id: int
    citizen_ulid: str
    name_canonical: str
    phone_last10: str | None
    birth_year: int | None
    birth_month: int | None
    birth_day: int | None
    gender: str | None
    nid_hash: str | None
    family_id_hash: str | None


@dataclass
class MatchResult:
    """Scoring output.

    `features` is a dict like {"name_jw": 0.97, "phone": True, ...} — stored
    on IdentityClaim.match_features for audit / debugging.
    """

    score: float
    method: str  # 'nid_exact' | 'probabilistic'
    features: dict = field(default_factory=dict)


def score(profile: IdentityProfile, candidate: Candidate) -> MatchResult:
    """Return the match score + feature breakdown.

    No DB, no I/O, no global state. Safe to call in parallel.
    """
    # ── Deterministic short-circuit: national ID ─────────────────────────────
    if profile.nid_hash and candidate.nid_hash and profile.nid_hash == candidate.nid_hash:
        return MatchResult(
            score=1.0,
            method="nid_exact",
            features={"nid_hash": True},
        )

    features: dict = {}
    total = 0.0

    # ── Phone (last 10 digits) ───────────────────────────────────────────────
    if profile.phone_last10 and candidate.phone_last10:
        phone_eq = profile.phone_last10 == candidate.phone_last10
        features["phone"] = phone_eq
        if phone_eq:
            total += W_PHONE

    # ── Birth date (exact | day↔month swap | miss) ───────────────────────────
    if profile.birth_year and candidate.birth_year and profile.birth_year == candidate.birth_year:
        exact = (
            profile.birth_month == candidate.birth_month
            and profile.birth_day == candidate.birth_day
            and profile.birth_month is not None
        )
        if exact:
            features["dob"] = "exact"
            total += W_DOB_EXACT
        elif (
            profile.birth_month == candidate.birth_day
            and profile.birth_day == candidate.birth_month
            and profile.birth_month is not None
        ):
            features["dob"] = "swap"
            total += W_DOB_SWAP
        else:
            features["dob"] = "year_only"
            # No weight awarded for year-only — too loose.

    # ── Name (Jaro-Winkler on canonical form) ────────────────────────────────
    if profile.name_canonical and candidate.name_canonical:
        jw = jaro_winkler(profile.name_canonical, candidate.name_canonical)
        features["name_jw"] = round(jw, 4)
        if jw >= NAME_JW_HIGH:
            total += W_NAME_HIGH
        elif jw >= NAME_JW_MID:
            total += W_NAME_MID

    # ── Gender ───────────────────────────────────────────────────────────────
    if profile.gender and candidate.gender:
        g_eq = profile.gender.upper() == candidate.gender.upper()
        features["gender"] = g_eq
        if g_eq:
            total += W_GENDER

    # ── Family ID ────────────────────────────────────────────────────────────
    if profile.family_id_hash and candidate.family_id_hash:
        fam_eq = profile.family_id_hash == candidate.family_id_hash
        features["family"] = fam_eq
        if fam_eq:
            total += W_FAMILY

    # Clamp to [0, 1]
    return MatchResult(
        score=min(total, 1.0),
        method="probabilistic",
        features=features,
    )


def classify(score_value: float) -> str:
    """Map a probabilistic score to a decision category.

    Returns 'auto_match' | 'review' | 'no_match'.
    """
    if score_value >= THRESHOLD_AUTO:
        return "auto_match"
    if score_value >= THRESHOLD_REVIEW:
        return "review"
    return "no_match"


def build_profile(
    *,
    name: str,
    phone_last10: str | None = None,
    birth_year: int | None = None,
    birth_month: int | None = None,
    birth_day: int | None = None,
    gender: str | None = None,
    nid_hash: str | None = None,
    family_id_hash: str | None = None,
) -> IdentityProfile:
    """Convenience constructor that normalizes the name.

    The rest of the fields are expected to be already normalized by the
    caller (resolver.py does the normalization before blocking).
    """
    return IdentityProfile(
        name_canonical=normalize_name(name),
        phone_last10=phone_last10,
        birth_year=birth_year,
        birth_month=birth_month,
        birth_day=birth_day,
        gender=gender,
        nid_hash=nid_hash,
        family_id_hash=family_id_hash,
    )
