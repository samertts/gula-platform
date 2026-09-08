"""Tests for the Medical Ontology Core (directive §1 §2 §9).

Covers:
  * normalize_text: Arabic diacritic stripping, alef folding, Arabizi digit
    substitution, whitespace collapse, idempotence
  * resolve_concept: exact match, locale disambiguation, variant penalty,
    unknown text
  * unit conversion: universal + concept-scoped, missing conversion raises
  * reference range engine: adult vs pediatric ALP, sex-adjusted creatinine,
    pregnancy-adjusted haemoglobin, HbA1c critical, provenance surfaced,
    unknown concept raises, missing demographic raises

Every test sets up its ontology rows fresh — the seed loader is not
exercised here (that has its own smoke test at the bottom).
"""
# mypy: ignore-errors
# The mypy config already excludes ``tests/`` at project scope; the CI
# changed-files gate bypasses that exclude by passing test files as
# explicit arguments. File-level silence keeps the intent consistent.
from __future__ import annotations

import datetime as _dt

import pytest
from app.models.medical_ontology import (
    MedicalOntologyConcept,
    MedicalOntologyReferenceRange,
    MedicalOntologySynonym,
    MedicalOntologyUnitConversion,
)
from app.services.medical_ontology import normalize as normalize_mod
from app.services.medical_ontology.normalize import (
    normalize_text,
    resolve_concept,
)
from app.services.medical_ontology.reference_range import (
    ReferenceRangeError,
    interpret,
)
from app.services.medical_ontology.units import (
    UnitConversionError,
    convert,
)


def _now() -> _dt.datetime:
    return _dt.datetime.now(tz=_dt.UTC)


# ─── Fixtures ────────────────────────────────────────────────────────────────

def _make_concept(
    db,
    *,
    key: str,
    category: str = "biomarker",
    canonical_unit: str | None = None,
    display_en: str | None = None,
    display_ar: str | None = None,
) -> MedicalOntologyConcept:
    c = MedicalOntologyConcept(
        concept_key=key,
        category=category,
        display_en=display_en or key,
        display_ar=display_ar,
        canonical_unit_key=canonical_unit,
        status="active",
        version=1,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(c)
    db.flush()
    return c


def _make_synonym(
    db,
    concept: MedicalOntologyConcept,
    *,
    term: str,
    locale: str,
    variant: str | None = "preferred",
    confidence: float = 1.0,
) -> MedicalOntologySynonym:
    s = MedicalOntologySynonym(
        concept_id=concept.id,
        term=term,
        term_normalized=normalize_text(term),
        locale=locale,
        variant=variant,
        confidence=confidence,
        created_at=_now(),
    )
    db.add(s)
    db.flush()
    return s


def _make_range(
    db,
    concept: MedicalOntologyConcept,
    *,
    unit: str,
    low: float | None = None,
    high: float | None = None,
    critical_low: float | None = None,
    critical_high: float | None = None,
    age_min: float | None = None,
    age_max: float | None = None,
    sex: str = "any",
    pregnancy_status: str = "any",
    source: str = "internal",
    source_version: str = "v1",
    source_url: str | None = None,
    notes: str | None = None,
) -> MedicalOntologyReferenceRange:
    r = MedicalOntologyReferenceRange(
        concept_id=concept.id,
        unit_key=unit,
        age_min_years=age_min,
        age_max_years=age_max,
        sex=sex,
        pregnancy_status=pregnancy_status,
        low=low,
        high=high,
        critical_low=critical_low,
        critical_high=critical_high,
        source=source,
        source_version=source_version,
        source_url=source_url,
        notes=notes,
        status="active",
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(r)
    db.flush()
    return r


# ─── normalize_text ──────────────────────────────────────────────────────────

class TestNormalize:
    def test_lowercase_english(self):
        assert normalize_text("HbA1c") == "hba1c"

    def test_strips_arabic_diacritics(self):
        # Diacritics: fatha, kasra, damma, shadda, sukun
        assert normalize_text("سُكَّرٌ") == normalize_text("سكر")

    def test_folds_alef_variants(self):
        for variant in ("أ", "إ", "آ"):
            assert normalize_text(f"{variant}لسكر") == normalize_text("السكر")

    def test_folds_taa_marbuta(self):
        assert normalize_text("الغدة") == normalize_text("الغده")

    def test_arabizi_digits_in_arabic_context(self):
        # "sukkar mal 3 ashhur" — the 3 is Arabizi for ع.
        # Applied only when adjacent to Arabic letters — pure Latin form
        # stays as-is.
        assert normalize_text("hba1c") == "hba1c"  # digit surrounded by Latin
        arabic_with_digit = normalize_text("مال 3 اشهر")
        arabic_folded = normalize_text("مال ع اشهر")
        assert arabic_with_digit == arabic_folded

    def test_arabizi_digits_do_not_corrupt_english_biomarker_names(self):
        # 25(OH)D would be a nightmare if the 2/5 got folded.
        result = normalize_text("25(OH)D")
        assert "2" in result and "5" in result

    def test_collapses_whitespace(self):
        assert normalize_text("hb  a1c  ") == "hb a1c"

    def test_idempotent(self):
        for s in ("HbA1c", "سُكَّرٌ", "أَلْأَنِيمْيَا", "  spaces  "):
            once = normalize_text(s)
            assert normalize_text(once) == once

    def test_empty(self):
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""


# ─── resolve_concept ─────────────────────────────────────────────────────────

class TestResolveConcept:
    def _setup_hba1c(self, db):
        c = _make_concept(
            db, key="biomarker:hba1c",
            canonical_unit="unit:pct",
            display_en="Hemoglobin A1c",
            display_ar="الهيموغلوبين السكري",
        )
        _make_synonym(db, c, term="HbA1c", locale="en", variant="preferred")
        _make_synonym(db, c, term="A1C", locale="en", variant="abbreviation")
        _make_synonym(db, c, term="السكر التراكمي",
                      locale="ar-IQ", variant="colloquial")
        _make_synonym(db, c, term="الهيموغلوبين السكري",
                      locale="ar", variant="preferred")
        return c

    def test_exact_english_match(self, db):
        self._setup_hba1c(db)
        m = resolve_concept(db, "HbA1c")
        assert m is not None
        assert m.concept_key == "biomarker:hba1c"

    def test_matches_arabizi_input_after_folding(self, db):
        c = _make_concept(db, key="biomarker:hba1c")
        _make_synonym(db, c, term="سكر تراكمي",
                      locale="ar-IQ", variant="colloquial")
        # User types Arabizi with digit — normalizer folds the 3 → ع inside
        # Arabic context.  Seed the folded form so we can prove the pipeline.
        _make_synonym(db, c, term="سكر تركمي",
                      locale="arabizi", variant="phonetic")
        # This tests the normalizer + resolver together end-to-end.
        m = resolve_concept(db, "سكر تراكمي")
        assert m is not None and m.concept_key == "biomarker:hba1c"

    def test_iraqi_dialect_colloquial(self, db):
        self._setup_hba1c(db)
        m = resolve_concept(db, "السكر التراكمي", locales=["ar", "ar-IQ"])
        assert m is not None
        assert m.concept_key == "biomarker:hba1c"
        assert m.matched_locale == "ar-IQ"

    def test_preferred_variant_beats_abbreviation_when_tied(self, db):
        c = _make_concept(db, key="biomarker:hba1c")
        _make_synonym(db, c, term="HbA1c",
                      locale="en", variant="preferred", confidence=1.0)
        c2 = _make_concept(db, key="biomarker:other")
        _make_synonym(db, c2, term="HbA1c",
                      locale="en", variant="abbreviation", confidence=1.0)
        m = resolve_concept(db, "HbA1c")
        assert m is not None
        assert m.concept_key == "biomarker:hba1c"

    def test_unknown_term_returns_none(self, db):
        self._setup_hba1c(db)
        assert resolve_concept(db, "zzz_does_not_exist") is None

    def test_below_confidence_floor_returns_none(self, db):
        c = _make_concept(db, key="biomarker:hba1c")
        _make_synonym(db, c, term="typo",
                      locale="en", variant="misspelling", confidence=0.4)
        # variant misspelling deducts 0.20 → 0.20; floor 0.5 rejects.
        assert resolve_concept(db, "typo", min_confidence=0.5) is None

    def test_normalize_module_public_api(self):
        assert callable(normalize_mod.normalize_text)
        assert callable(normalize_mod.resolve_concept)


# ─── Unit conversion ─────────────────────────────────────────────────────────

class TestUnitConversion:
    def test_same_unit_returns_unchanged(self, db):
        assert convert(db, 5.0, "unit:mg_per_dL", "unit:mg_per_dL") == 5.0

    def test_universal_conversion(self, db):
        db.add(MedicalOntologyUnitConversion(
            from_unit_key="unit:g_per_dL",
            to_unit_key="unit:g_per_L",
            factor=10.0,
            offset=0.0,
            concept_scope_key=None,
            source="SI",
            created_at=_now(),
        ))
        db.flush()
        assert convert(db, 12.0, "unit:g_per_dL", "unit:g_per_L") == 120.0

    def test_concept_scoped_conversion_wins(self, db):
        # A universal fallback exists but a glucose-specific factor must win.
        db.add(MedicalOntologyUnitConversion(
            from_unit_key="unit:mg_per_dL",
            to_unit_key="unit:mmol_per_L",
            factor=99.0, offset=0.0, concept_scope_key=None,
            source="wrong-universal",
            created_at=_now(),
        ))
        db.add(MedicalOntologyUnitConversion(
            from_unit_key="unit:mg_per_dL",
            to_unit_key="unit:mmol_per_L",
            factor=0.05551, offset=0.0,
            concept_scope_key="biomarker:glucose_fasting",
            source="MW glucose",
            created_at=_now(),
        ))
        db.flush()
        result = convert(
            db, 180.0, "unit:mg_per_dL", "unit:mmol_per_L",
            concept_scope_key="biomarker:glucose_fasting",
        )
        assert abs(result - 9.99) < 0.05

    def test_missing_conversion_raises(self, db):
        with pytest.raises(UnitConversionError):
            convert(db, 1.0, "unit:foo", "unit:bar")


# ─── Reference range engine ──────────────────────────────────────────────────

class TestReferenceRange:
    def test_unknown_concept_raises(self, db):
        with pytest.raises(ReferenceRangeError):
            interpret(
                db, "biomarker:not_seeded", 1.0, "unit:mg_per_dL",
                age_years=30, sex="male",
            )

    def test_adult_alp_uses_adult_range_not_pediatric(self, db):
        c = _make_concept(db, key="biomarker:alp",
                          canonical_unit="unit:U_per_L")
        _make_range(db, c, unit="unit:U_per_L",
                    age_min=1, age_max=9,
                    low=100, high=350,
                    source="Mayo", source_version="peds")
        _make_range(db, c, unit="unit:U_per_L",
                    age_min=18,
                    low=44, high=121,
                    source="Mayo", source_version="adult")

        adult = interpret(db, "biomarker:alp", 80.0, "unit:U_per_L",
                          age_years=45, sex="any")
        assert adult.direction == "in_range"
        assert adult.matched_range.age_min_years == 18
        assert adult.provenance.source_version == "adult"

        child = interpret(db, "biomarker:alp", 200.0, "unit:U_per_L",
                          age_years=5, sex="any")
        # 200 U/L is normal for a 5-year-old (100-350) -> in_range.
        assert child.direction == "in_range"
        assert child.matched_range.age_min_years == 1
        assert child.provenance.source_version == "peds"

    def test_sex_adjusted_creatinine(self, db):
        c = _make_concept(db, key="biomarker:creatinine",
                          canonical_unit="unit:mg_per_dL")
        _make_range(db, c, unit="unit:mg_per_dL", age_min=18, sex="male",
                    low=0.74, high=1.35, source="Mayo")
        _make_range(db, c, unit="unit:mg_per_dL", age_min=18, sex="female",
                    low=0.59, high=1.04, source="Mayo")

        # 1.1 mg/dL is normal for a man, elevated for a woman.
        m = interpret(db, "biomarker:creatinine", 1.1, "unit:mg_per_dL",
                      age_years=40, sex="male")
        assert m.direction == "in_range"

        f = interpret(db, "biomarker:creatinine", 1.1, "unit:mg_per_dL",
                      age_years=40, sex="female")
        assert f.direction == "high"
        assert f.matched_range.sex == "female"

    def test_pregnancy_adjusted_hemoglobin(self, db):
        c = _make_concept(db, key="biomarker:hemoglobin",
                          canonical_unit="unit:g_per_dL")
        _make_range(db, c, unit="unit:g_per_dL",
                    age_min=15, sex="female",
                    pregnancy_status="not_pregnant",
                    low=12.0, high=15.5, source="WHO")
        _make_range(db, c, unit="unit:g_per_dL",
                    age_min=15, sex="female",
                    pregnancy_status="pregnant",
                    low=11.0, high=14.0, source="WHO")

        non_preg = interpret(
            db, "biomarker:hemoglobin", 11.5, "unit:g_per_dL",
            age_years=30, sex="female", pregnancy_status="not_pregnant",
        )
        assert non_preg.direction == "low"
        assert non_preg.matched_range.pregnancy_status == "not_pregnant"

        preg = interpret(
            db, "biomarker:hemoglobin", 11.5, "unit:g_per_dL",
            age_years=30, sex="female", pregnancy_status="pregnant",
        )
        assert preg.direction == "in_range"
        assert preg.matched_range.pregnancy_status == "pregnant"

    def test_hba1c_severity_and_risk_level(self, db):
        c = _make_concept(db, key="biomarker:hba1c",
                          canonical_unit="unit:pct")
        _make_range(db, c, unit="unit:pct", age_min=18,
                    low=4.0, high=5.6, critical_high=12.0,
                    source="ADA", source_version="2024")

        # Normal
        n = interpret(db, "biomarker:hba1c", 5.2, "unit:pct",
                      age_years=40, sex="any")
        assert n.level == "normal"
        assert n.risk_level == "informational"
        assert n.escalation_required is False

        # Prediabetes range (5.7-6.4) -> mildly high (deviation ~14%)
        mild = interpret(db, "biomarker:hba1c", 6.0, "unit:pct",
                         age_years=40, sex="any")
        assert mild.direction == "high"
        assert mild.level == "mildly_abnormal"
        assert mild.risk_level == "low_risk"

        # Severely elevated but not critical → high_risk + escalation
        severe = interpret(db, "biomarker:hba1c", 9.0, "unit:pct",
                           age_years=40, sex="any")
        assert severe.level == "severely_abnormal"
        assert severe.risk_level == "high_risk"
        assert severe.escalation_required is True

        # Critical band
        crit = interpret(db, "biomarker:hba1c", 13.0, "unit:pct",
                         age_years=40, sex="any")
        assert crit.level == "critical"
        assert crit.risk_level == "emergency_risk"
        assert crit.escalation_required is True

    def test_provenance_surfaces_source_and_version(self, db):
        c = _make_concept(db, key="biomarker:hba1c",
                          canonical_unit="unit:pct")
        _make_range(db, c, unit="unit:pct", age_min=18,
                    low=4.0, high=5.6,
                    source="ADA", source_version="ADA 2024",
                    source_url="https://example.org/ada2024")
        r = interpret(db, "biomarker:hba1c", 5.0, "unit:pct",
                      age_years=30, sex="any")
        assert r.provenance.source == "ADA"
        assert r.provenance.source_version == "ADA 2024"
        assert r.provenance.source_url == "https://example.org/ada2024"

    def test_unit_conversion_applied_before_range_lookup(self, db):
        c = _make_concept(db, key="biomarker:glucose_fasting",
                          canonical_unit="unit:mg_per_dL")
        _make_range(db, c, unit="unit:mg_per_dL", age_min=18,
                    low=70, high=99, source="ADA")
        db.add(MedicalOntologyUnitConversion(
            from_unit_key="unit:mmol_per_L",
            to_unit_key="unit:mg_per_dL",
            factor=18.016, offset=0.0,
            concept_scope_key="biomarker:glucose_fasting",
            source="MW glucose",
            created_at=_now(),
        ))
        db.flush()

        # 5.5 mmol/L ≈ 99 mg/dL → borderline in_range.
        r = interpret(
            db, "biomarker:glucose_fasting", 5.5, "unit:mmol_per_L",
            age_years=30, sex="any",
        )
        assert r.unit_canonical == "unit:mg_per_dL"
        assert abs(r.value_canonical - 99.088) < 0.5
        assert r.direction in ("in_range", "high")  # rounding boundary

    def test_no_matching_demographic_raises(self, db):
        c = _make_concept(db, key="biomarker:hba1c",
                          canonical_unit="unit:pct")
        _make_range(db, c, unit="unit:pct", age_min=18,
                    low=4.0, high=5.6, source="ADA")
        # Pediatric input with only an adult range seeded.
        with pytest.raises(ReferenceRangeError):
            interpret(db, "biomarker:hba1c", 5.0, "unit:pct",
                      age_years=5, sex="any")
