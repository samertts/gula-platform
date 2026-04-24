"""Clinical-indication → additional-test suggestions.

Small, hand-curated map that augments a physician's test order when the
clinical indication matches a known pattern. The rules here are deliberately
conservative: they only add tests that are standard-of-care follow-ons for
the indication (e.g. HbA1c + lipid panel when diabetes is suspected).

Rules fire on substring match against the Arabic *or* English keywords. Codes
already present in the physician's order are never re-added.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SuggestionRule:
    keywords: tuple[str, ...]
    add: tuple[str, ...]
    rationale: str


# Keep this table small and clinically defensible. Extend only with sign-off.
_RULES: tuple[SuggestionRule, ...] = (
    SuggestionRule(
        keywords=("سكري", "سكر", "diabetes", "hyperglycemia", "dm"),
        add=("HBA1C", "GLU", "CR", "LDL", "HDL", "TG"),
        rationale="diabetes_workup",
    ),
    SuggestionRule(
        keywords=("ضغط", "hypertension", "htn", "blood pressure"),
        add=("NA", "K", "CR", "BUN"),
        rationale="hypertension_workup",
    ),
    SuggestionRule(
        keywords=("فقر دم", "أنيميا", "anemia", "anaemia"),
        add=("HGB", "HCT", "RBC", "PLT"),
        rationale="anemia_workup",
    ),
    SuggestionRule(
        keywords=("كبد", "liver", "hepatitis", "jaundice", "يرقان"),
        add=("ALT", "AST"),
        rationale="liver_panel",
    ),
    SuggestionRule(
        keywords=("كلى", "kidney", "renal", "إختلال كلوي"),
        add=("CR", "BUN", "NA", "K"),
        rationale="renal_panel",
    ),
    SuggestionRule(
        keywords=("غدة درقية", "غدة", "thyroid", "hypothyroid", "hyperthyroid"),
        add=("TSH",),
        rationale="thyroid_workup",
    ),
    SuggestionRule(
        keywords=("دهون", "كوليسترول", "cholesterol", "lipid", "dyslipidemia"),
        add=("CHOL", "LDL", "HDL", "TG"),
        rationale="lipid_panel",
    ),
    SuggestionRule(
        keywords=("التهاب", "infection", "fever", "حمى"),
        add=("WBC", "CRP"),
        rationale="infection_workup",
    ),
    SuggestionRule(
        keywords=("تخثر", "نزيف", "coagulation", "bleeding", "anticoagulant"),
        add=("INR", "PLT"),
        rationale="coagulation_panel",
    ),
)


def suggest_additional_tests(
    clinical_indication: str,
    already_ordered: list[str],
) -> tuple[list[str], list[str]]:
    """Return ``(additions, rationales)`` for the given indication.

    ``additions`` preserves discovery order (first-match-first-added), and
    never contains codes already in ``already_ordered``. ``rationales`` lists
    each rule that fired, for audit visibility.
    """
    text = (clinical_indication or "").strip().lower()
    if not text:
        return [], []

    have = {(c or "").strip().upper() for c in already_ordered}
    additions: list[str] = []
    seen: set[str] = set()
    rationales: list[str] = []

    for rule in _RULES:
        if not any(kw.lower() in text for kw in rule.keywords):
            continue
        rationales.append(rule.rationale)
        for code in rule.add:
            if code not in have and code not in seen:
                seen.add(code)
                additions.append(code)

    return additions, rationales
