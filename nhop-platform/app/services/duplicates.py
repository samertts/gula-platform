"""Citizen duplicate detection.

Scores candidate citizens already in the registry against a prospective new
registration. A score ≥ ``DUPLICATE_CONFLICT_THRESHOLD`` is treated as a
likely duplicate by the API and returned as a 409 conflict.

Scoring weights (sum ≤ 1.0):
    full_name Jaro-Winkler ≥ 0.95        0.45
    full_name Jaro-Winkler ≥ 0.85        0.25  (mutually exclusive)
    birth_date exact                     0.25
    phone exact (last 10 digits match)   0.20
    mother_name Jaro-Winkler ≥ 0.90      0.10

The function is pure (no writes, no external I/O) — it only runs a blocking
query on the citizens table to narrow candidates before scoring.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models.citizen import Citizen


DUPLICATE_CONFLICT_THRESHOLD = 0.85
_MAX_CANDIDATES = 200

W_NAME_HIGH = 0.45
W_NAME_MID  = 0.25
W_DOB       = 0.25
W_PHONE     = 0.20
W_MOTHER    = 0.10

NAME_JW_HIGH = 0.95
NAME_JW_MID  = 0.85
MOTHER_JW    = 0.90


@dataclass
class DuplicateHit:
    health_id: str
    full_name: str
    score: float
    reasons: list[str]


# ─── Name normalization (Arabic-aware) ──────────────────────────────────────

_ARABIC_DIACRITICS = re.compile(r"[\u064B-\u0652\u0670]")


def _normalize_name(name: str) -> str:
    s = name.strip().lower()
    s = _ARABIC_DIACRITICS.sub("", s)
    # Collapse alef variants and taa-marbuta / haa for Arabic, plus whitespace
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = s.replace("ى", "ي").replace("ة", "ه")
    s = re.sub(r"\s+", " ", s)
    return s


def _phone_last10(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    return digits[-10:] if len(digits) >= 10 else None


# ─── Jaro-Winkler (self-contained; no external dependency) ──────────────────

def _jaro(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    match_distance = max(len(s1), len(s2)) // 2 - 1
    if match_distance < 0:
        match_distance = 0
    s1_matches = [False] * len(s1)
    s2_matches = [False] * len(s2)
    matches = 0
    transpositions = 0
    for i, c in enumerate(s1):
        start = max(0, i - match_distance)
        end   = min(i + match_distance + 1, len(s2))
        for j in range(start, end):
            if s2_matches[j] or s2[j] != c:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break
    if matches == 0:
        return 0.0
    k = 0
    for i in range(len(s1)):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1
    transpositions //= 2
    return (matches / len(s1) + matches / len(s2)
            + (matches - transpositions) / matches) / 3.0


def _jaro_winkler(s1: str, s2: str, p: float = 0.1) -> float:
    j = _jaro(s1, s2)
    prefix = 0
    for a, b in zip(s1, s2):
        if a == b and prefix < 4:
            prefix += 1
        else:
            break
    return j + prefix * p * (1 - j)


# ─── Public API ─────────────────────────────────────────────────────────────

def find_duplicates(
    db: Session,
    *,
    full_name: str,
    birth_date: Optional[date] = None,
    phone: Optional[str] = None,
    mother_name: Optional[str] = None,
    national_id: Optional[str] = None,
    exclude_health_id: Optional[str] = None,
) -> list[DuplicateHit]:
    """Return candidates that likely refer to the same person, score-descending.

    Only rows scoring > 0 are returned. The caller decides whether to treat any
    of them as a hard conflict (see ``DUPLICATE_CONFLICT_THRESHOLD``).
    """
    target_name    = _normalize_name(full_name)
    target_phone10 = _phone_last10(phone)
    target_mother  = _normalize_name(mother_name) if mother_name else None

    # Blocking: cheap filter before expensive scoring.
    q = db.query(Citizen)
    blocks = []
    if national_id:
        blocks.append(Citizen.national_id == national_id)
    if target_phone10:
        blocks.append(Citizen.phone.like(f"%{target_phone10}"))
    if birth_date is not None:
        blocks.append(Citizen.birth_date == birth_date)
    # Always include a loose name prefix block so name-only matches still appear.
    name_prefix = target_name.split(" ", 1)[0][:4]
    if name_prefix:
        blocks.append(Citizen.full_name.ilike(f"%{name_prefix}%"))
    if blocks:
        q = q.filter(or_(*blocks))
    if exclude_health_id:
        q = q.filter(Citizen.health_id != exclude_health_id)

    candidates = q.limit(_MAX_CANDIDATES).all()

    hits: list[DuplicateHit] = []
    for c in candidates:
        score = 0.0
        reasons: list[str] = []

        # Name
        cand_name = _normalize_name(c.full_name or "")
        name_jw = _jaro_winkler(target_name, cand_name) if cand_name else 0.0
        if name_jw >= NAME_JW_HIGH:
            score += W_NAME_HIGH
            reasons.append(f"name_jw={name_jw:.3f}")
        elif name_jw >= NAME_JW_MID:
            score += W_NAME_MID
            reasons.append(f"name_jw={name_jw:.3f}")

        # Birth date
        if birth_date is not None and c.birth_date is not None and c.birth_date == birth_date:
            score += W_DOB
            reasons.append("birth_date_exact")

        # Phone (last 10 digits)
        cand_phone10 = _phone_last10(c.phone)
        if target_phone10 and cand_phone10 and target_phone10 == cand_phone10:
            score += W_PHONE
            reasons.append("phone_match")

        # Mother name
        if target_mother and c.mother_name:
            mother_jw = _jaro_winkler(target_mother, _normalize_name(c.mother_name))
            if mother_jw >= MOTHER_JW:
                score += W_MOTHER
                reasons.append(f"mother_jw={mother_jw:.3f}")

        if score > 0:
            hits.append(DuplicateHit(
                health_id=c.health_id,
                full_name=c.full_name,
                score=min(round(score, 4), 1.0),
                reasons=reasons,
            ))

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits
