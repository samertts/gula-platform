"""Unit tests for backend/app/services/identity.py — name normalization, matching, hashing."""

from __future__ import annotations

import pytest
from app.services.identity import (
    hash_family_id,
    hash_national_id,
    jaro_similarity,
    jaro_winkler,
    match_score,
    normalize_arabic,
    normalize_name,
)


class TestNormalizeArabic:
    def test_removes_diacritics(self):
        assert "ُ" not in normalize_arabic("مُحَمَّد")
        assert "َ" not in normalize_arabic("مُحَمَّد")

    def test_normalizes_alef_variants(self):
        assert normalize_arabic("أحمد إبراهيم آدم") == "احمد ابراهيم ادم"

    def test_normalizes_ta_marbuta(self):
        assert normalize_arabic("فاطمة") == "فاطمه"

    def test_normalizes_alef_maksura_and_hamza(self):
        assert normalize_arabic("مستشفى مؤمن ئسلام") == "مستشفي مومن يسلام"

    def test_plain_arabic_unchanged(self):
        assert normalize_arabic("محمد") == "محمد"

    def test_empty_string(self):
        assert normalize_arabic("") == ""


class TestNormalizeName:
    def test_trims_and_collapses_whitespace(self):
        assert normalize_name("  محمد   علي  ") == "محمد علي"

    def test_lowercases_english(self):
        assert normalize_name("MOHAMMED ALI") == "mohammed ali"

    def test_normalizes_english_variants(self):
        assert normalize_name("mohamed") == "mohammed"
        assert normalize_name("ahmad") == "ahmed"
        assert normalize_name("hussain") == "hussein"

    def test_normalizes_arabic_then_lowercase(self):
        assert normalize_name("مُحَمَّد") == "محمد"

    def test_empty_name_returns_empty(self):
        assert normalize_name("") == ""
        assert normalize_name(None) == ""  # type: ignore[arg-type]

    def test_unknown_token_unchanged(self):
        assert normalize_name("xyzzy") == "xyzzy"


class TestJaroSimilarity:
    def test_identical_strings(self):
        assert jaro_similarity("abc", "abc") == 1.0

    def test_completely_different(self):
        assert jaro_similarity("abc", "xyz") == 0.0

    def test_empty_inputs(self):
        assert jaro_similarity("", "abc") == 0.0
        assert jaro_similarity("abc", "") == 0.0

    def test_transposition_counts(self):
        score = jaro_similarity("marhta", "marthra")
        assert 0.8 < score < 1.0

    def test_single_typo(self):
        score = jaro_similarity("karim", "karin")
        assert 0.8 < score < 1.0


class TestJaroWinkler:
    def test_identical_strings(self):
        assert jaro_winkler("abc", "abc") == 1.0

    def test_prefix_boost_applied(self):
        plain = jaro_similarity("ahmed", "ahmad")
        boosted = jaro_winkler("ahmed", "ahmad")
        assert boosted >= plain

    def test_no_boost_below_threshold(self):
        assert jaro_winkler("abc", "xyz") == jaro_similarity("abc", "xyz")

    def test_custom_prefix_weight(self):
        base = jaro_winkler("mohammed", "mohammad")
        stronger = jaro_winkler("mohammed", "mohammad", prefix_weight=0.2)
        assert stronger > base


class TestMatchScore:
    def test_national_id_hash_is_definitive(self):
        assert (
            match_score("a", "1", "2000-01-01", "b", "2", "1999-01-01",
                        p1_national_id_hash="h1", p2_national_id_hash="h1")
            == 1.0
        )

    def test_exact_name_phone_birth_maxes_at_1(self):
        score = match_score("محمد علي", "07701234567", "1990-01-01",
                            "محمد علي", "07701234567", "1990-01-01")
        assert score == 1.0

    def test_name_alone_gives_045(self):
        score = match_score("محمد علي", "", "", "محمد علي", "", "")
        assert score == pytest.approx(0.45)

    def test_similar_name_gives_030(self):
        score = match_score("احمد علي محمد حسين كريم", "", "",
                            "احمد علي محمد حسين كريم جمال", "", "")
        assert score == pytest.approx(0.30)

    def test_phone_matching_normalizes_digits(self):
        score = match_score("", "07701234567", "", "", "+9647701234567", "")
        assert score == pytest.approx(0.35)

    def test_birth_match(self):
        score = match_score("", "", "1990-05-05", "", "", "1990-05-05")
        assert score == pytest.approx(0.20)

    def test_no_signals_zero(self):
        assert match_score("", "", "", "", "", "") == 0.0

    def test_mismatched_national_ids_not_definitive(self):
        score = match_score("محمد علي", "07701234567", "1990-01-01",
                            "محمد علي", "07701234567", "1990-01-01",
                            p1_national_id_hash="h1", p2_national_id_hash="h2")
        assert score == 1.0  # capped, still all other signals match


class TestHashing:
    def test_hash_national_id_is_stable(self):
        assert hash_national_id("07001234567") == hash_national_id("07001234567")

    def test_hash_national_id_deterministic_hex(self):
        result = hash_national_id("07001234567")
        assert len(result) == 64
        int(result, 16)

    def test_hash_national_id_strips_non_digits(self):
        assert hash_national_id("0700-123-4567") == hash_national_id("07001234567")

    def test_hash_national_id_empty(self):
        assert hash_national_id("") == ""

    def test_family_id_domain_separation(self):
        assert hash_family_id("12345") != hash_national_id("12345")

    def test_family_id_stable_and_strips_digits(self):
        assert hash_family_id("12-345") == hash_family_id("12345")

    def test_family_id_empty(self):
        assert hash_family_id("") == ""
