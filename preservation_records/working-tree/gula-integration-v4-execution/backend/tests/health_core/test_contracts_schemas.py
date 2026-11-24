"""Contract tests: versioned Pydantic schemas accept only synthetic payloads."""

from __future__ import annotations

import pytest
from app.health_core.common import new_synthetic_id
from app.health_core.contracts.catalogue import ContractDomain
from app.health_core.contracts.models import (
    DOMAIN_SCHEMAS,
    PractitionerCreateRequest,
)
from app.health_core.contracts.version import CONTRACT_STATUS, HEALTH_CORE_CONTRACT_VERSION
from pydantic import ValidationError

ARABIC_TEXT = "نتيجة مختبر تجريبية"


def _ref(prefix: str = "TST") -> str:
    return new_synthetic_id(prefix)


def valid_request_payload(domain: ContractDomain) -> dict[str, object]:
    """Return a fresh, valid synthetic request payload for ``domain``."""
    fields: dict[ContractDomain, dict[str, object]] = {
        ContractDomain.PRACTITIONER: {
            "display_name": "د. ليلى",
            "role_code": "CLINICIAN",
            "active": True,
        },
        ContractDomain.ORGANIZATION: {
            "name": "مستشفى النور",
            "organization_type_code": "HOSPITAL",
        },
        ContractDomain.FACILITY: {
            "name": "مختبر بغداد",
            "organization_ref": _ref("ORG"),
            "facility_type_code": "LAB",
        },
        ContractDomain.MEDICAL_RECORD: {
            "patient_ref": _ref("PAT"),
            "title": "ملف المريض",
            "notes": ARABIC_TEXT,
        },
        ContractDomain.ENCOUNTER: {
            "patient_ref": _ref("PAT"),
            "practitioner_ref": _ref("PRC"),
            "facility_ref": _ref("FAC"),
            "reason": "زيارة متابعة",
        },
        ContractDomain.DIAGNOSIS: {
            "encounter_ref": _ref("ENC"),
            "code_system": "SNOMED-SYN",
            "code": "SYN-CODE-1",
            "display": "تشخيص تجريبي",
        },
        ContractDomain.OBSERVATION: {
            "patient_ref": _ref("PAT"),
            "encounter_ref": _ref("ENC"),
            "code": "SYN-OBS-1",
            "value_text": "12.5",
            "unit": "MG-DL-SYN",
        },
        ContractDomain.LAB_ORDER: {
            "patient_ref": _ref("PAT"),
            "practitioner_ref": _ref("PRC"),
            "facility_ref": _ref("FAC"),
            "test_code": "SYN-TEST-1",
        },
        ContractDomain.SPECIMEN: {
            "order_ref": _ref("ORD"),
            "specimen_type_code": "SYN-SPEC-1",
            "collection_site": "وريد",
        },
        ContractDomain.LAB_RESULT: {
            "order_ref": _ref("ORD"),
            "specimen_ref": _ref("SPC"),
            "test_code": "SYN-TEST-1",
            "value_text": "13.0",
            "unit": "MG-DL-SYN",
            "abnormal_flag": True,
        },
        ContractDomain.RESULT_VERIFICATION: {
            "result_ref": _ref("RES"),
            "verifier_ref": _ref("PRC"),
            "verification_note": "تمت المراجعة",
        },
    }
    return {"tenant_id": _ref("LAB"), **fields[domain]}


def valid_response_payload(domain: ContractDomain) -> dict[str, object]:
    """Return a fresh, valid synthetic response payload for ``domain``."""
    payload = valid_request_payload(domain)
    payload["ref"] = _ref("ENT")
    if domain is ContractDomain.RESULT_VERIFICATION:
        payload["verified_at"] = "2026-11-18T12:00:00+00:00"
    return payload


def test_every_domain_has_a_request_and_response_schema() -> None:
    assert set(DOMAIN_SCHEMAS) == set(ContractDomain)
    for domain, (request_model, response_model) in DOMAIN_SCHEMAS.items():
        assert request_model.__name__.endswith("Request"), domain
        assert response_model.__name__.endswith("Response"), domain


@pytest.mark.parametrize("domain", list(ContractDomain))
def test_valid_request_payload_accepted_for_every_domain(domain: ContractDomain) -> None:
    model = DOMAIN_SCHEMAS[domain][0]
    instance = model(**valid_request_payload(domain))
    assert instance.tenant_id.startswith("SYN-")
    assert instance.model_dump()["tenant_id"].startswith("SYN-")


@pytest.mark.parametrize("domain", list(ContractDomain))
def test_valid_response_payload_accepted_for_every_domain(domain: ContractDomain) -> None:
    model = DOMAIN_SCHEMAS[domain][1]
    instance = model(**valid_response_payload(domain))
    assert instance.ref.startswith("SYN-")


@pytest.mark.parametrize("domain", list(ContractDomain))
def test_response_models_are_version_tagged(domain: ContractDomain) -> None:
    instance = DOMAIN_SCHEMAS[domain][1](**valid_response_payload(domain))
    assert instance.contract_version == HEALTH_CORE_CONTRACT_VERSION
    assert instance.contract_status == CONTRACT_STATUS


def test_arabic_free_text_is_preserved_verbatim() -> None:
    payload = valid_request_payload(ContractDomain.MEDICAL_RECORD)
    payload["notes"] = ARABIC_TEXT
    instance = DOMAIN_SCHEMAS[ContractDomain.MEDICAL_RECORD][0](**payload)
    assert instance.notes == ARABIC_TEXT


@pytest.mark.parametrize("bad_ref", ["123456789012", "ABC123456789", "", "   ", "PAT-1234"])
def test_real_looking_or_empty_references_are_rejected(bad_ref: str) -> None:
    payload = valid_request_payload(ContractDomain.PRACTITIONER)
    payload["tenant_id"] = bad_ref
    with pytest.raises(ValidationError):
        PractitionerCreateRequest(**payload)


def test_non_synthetic_aggregate_reference_is_rejected() -> None:
    payload = valid_request_payload(ContractDomain.MEDICAL_RECORD)
    payload["patient_ref"] = "PAT-0001"
    with pytest.raises(ValidationError):
        DOMAIN_SCHEMAS[ContractDomain.MEDICAL_RECORD][0](**payload)


def test_unknown_fields_are_forbidden() -> None:
    payload = valid_request_payload(ContractDomain.PRACTITIONER)
    payload["real_identifier_field"] = "should-not-be-accepted"
    with pytest.raises(ValidationError):
        PractitionerCreateRequest(**payload)


def test_contract_models_are_immutable() -> None:
    instance = PractitionerCreateRequest(**valid_request_payload(ContractDomain.PRACTITIONER))
    with pytest.raises(ValidationError):
        instance.role_code = "ADMIN"  # type: ignore[misc]


def test_free_text_length_is_bounded() -> None:
    payload = valid_request_payload(ContractDomain.PRACTITIONER)
    payload["display_name"] = "أ" * 513
    with pytest.raises(ValidationError):
        PractitionerCreateRequest(**payload)


def test_models_are_serialisable_to_json() -> None:
    instance = DOMAIN_SCHEMAS[ContractDomain.LAB_RESULT][1](
        **valid_response_payload(ContractDomain.LAB_RESULT)
    )
    encoded = instance.model_dump_json()
    assert "SYN-" in encoded
    assert HEALTH_CORE_CONTRACT_VERSION in encoded
