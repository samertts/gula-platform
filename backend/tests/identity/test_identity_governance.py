from __future__ import annotations

import pytest
from app.services.governance.identity_governance import (
    DocumentVerificationStatus,
    IdentityDocumentType,
    IdentityGovernanceService,
)


class TestIdentityGovernance:
    def test_register_citizen(self):
        svc = IdentityGovernanceService(nid_hmac_key="test-key")
        record = svc.register_citizen(
            full_name="Ali Ahmed",
            national_id="1234567890",
            gender="male",
        )
        assert record.identity_type == "citizen"
        assert record.health_number.startswith("HN-")
        assert record.national_id_hash
        assert len(record.history) == 1
        assert record.get_document(IdentityDocumentType.IRAQI_NATIONAL_ID) is not None

    def test_register_newborn(self):
        from datetime import date
        svc = IdentityGovernanceService()
        record = svc.register_newborn(
            full_name="Baby Ali",
            date_of_birth=date.today(),
            gender="male",
            parent_national_id="1234567890",
            birth_certificate_number="BC-2026-001",
        )
        assert record.identity_type == "newborn"
        assert record.get_document(IdentityDocumentType.BIRTH_CERTIFICATE) is not None

    def test_register_foreigner(self):
        svc = IdentityGovernanceService()
        record = svc.register_foreigner(
            full_name="John Smith",
            passport_number="AB123456",
            country_of_origin="US",
            visa_number="V-2026-001",
        )
        assert record.identity_type == "foreigner"
        assert record.get_document(IdentityDocumentType.PASSPORT) is not None
        assert record.get_document(IdentityDocumentType.VISA) is not None

    def test_register_visitor(self):
        svc = IdentityGovernanceService()
        record = svc.register_visitor(
            full_name="Tourist One",
            passport_number="CD789012",
            visa_number="V-2026-002",
            country_of_origin="UK",
        )
        assert record.identity_type == "visitor"

    def test_register_unknown_patient(self):
        svc = IdentityGovernanceService()
        record = svc.register_unknown_patient(gender="female", approximate_age=35)
        assert record.identity_type == "unknown"
        assert record.metadata["approximate_age"] == 35

    def test_link_birth_certificate(self):
        svc = IdentityGovernanceService()
        record = svc.register_citizen(full_name="Test", national_id="111111")
        svc.link_birth_certificate(record.health_number, "BC-2026-002")
        doc = record.get_document(IdentityDocumentType.BIRTH_CERTIFICATE)
        assert doc is not None
        assert doc.document_number == "BC-2026-002"

    def test_link_passport(self):
        svc = IdentityGovernanceService()
        record = svc.register_citizen(full_name="Test", national_id="222222")
        svc.link_passport(record.health_number, "PP-123456")
        assert record.get_document(IdentityDocumentType.PASSPORT) is not None

    def test_verify_document(self):
        svc = IdentityGovernanceService()
        record = svc.register_citizen(full_name="Test", national_id="333333")
        svc.verify_document(record.health_number, IdentityDocumentType.IRAQI_NATIONAL_ID, "admin")
        doc = record.get_document(IdentityDocumentType.IRAQI_NATIONAL_ID)
        assert doc.verification_status == DocumentVerificationStatus.VERIFIED
        assert doc.verified_by == "admin"

    def test_get_healthcare_view_no_national_id(self):
        svc = IdentityGovernanceService()
        record = svc.register_citizen(full_name="Safe", national_id="444444")
        view = svc.get_healthcare_view(record.health_number)
        assert "health_number" in view
        assert view.get("national_id_hash") is None
        assert "national_id" not in view


def test_registration_logs_are_redacted(caplog):
    svc = IdentityGovernanceService(nid_hmac_key="test-key")
    with caplog.at_level("INFO"):
        record = svc.register_citizen(
            full_name="Private Citizen",
            national_id="9876543210",
            gender="female",
        )
    messages = " ".join(caplog.messages)
    assert "Private Citizen" not in messages
    assert record.health_number not in messages
    assert "9876543210" not in messages
    assert record.history[0].get("national_id") is None
