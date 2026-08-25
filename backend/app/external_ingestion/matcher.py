"""Privacy-preserving professional entity resolution.

The matcher never persists raw PII. Automatic linking is allowed only for a
stable, source-independent hard anchor (national ID or license + authority +
profession). Name/phone/date combinations remain pending review to avoid a
false clinical identity merge.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass

from app.services.identity import normalize_name

_PROFESSIONS = frozenset({
    "doctor",
    "pharmacist",
    "laboratory_scientist",
    "dentist",
    "nurse",
})


@dataclass(frozen=True)
class ProfessionalFingerprints:
    person_ref_hmac: str
    national_id_hmac: str | None
    license_hmac: str | None
    license_authority: str | None
    profession: str
    specialty_hmac: str | None
    name_hmac: str
    name_tokens_hmac: tuple[str, ...]
    phone_hmac: str | None
    birth_date_hmac: str | None
    employer_ref_hmac: str | None
    employment_status: str | None


@dataclass(frozen=True)
class CandidateFingerprint:
    entity_id: int
    national_id_hmac: str | None
    license_hmac: str | None
    license_authority: str | None
    profession: str
    name_hmac: str
    phone_hmac: str | None
    birth_date_hmac: str | None


@dataclass(frozen=True)
class MatchResult:
    status: str  # auto_matched | pending_review | no_match | conflict
    method: str
    score: int
    candidate_entity_id: int | None
    features: dict[str, bool | str]


def _clean(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def _normalise_phone(value: str | None) -> str:
    digits = re.sub(r"\D", "", value or "")
    return digits[-10:] if len(digits) >= 10 else digits


def _normalise_date(value: str | None) -> str | None:
    cleaned = _clean(value)
    if not cleaned:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cleaned):
        return None
    return cleaned


def _fingerprint(value: str, *, key: str, domain: str) -> str:
    normalized = _clean(value).casefold()
    return hmac.new(key.encode("utf-8"), f"{domain}:{normalized}".encode(), hashlib.sha256).hexdigest()


def build_fingerprints(record, *, hmac_key: str) -> ProfessionalFingerprints:
    """Build non-reversible matching features from a validated input record."""
    profession = _clean(record.profession).casefold()
    if profession not in _PROFESSIONS:
        raise ValueError("unsupported profession")

    normalized_name = normalize_name(record.full_name)
    if not normalized_name:
        raise ValueError("full_name must not be blank")
    name_tokens = tuple(sorted(set(normalized_name.split())))
    name_hmac = _fingerprint(normalized_name, key=hmac_key, domain="professional-name")
    name_token_hmacs = tuple(
        _fingerprint(token, key=hmac_key, domain="professional-name-token")
        for token in name_tokens
    )

    national_id = _clean(record.national_id)
    national_id_hmac = _fingerprint(national_id, key=hmac_key, domain="national-id") if national_id else None
    authority = _clean(record.license_authority).casefold() or None
    license_number = _clean(record.license_number)
    license_hmac = None
    if license_number and authority:
        license_hmac = _fingerprint(
            f"{authority}|{profession}|{license_number}",
            key=hmac_key,
            domain="professional-license",
        )

    phone = _normalise_phone(record.phone)
    phone_hmac = _fingerprint(phone, key=hmac_key, domain="professional-phone") if phone else None
    birth_date = _normalise_date(record.birth_date)
    specialty = _clean(record.specialty) or None
    specialty_hmac = _fingerprint(specialty, key=hmac_key, domain="professional-specialty") if specialty else None
    employer = _clean(record.employer_reference)
    employer_hmac = _fingerprint(employer, key=hmac_key, domain="employer-ref") if employer else None

    if national_id_hmac:
        person_ref_hmac = national_id_hmac
    elif license_hmac:
        person_ref_hmac = license_hmac
    else:
        # This is intentionally not sufficient for auto-approval. It is useful
        # only as a stable review key for exact repeats of weak-source records.
        person_ref_hmac = _fingerprint(
            "|".join((normalized_name, birth_date or "", phone)),
            key=hmac_key,
            domain="professional-review-ref",
        )

    return ProfessionalFingerprints(
        person_ref_hmac=person_ref_hmac,
        national_id_hmac=national_id_hmac,
        license_hmac=license_hmac,
        license_authority=authority,
        profession=profession,
        specialty_hmac=specialty_hmac,
        name_hmac=name_hmac,
        name_tokens_hmac=name_token_hmacs,
        phone_hmac=phone_hmac,
        birth_date_hmac=_fingerprint(birth_date, key=hmac_key, domain="professional-birth-date") if birth_date else None,
        employer_ref_hmac=employer_hmac,
        employment_status=_clean(record.employment_status) or None,
    )


def resolve_candidate(
    incoming: ProfessionalFingerprints,
    candidates: list[CandidateFingerprint],
) -> MatchResult:
    """Resolve conservatively; ambiguous or weak matches never auto-link."""
    same_profession = [c for c in candidates if c.profession == incoming.profession]
    if not same_profession:
        return MatchResult("no_match", "no_candidate", 0, None, {})

    if incoming.national_id_hmac:
        exact = [c for c in same_profession if c.national_id_hmac == incoming.national_id_hmac]
        if len(exact) == 1:
            candidate = exact[0]
            if incoming.license_hmac and candidate.license_hmac and incoming.license_hmac != candidate.license_hmac:
                return MatchResult(
                    "conflict", "national_id_license_disagreement", 100, None,
                    {"national_id_exact": True, "license_disagreement": True},
                )
            return MatchResult(
                "auto_matched", "national_id_exact", 100, candidate.entity_id,
                {"national_id_exact": True},
            )
        if len(exact) > 1:
            return MatchResult("conflict", "national_id_multiple_entities", 100, None, {"national_id_exact": True})

    if incoming.license_hmac and incoming.license_authority:
        exact = [
            c for c in same_profession
            if c.license_hmac == incoming.license_hmac
            and c.license_authority == incoming.license_authority
        ]
        if len(exact) == 1:
            candidate = exact[0]
            if incoming.national_id_hmac and candidate.national_id_hmac and incoming.national_id_hmac != candidate.national_id_hmac:
                return MatchResult(
                    "conflict", "license_national_id_disagreement", 99, None,
                    {"license_exact": True, "authority_exact": True, "national_id_disagreement": True},
                )
            return MatchResult(
                "auto_matched", "license_authority_exact", 99, candidate.entity_id,
                {"license_exact": True, "authority_exact": True},
            )
        if len(exact) > 1:
            return MatchResult("conflict", "license_multiple_entities", 99, None, {"license_exact": True})

    weak_exact = [
        c for c in same_profession
        if c.name_hmac == incoming.name_hmac
        and incoming.phone_hmac is not None
        and c.phone_hmac == incoming.phone_hmac
        and incoming.birth_date_hmac is not None
        and c.birth_date_hmac == incoming.birth_date_hmac
    ]
    if len(weak_exact) == 1:
        return MatchResult(
            "pending_review", "name_phone_birth_exact", 92, weak_exact[0].entity_id,
            {"name_exact": True, "phone_exact": True, "birth_date_exact": True},
        )
    if len(weak_exact) > 1:
        return MatchResult("conflict", "weak_multiple_entities", 92, None, {"weak_signals": True})

    if same_profession:
        return MatchResult(
            "pending_review", "no_safe_hard_anchor", 0, None,
            {"candidate_set_nonempty": True},
        )
    return MatchResult("no_match", "no_candidate", 0, None, {})
