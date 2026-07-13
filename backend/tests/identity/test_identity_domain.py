"""Identity Platform - Domain Layer Tests"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from shared.identity.domain import (
    Gender,
    IdentityDocument,
    IdentityDocumentType,
    IdentityStatus,
    PatientIdentity,
    PersonName,
)


class TestPersonName:
    def test_display_returns_arabic_when_available(self):
        name = PersonName(first="John", last="Doe", name_ar="جون دو")
        assert name.display(prefer_arabic=True) == "جون دو"

    def test_display_falls_back_to_full(self):
        name = PersonName(full="John Michael Doe")
        assert name.display(prefer_arabic=True) == "John Michael Doe"

    def test_display_constructs_from_parts(self):
        name = PersonName(first="John", middle="Michael", last="Doe")
        assert name.display(prefer_arabic=False) == "John Michael Doe"

    def test_normalized_removes_diacritics(self):
        name = PersonName(name_ar="مُحَمَّد")
        normalized = name.normalized()
        assert "ُ" not in normalized
        assert "َّ" not in normalized

    def test_normalized_maps_alef_variants(self):
        name = PersonName(name_ar="أحمد إبراهيم")
        normalized = name.normalized()
        assert "أ" not in normalized
        assert "إ" not in normalized


class TestIdentityDocument:
    def test_is_expired_false_when_no_expiry(self):
        doc = IdentityDocument(type=IdentityDocumentType.IRAQI_NATIONAL_ID, value="12345")
        assert doc.is_expired() is False

    def test_is_expired_true_when_expired(self):
        doc = IdentityDocument(
            type=IdentityDocumentType.IRAQI_NATIONAL_ID,
            value="12345",
            expires_at=date(2020, 1, 1),
        )
        assert doc.is_expired() is True

    def test_is_expired_false_when_future_expiry(self):
        doc = IdentityDocument(
            type=IdentityDocumentType.IRAQI_NATIONAL_ID,
            value="12345",
            expires_at=date(2099, 1, 1),
        )
        assert doc.is_expired() is False


class TestPatientIdentity:
    def test_age_from_dob(self):
        patient = PatientIdentity(date_of_birth=date(1990, 6, 15))
        expected_age = date.today().year - 1990 - (
            (date.today().month, date.today().day) < (6, 15)
        )
        assert patient.age() == expected_age

    def test_age_none_when_no_dob(self):
        patient = PatientIdentity()
        assert patient.age() is None

    def test_has_valid_national_id_true(self):
        patient = PatientIdentity(
            national_id_hash="abc123",
            documents=[IdentityDocument(
                type=IdentityDocumentType.IRAQI_NATIONAL_ID,
                value="1234567890",
            )],
        )
        assert patient.has_valid_national_id() is True

    def test_has_valid_national_id_false_when_no_hash(self):
        patient = PatientIdentity(
            documents=[IdentityDocument(
                type=IdentityDocumentType.IRAQI_NATIONAL_ID,
                value="1234567890",
            )],
        )
        assert patient.has_valid_national_id() is False

    def test_has_valid_national_id_false_when_no_doc(self):
        patient = PatientIdentity(national_id_hash="abc123")
        assert patient.has_valid_national_id() is False

    def test_to_dict_contains_all_required_fields(self):
        patient = PatientIdentity(
            id="P001",
            health_id="HID-ABCD1234-5678EF01",
            name=PersonName(first="Ali", last="Hassan", name_ar="علي حسن"),
            gender=Gender.MALE,
            phone="+9647701234567",
        )
        d = patient.to_dict()
        assert d["id"] == "P001"
        assert d["health_id"] == "HID-ABCD1234-5678EF01"
        assert d["name"]["first"] == "Ali"
        assert d["name"]["name_ar"] == "علي حسن"
        assert d["gender"] == "male"
        assert d["phone"] == "+9647701234567"
        assert d["status"] == "active"

    def test_deceased_status(self):
        patient = PatientIdentity(
            status=IdentityStatus.DECEASED,
            is_deceased=True,
        )
        assert patient.status == IdentityStatus.DECEASED
        assert patient.is_deceased is True
