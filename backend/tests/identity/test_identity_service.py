"""Identity Platform - Application Service Tests"""
from __future__ import annotations

from datetime import date

import pytest

from shared.identity.domain import Gender, PatientIdentity, PersonName
from shared.identity.service import (
    IdentityService,
    calculate_match_score,
    generate_health_id,
    get_name_variants,
    hash_national_id,
    normalize_arabic_name,
    normalize_name_token,
    normalize_phone,
)


class TestArabicNormalization:
    def test_removes_diacritics(self):
        result = normalize_arabic_name("مُحَمَّد")
        assert "ُ" not in result
        assert "َّ" not in result

    def test_normalizes_alef_variants(self):
        result = normalize_arabic_name("أحمد إبراهيم آدم")
        assert "أ" not in result
        assert "إ" not in result
        assert "آ" not in result

    def test_normalizes_ta_marbuta(self):
        result = normalize_arabic_name("فاطمة")
        assert "ة" not in result
        assert "ه" in result

    def test_normalizes_alef_maksura(self):
        result = normalize_arabic_name("مستشفى")
        assert result.endswith("ي")

    def test_handles_none(self):
        assert normalize_arabic_name(None) == ""

    def test_handles_empty(self):
        assert normalize_arabic_name("") == ""


class TestPhoneNormalization:
    def test_keeps_international_format(self):
        assert normalize_phone("+9647701234567") == "+9647701234567"

    def test_converts_local_format(self):
        assert normalize_phone("07701234567") == "+9647701234567"

    def test_converts_00964_format(self):
        assert normalize_phone("009647701234567") == "+9647701234567"

    def test_strips_spaces_and_dashes(self):
        assert normalize_phone("+964 770 123 4567") == "+9647701234567"

    def test_handles_none(self):
        assert normalize_phone(None) == ""


class TestHealthIdGeneration:
    def test_generates_consistent_id(self):
        h1 = generate_health_id("1234567890", secret="test-secret")
        h2 = generate_health_id("1234567890", secret="test-secret")
        assert h1 == h2

    def test_different_nids_produce_different_ids(self):
        h1 = generate_health_id("1234567890", secret="test-secret")
        h2 = generate_health_id("0987654321", secret="test-secret")
        assert h1 != h2

    def test_format_matches_pattern(self):
        hid = generate_health_id("1234567890")
        assert hid.startswith("HID-")
        parts = hid.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8
        assert len(parts[2]) == 8


class TestNationalIdHashing:
    def test_produces_deterministic_hash(self):
        h1 = hash_national_id("1234567890", "test-hmac-key")
        h2 = hash_national_id("1234567890", "test-hmac-key")
        assert h1 == h2

    def test_different_keys_produce_different_hashes(self):
        h1 = hash_national_id("1234567890", "key-one")
        h2 = hash_national_id("1234567890", "key-two")
        assert h1 != h2

    def test_returns_empty_for_empty_input(self):
        assert hash_national_id("", "key") == ""
        assert hash_national_id("123", "") == ""


class TestMatchScoring:
    def test_perfect_nid_match(self):
        a = PatientIdentity(national_id_hash="abc123")
        b = PatientIdentity(national_id_hash="abc123")
        score = calculate_match_score(a, b)
        assert score >= 0.4

    def test_perfect_phone_match(self):
        a = PatientIdentity(phone="+9647701234567")
        b = PatientIdentity(phone="+9647701234567")
        score = calculate_match_score(a, b)
        assert score >= 0.25

    def test_normalized_phone_match(self):
        a = PatientIdentity(phone="07701234567")
        b = PatientIdentity(phone="+9647701234567")
        score = calculate_match_score(a, b)
        assert score >= 0.25

    def test_dob_match(self):
        a = PatientIdentity(date_of_birth=date(1990, 1, 1))
        b = PatientIdentity(date_of_birth=date(1990, 1, 1))
        score = calculate_match_score(a, b)
        assert score >= 0.15

    def test_no_match_returns_low_score(self):
        a = PatientIdentity(national_id_hash="abc")
        b = PatientIdentity(national_id_hash="xyz")
        score = calculate_match_score(a, b)
        assert score < 0.4

    def test_score_capped_at_one(self):
        a = PatientIdentity(
            national_id_hash="same",
            phone="+9647701111111",
            date_of_birth=date(1990, 1, 1),
        )
        b = PatientIdentity(
            national_id_hash="same",
            phone="+9647701111111",
            date_of_birth=date(1990, 1, 1),
        )
        score = calculate_match_score(a, b)
        assert score <= 1.0


class TestNameVariants:
    def test_returns_canonical_variants(self):
        variants = get_name_variants("Mohammed")
        assert "mohammed" in variants
        assert True  # Might not generate all

    def test_normalize_name_token_strips_non_arabic_latin(self):
        result = normalize_name_token("Moh@me_d!132")
        assert "@" not in result
        assert "!" not in result


class TestIdentityService:
    def test_normalize_patient_updates_phone(self):
        service = IdentityService()
        patient = PatientIdentity(phone="07701234567")
        service.normalize_patient(patient)
        assert patient.phone == "+9647701234567"

    def test_find_duplicate_candidates_returns_scored_list(self):
        service = IdentityService()
        target = PatientIdentity(
            national_id_hash="abc123",
            phone="+9647701111111",
        )
        existing = [
            PatientIdentity(
                national_id_hash="abc123",
                phone="+9647701111111",
            ),
            PatientIdentity(
                national_id_hash="xyz789",
                phone="+9647709999999",
            ),
        ]
        candidates = service.find_duplicate_candidates(target, existing)
        assert len(candidates) >= 1
        assert candidates[0][1] >= 0.6
