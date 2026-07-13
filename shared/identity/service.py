from __future__ import annotations

import hashlib
import hmac
import logging
import re
from datetime import date
from typing import Any, Optional

from .domain import (
    Gender,
    IdentityDocument,
    IdentityDocumentType,
    IdentityStatus,
    PatientIdentity,
    PersonName,
)

logger = logging.getLogger("gula.identity")


# Arabic character normalization
_ARABIC_NORMALIZE = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي",
}

_ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]")


def normalize_arabic_name(name: str | None) -> str:
    if not name:
        return ""
    name = _ARABIC_DIACRITICS.sub("", name)
    for src, dst in _ARABIC_NORMALIZE.items():
        name = name.replace(src, dst)
    return re.sub(r"\s+", " ", name).strip()


def normalize_phone(phone: str | None) -> str:
    if not phone:
        return ""
    phone = re.sub(r"[\s\-\(\)]", "", phone)
    if phone.startswith("+964"):
        return phone
    if phone.startswith("00964"):
        return "+964" + phone[5:]
    if phone.startswith("0"):
        return "+964" + phone[1:]
    return phone


def generate_health_id(national_id: str, secret: str = "") -> str:
    raw = (national_id + secret).encode()
    h = hashlib.sha256(raw).hexdigest()[:16].upper()
    return f"HID-{h[:8]}-{h[8:16]}"


def hash_national_id(nid: str, hmac_key: str) -> str:
    if not nid or not hmac_key:
        return ""
    return hmac.new(
        hmac_key.encode(), nid.encode(), hashlib.sha256
    ).hexdigest()


def calculate_match_score(a: PatientIdentity, b: PatientIdentity) -> float:
    score = 0.0
    weights = {"nid": 0.4, "phone": 0.25, "name": 0.2, "dob": 0.15}

    if a.national_id_hash and a.national_id_hash == b.national_id_hash:
        score += weights["nid"]
        logger.debug("NID match: +%.2f", weights["nid"])

    phone_a = normalize_phone(a.phone)
    phone_b = normalize_phone(b.phone)
    if phone_a and phone_b and phone_a == phone_b:
        score += weights["phone"]
        logger.debug("Phone match: +%.2f", weights["phone"])

    name_a = normalize_arabic_name(a.name.name_ar or a.name.full)
    name_b = normalize_arabic_name(b.name.name_ar or b.name.full)
    if name_a and name_b:
        from difflib import SequenceMatcher
        ratio = SequenceMatcher(None, name_a, name_b).ratio()
        score += weights["name"] * ratio
        if ratio > 0.9:
            logger.debug("Name match (ratio=%.3f): +%.2f", ratio, weights["name"] * ratio)

    if a.date_of_birth and b.date_of_birth and a.date_of_birth == b.date_of_birth:
        score += weights["dob"]
        logger.debug("DOB match: +%.2f", weights["dob"])

    return min(score, 1.0)


PATIENT_NAME_ALIASES: dict[str, list[str]] = {
    "mohammed": ["mohammad", "mohamed", "muhammed", "muhamad", "mohamad"],
    "ahmed": ["ahmad", "ahmet"],
    "hussein": ["husain", "husein", "hussain", "hossein"],
    "hassan": ["hasan", "hasen"],
    "abdullah": ["abdallah", "abd allah", "abdulla"],
    "omar": ["umar", "omer"],
    "othman": ["osman", "uthman"],
    "khalid": ["khaled"],
    "karim": ["kareem"],
    "youssef": ["yousef", "yusuf", "yosef"],
    "mustafa": ["mostafa", "mustpha"],
    "ibrahim": ["ibraheem", "abraham"],
    "ismail": ["ismael", "esmail"],
}


def normalize_name_token(name: str) -> str:
    name = normalize_arabic_name(name)
    return re.sub(r"[^a-zA-Z\u0600-\u06FF\s]", "", name).strip()


def get_name_variants(name: str) -> set[str]:
    normalized = normalize_name_token(name)
    tokens = normalized.lower().split()
    variants = {normalized.lower()}
    for i, token in enumerate(tokens):
        if token in PATIENT_NAME_ALIASES:
            for alias in PATIENT_NAME_ALIASES[token]:
                variant = tokens.copy()
                variant[i] = alias
                variants.add(" ".join(variant))
    return variants


class IdentityService:
    def __init__(self, nid_hmac_key: str = ""):
        self._nid_hmac_key = nid_hmac_key

    def normalize_patient(self, patient: PatientIdentity) -> PatientIdentity:
        if patient.phone:
            patient.phone = normalize_phone(patient.phone)
        if patient.national_id_hash and self._nid_hmac_key:
            patient.national_id_hash = hash_national_id(
                patient.national_id_hash, self._nid_hmac_key
            )
        patient.updated_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )
        return patient

    def score_match(self, a: PatientIdentity, b: PatientIdentity) -> float:
        return calculate_match_score(a, b)

    def find_duplicate_candidates(
        self, patient: PatientIdentity, existing: list[PatientIdentity]
    ) -> list[tuple[PatientIdentity, float]]:
        scored = [(p, self.score_match(patient, p)) for p in existing]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(p, s) for p, s in scored if s >= 0.6]
