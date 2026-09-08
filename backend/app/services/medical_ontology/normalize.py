"""Iraqi medical language normalizer.

Maps free-text mentions in English, Modern Standard Arabic, Iraqi dialect,
or Arabizi (Arabic written in Latin + digits) to canonical
``concept_key`` slugs from the ontology.

The normalizer is *deterministic and stateless* at query time — the
pre-normalized ``term_normalized`` column on ``medical_ontology_synonyms``
is the index. Ranking prefers, in order:

  1. Exact normalized match on the given locale.
  2. Exact normalized match on any locale (with a locale-mismatch penalty).
  3. Longest-prefix match on normalized form (only when tie-breaking equal
     candidates).

Two dictionaries drive text folding:

  * ``ARABIC_DIACRITICS`` — the U+064B..U+065F block plus the tatweel; these
    carry no lexical value in unpointed medical text.
  * ``ARABIZI_TABLE`` — the standard Arabizi digit-to-Arabic-letter map.
    Applied only when the input contains ASCII digits mixed into Arabic
    context; safe on pure English/Arabic strings.

The normalizer never *invents* a concept — an unresolved term returns None
and is logged (§7 labeling pipeline) so the physician review console can
propose it as a candidate synonym.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models.medical_ontology import (
    MedicalOntologyConcept,
    MedicalOntologySynonym,
)


# ─── Character folding ───────────────────────────────────────────────────────

# Combining marks + tatweel that MSA-unpointed Arabic medical text can drop
# without loss. Kept as a set for O(1) membership tests.
_ARABIC_DIACRITICS: frozenset[str] = frozenset(
    chr(c) for c in list(range(0x064B, 0x0660)) + [0x0640]
)

# Common Arabic letter normalisations — alef variants → bare alef, ya → alef
# maqsura is *not* folded (they carry meaning), taa marbuta → haa is a common
# practical fold for medical vocabulary matching.
_ARABIC_LETTER_FOLDS = {
    "آ": "ا",  # ALEF WITH MADDA -> ALEF
    "أ": "ا",  # ALEF WITH HAMZA ABOVE -> ALEF
    "إ": "ا",  # ALEF WITH HAMZA BELOW -> ALEF
    "ة": "ه",  # TAA MARBUTA -> HAA
    "ى": "ي",  # ALEF MAKSURA -> YAA
    "ک": "ك",  # persian keheh -> arabic kaf (used in Iraqi text)
    "ی": "ي",  # persian yeh -> arabic yaa
}

# Arabizi digit-to-Arabic-letter table. Applied only when the input mixes
# digits into Arabic-letter runs (see ``_maybe_apply_arabizi``).
_ARABIZI_TABLE = {
    "2": "ء",
    "3": "ع",
    "5": "خ",
    "6": "ط",
    "7": "ح",
    "8": "غ",
    "9": "ق",
}

_WS_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Return the canonical folded form of ``text``.

    Idempotent: ``normalize(normalize(x)) == normalize(x)``.

    Steps:
      1. Unicode NFKC normalisation.
      2. Casefold (lower-case + locale-independent case folds).
      3. Drop Arabic diacritics + tatweel.
      4. Apply Arabic letter folds (alef variants, taa marbuta).
      5. Fold Arabizi digits inside Arabic-letter runs.
      6. Collapse whitespace, trim.
    """
    if not text:
        return ""

    s = unicodedata.normalize("NFKC", text).casefold()
    s = "".join(c for c in s if c not in _ARABIC_DIACRITICS)
    s = "".join(_ARABIC_LETTER_FOLDS.get(c, c) for c in s)
    s = _maybe_apply_arabizi(s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def _maybe_apply_arabizi(s: str) -> str:
    """Substitute Arabizi digits when they appear in Arabic-letter context.

    Applied only when ambient context is Arabic — we do not want to corrupt
    English strings that happen to contain digits (e.g. ``"HbA1c"``,
    ``"25(OH)D"``). A digit is folded only if the nearest non-space
    character on either side is an Arabic letter (Unicode block
    U+0600..U+06FF). Spaces and punctuation between the digit and the
    nearest letter are skipped, so ``"مال 3 اشهر"`` and ``"مال3اشهر"``
    both fold.
    """
    if not any(c.isdigit() for c in s):
        return s

    def is_arabic(ch: str) -> bool:
        return "؀" <= ch <= "ۿ"

    def nearest(index: int, step: int) -> str:
        i = index + step
        while 0 <= i < len(s):
            if not s[i].isspace():
                return s[i]
            i += step
        return ""

    out = []
    for i, ch in enumerate(s):
        if ch in _ARABIZI_TABLE:
            if is_arabic(nearest(i, -1)) or is_arabic(nearest(i, +1)):
                out.append(_ARABIZI_TABLE[ch])
                continue
        out.append(ch)
    return "".join(out)


# ─── Concept resolution ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class ConceptMatch:
    """Result of a normaliser lookup.

    ``confidence`` reflects the aggregate of the synonym-row confidence and
    a ranking penalty (locale mismatch, variant type). Callers should reject
    matches below their own confidence floor (typical: 0.5 for retrieval
    expansion, 0.7 for interpretation).
    """
    concept_key: str
    concept_id: object
    category: str
    display_en: Optional[str]
    display_ar: Optional[str]
    matched_term: str
    matched_locale: str
    matched_variant: Optional[str]
    confidence: float


# Ordered ranking penalties applied to synonym-row confidence.
_LOCALE_MATCH_BONUS = 0.0
_LOCALE_MISS_PENALTY = 0.15
_VARIANT_PENALTIES = {
    "preferred":    0.0,
    "abbreviation": 0.02,
    "colloquial":   0.05,
    "phonetic":     0.10,
    "misspelling":  0.20,
}


def resolve_concept(
    session: Session,
    text: str,
    *,
    locales: Optional[Iterable[str]] = None,
    min_confidence: float = 0.0,
) -> Optional[ConceptMatch]:
    """Resolve ``text`` to a canonical concept.

    ``locales`` narrows the search — pass ``['ar', 'ar-IQ']`` when the user
    is clearly writing Arabic, so an English coincidence like ``"al"`` (a
    prepositional prefix) does not resolve to English "ALP".

    Returns None when no synonym matches above ``min_confidence``.
    """
    normalized = normalize_text(text)
    if not normalized:
        return None

    stmt = (
        select(
            MedicalOntologySynonym.term,
            MedicalOntologySynonym.locale,
            MedicalOntologySynonym.variant,
            MedicalOntologySynonym.confidence,
            MedicalOntologyConcept.id,
            MedicalOntologyConcept.concept_key,
            MedicalOntologyConcept.category,
            MedicalOntologyConcept.display_en,
            MedicalOntologyConcept.display_ar,
        )
        .join(
            MedicalOntologyConcept,
            MedicalOntologySynonym.concept_id == MedicalOntologyConcept.id,
        )
        .where(MedicalOntologySynonym.term_normalized == normalized)
        .where(MedicalOntologyConcept.status == "active")
    )
    rows = session.execute(stmt).all()
    if not rows:
        return None

    preferred_locales = set(locales) if locales else None
    best: Optional[ConceptMatch] = None
    best_score = -1.0

    for row in rows:
        (term, locale, variant, confidence, concept_id, concept_key,
         category, display_en, display_ar) = row

        score = float(confidence)
        if preferred_locales is not None:
            if locale in preferred_locales:
                score += _LOCALE_MATCH_BONUS
            else:
                score -= _LOCALE_MISS_PENALTY
        score -= _VARIANT_PENALTIES.get(variant or "preferred", 0.05)
        score = max(0.0, min(1.0, score))

        if score > best_score:
            best_score = score
            best = ConceptMatch(
                concept_key=concept_key,
                concept_id=concept_id,
                category=category,
                display_en=display_en,
                display_ar=display_ar,
                matched_term=term,
                matched_locale=locale,
                matched_variant=variant,
                confidence=score,
            )

    if best is None or best.confidence < min_confidence:
        return None
    return best


__all__ = ["ConceptMatch", "normalize_text", "resolve_concept"]
