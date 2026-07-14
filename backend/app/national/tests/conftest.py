from __future__ import annotations

import pytest


@pytest.fixture
def sample_citizen_data() -> dict:
    return {
        "first_name": "Ali",
        "father_name": "Ahmed",
        "last_name": "Hassan",
        "date_of_birth": "1990-01-15",
        "gender": "male",
        "phone": "+9647701234567",
        "governorate": "Baghdad",
        "nationality": "Iraqi",
    }


@pytest.fixture
def sample_newborn_data() -> dict:
    return {
        "birth_certificate_number": "BC20260501-001",
        "first_name": "Zainab",
        "last_name": "Hassan",
        "date_of_birth": "2026-05-01",
        "gender": "female",
        "mother_id": "CIT001",
        "birth_weight_grams": 3200,
    }


@pytest.fixture
def sample_foreigner_data() -> dict:
    return {
        "passport_number": "P12345678",
        "passport_country": "Jordan",
        "first_name": "Mohammad",
        "last_name": "Al-Jaberi",
        "date_of_birth": "1985-06-20",
        "gender": "male",
        "nationality": "Jordanian",
        "visa_number": "V987654",
    }


@pytest.fixture
def sample_encounter_data() -> dict:
    return {
        "patient_id": "PAT001",
        "encounter_type": "outpatient",
        "facility_id": "FAC001",
        "practitioner_id": "PRAC001",
        "reason_description": "Routine checkup",
        "period_start": "2026-05-01T10:00:00",
    }


@pytest.fixture
def sample_family_data() -> dict:
    return {
        "family_name": "Al-Hassan",
        "family_name_ar": "آل حسن",
        "governorate": "Baghdad",
        "head_of_family_name": "Ahmed Hassan",
    }
