from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app._compat import UTC
from app.governance.base import GovernanceBase
from app.governance.models.health_number import HealthNumberAudit, MergedIdentityRecord
from app.governance.models.identity import GovernanceBreakGlassAccess, GovernanceIdentityRecord, MergeProposal
from app.governance.services.identity_persistence_service import (
    PersistedBreakGlassService,
    PersistedIdentityGovernanceService,
    PersistedIdentityMergeEngine,
)


@pytest.fixture()
def gov_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    GovernanceBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    session = Session(expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        GovernanceBase.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def svc(gov_db):
    return PersistedIdentityGovernanceService(gov_db, nid_hmac_key="test-hmac-key")


class TestPersistedIdentityGovernanceService:
    def test_register_citizen(self, svc):
        record = svc.register_citizen(
            full_name="Ali Ahmed",
            national_id="1234567890",
            date_of_birth=date(1990, 5, 15),
            gender="male",
            phone="+9647701234567",
            email="ali@example.com",
        )
        assert record.health_number.startswith("HN-")
        assert record.national_id_hash
        assert record.full_name == "Ali Ahmed"
        assert record.identity_type == "citizen"
        assert record.identity_status == "active"
        assert record.version == 1
        docs = record.documents_json or {}
        assert "iraqi_national_id" in docs
        history = record.history_json or []
        assert any(h["action"] == "citizen_registered" for h in history)

    def test_register_citizen_duplicate_nid_raises(self, svc):
        svc.register_citizen(full_name="First", national_id="9999999999")
        with pytest.raises(ValueError, match="already registered"):
            svc.register_citizen(full_name="Second", national_id="9999999999")

    def test_register_newborn(self, svc):
        record = svc.register_newborn(
            full_name="Baby Ali",
            date_of_birth=date.today(),
            gender="male",
            parent_national_id="1234567890",
            birth_certificate_number="BC-2026-001",
        )
        assert record.health_number.startswith("HN-")
        assert record.identity_type == "newborn"
        assert record.identity_status == "active"
        docs = record.documents_json or {}
        assert "birth_certificate" in docs
        assert docs["birth_certificate"]["document_number"] == "BC-2026-001"

    def test_register_foreigner(self, svc):
        record = svc.register_foreigner(
            full_name="John Smith",
            passport_number="AB123456",
            country_of_origin="US",
            date_of_birth=date(1985, 3, 20),
            gender="male",
            visa_number="V-2026-001",
        )
        assert record.identity_type == "foreigner"
        docs = record.documents_json or {}
        assert "passport" in docs
        assert "visa" in docs

    def test_register_unknown_patient(self, svc):
        record = svc.register_unknown_patient(
            gender="female",
            approximate_age=35,
            presenting_complaint="Chest pain",
        )
        assert record.identity_type == "unknown"
        assert record.identity_status == "pending_verification"
        meta = record.metadata_json or {}
        assert meta.get("approximate_age") == 35
        assert meta.get("presenting_complaint") == "Chest pain"
        assert record.full_name == "Unknown Patient"

    def test_link_document(self, svc):
        record = svc.register_citizen(full_name="Test", national_id="111111")
        updated = svc.link_document(
            record.health_number, "passport", "PP-123456",
            issuing_authority="Iraq MOI",
        )
        docs = updated.documents_json or {}
        assert "passport" in docs
        assert docs["passport"]["document_number"] == "PP-123456"
        assert updated.version > 1

    def test_link_document_nonexistent_health_number(self, svc):
        with pytest.raises(ValueError, match="not found"):
            svc.link_document("HN-NONEXISTENT", "passport", "PP-000")

    def test_link_document_optimistic_lock(self, svc):
        record = svc.register_citizen(full_name="Lock", national_id="222222")
        with pytest.raises(Exception, match="version"):
            svc.link_document(
                record.health_number, "passport", "PP-000", expected_version=99,
            )

    def test_verify_document(self, svc):
        record = svc.register_citizen(full_name="Verify", national_id="333333")
        updated = svc.verify_document(
            record.health_number, "iraqi_national_id", verified_by="admin",
        )
        docs = updated.documents_json or {}
        assert docs["iraqi_national_id"]["verification_status"] == "verified"
        assert docs["iraqi_national_id"]["verified_by"] == "admin"
        history = updated.history_json or []
        assert any(h["action"] == "document_verified" for h in history)

    def test_verify_nonexistent_document_type(self, svc):
        record = svc.register_citizen(full_name="DocCheck", national_id="444444")
        with pytest.raises(ValueError, match="not found"):
            svc.verify_document(record.health_number, "nonexistent_type", "admin")

    def test_get_identity_history(self, svc):
        record = svc.register_citizen(full_name="History", national_id="555555")
        svc.link_document(record.health_number, "passport", "PP-999")
        svc.verify_document(record.health_number, "iraqi_national_id", "admin")
        history = svc.get_identity_history(record.health_number)
        assert len(history) == 3
        actions = [h["action"] for h in history]
        assert "citizen_registered" in actions
        assert "passport_linked" in actions
        assert "document_verified" in actions

    def test_get_identity_summary(self, svc):
        record = svc.register_citizen(full_name="Summary", national_id="666666")
        summary = svc.get_identity_summary(record.health_number)
        assert summary["health_number"] == record.health_number
        assert summary["has_national_id"] is True
        assert summary["identity_type"] == "citizen"
        assert summary["status"] == "active"
        assert summary["document_count"] >= 1
        assert summary["history_count"] >= 1

    def test_get_healthcare_view(self, svc):
        record = svc.register_citizen(
            full_name="ViewTest", national_id="777777",
            date_of_birth=date(2000, 1, 1), gender="female",
            phone="+964000000000", email="view@test.com",
        )
        view = svc.get_healthcare_view(record.health_number)
        assert view["health_number"] == record.health_number
        assert view["full_name"] == "ViewTest"
        assert view["date_of_birth"] is not None
        assert view["gender"] == "female"
        assert "national_id" not in view

    def test_search_by_name(self, svc):
        svc.register_citizen(full_name="Unique Name For Search", national_id="888881")
        svc.register_citizen(full_name="Other Person", national_id="888882")
        results = svc.search("Unique Name")
        assert len(results) >= 1
        assert any("Unique Name For Search" in r.full_name for r in results)

    def test_search_by_health_number(self, svc):
        record = svc.register_citizen(full_name="SearchHN", national_id="999991")
        results = svc.search(record.health_number[:8])
        assert any(r.health_number == record.health_number for r in results)

    def test_empty_search_returns_all(self, svc):
        svc.register_citizen(full_name="A", national_id="111110")
        svc.register_citizen(full_name="B", national_id="111111")
        results = svc.search("")
        assert len(results) >= 2


class TestPersistedBreakGlassService:
    @pytest.fixture()
    def glass(self, gov_db):
        return PersistedBreakGlassService(gov_db)

    def test_request_access(self, glass):
        access = glass.request_access(
            user_id="user-1", user_name="Dr. Ali", user_role="physician",
            reason="emergency", reason_detail="Patient critical",
            resource_type="patient_record", resource_id="patient-123",
            patient_id="patient-123", duration_minutes=60,
        )
        assert access.is_active is True
        assert access.user_id == "user-1"
        assert access.user_name == "Dr. Ali"
        assert access.reason == "emergency"
        assert access.version == 1

    def test_revoke_access(self, glass):
        access = glass.request_access(
            user_id="user-2", user_name="Dr. Sara", user_role="physician",
            reason="emergency",
        )
        glass.revoke_access(access.id, reviewer="admin", notes="Resolved")
        assert access.is_active is False
        assert access.reviewed_by == "admin"
        assert access.version == 2

    def test_is_access_valid_true(self, glass):
        access = glass.request_access(
            user_id="user-3", user_name="Dr. Test", user_role="nurse",
            reason="break_glass",
        )
        assert glass.is_access_valid(access.id) is True

    def test_is_access_valid_revoked(self, glass):
        access = glass.request_access(
            user_id="user-4", user_name="Dr. Revoked", user_role="physician",
            reason="emergency",
        )
        glass.revoke_access(access.id)
        assert glass.is_access_valid(access.id) is False

    def test_is_access_valid_expired(self, glass):
        access = glass.request_access(
            user_id="user-5", user_name="Dr. Expired", user_role="physician",
            reason="emergency", duration_minutes=0,
        )
        import time
        access.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        glass._db.commit()
        assert glass.is_access_valid(access.id) is False

    def test_get_active_accesses(self, glass):
        glass.request_access(user_id="u1", user_name="A", user_role="r", reason="emergency")
        glass.request_access(user_id="u2", user_name="B", user_role="r", reason="emergency")
        all_active = glass.get_active_accesses()
        assert len(all_active) >= 2
        user1_active = glass.get_active_accesses(user_id="u1")
        assert len(user1_active) >= 1
        assert all(a.user_id == "u1" for a in user1_active)

    def test_expire_stale(self, glass, gov_db):
        access = glass.request_access(
            user_id="u-stale", user_name="Stale", user_role="r",
            reason="emergency", duration_minutes=0,
        )
        access.expires_at = datetime.now(UTC) - timedelta(hours=1)
        gov_db.commit()
        count = glass.expire_stale()
        assert count >= 1


class TestPersistedIdentityMergeEngine:
    @pytest.fixture()
    def engine(self, svc, gov_db):
        return PersistedIdentityMergeEngine(gov_db, svc)

    def test_calculate_confidence_exact_nid_match(self, svc, engine):
        p = svc.register_citizen(full_name="Primary", national_id="MERGE001")
        d = svc.register_citizen(full_name="Primary", national_id="MERGE002")
        d.national_id_hash = p.national_id_hash
        svc._db.commit()
        score = engine.calculate_confidence(p.health_number, d.health_number)
        assert score >= 0.5

    def test_calculate_confidence_no_match(self, svc, engine):
        p = svc.register_citizen(full_name="Person A", national_id="NID-A")
        d = svc.register_citizen(full_name="Person B", national_id="NID-B")
        score = engine.calculate_confidence(p.health_number, d.health_number)
        assert score < 0.5

    def test_calculate_confidence_name_and_dob_match(self, svc, engine):
        p = svc.register_citizen(
            full_name="Muhammad Ali", national_id="SIM-A",
            date_of_birth=date(1990, 1, 1), phone="+964000000001",
        )
        d = svc.register_citizen(
            full_name="Muhammad Ali", national_id="SIM-B",
            date_of_birth=date(1990, 1, 1), phone="+964000000001",
        )
        score = engine.calculate_confidence(p.health_number, d.health_number)
        assert score > 0.4

    def test_propose_merge_above_threshold(self, svc, engine):
        p = svc.register_citizen(full_name="Merge Person", national_id="MERGE-P")
        d = svc.register_unknown_patient(gender="male", approximate_age=30)
        d.full_name = "Merge Person"
        d.date_of_birth = p.date_of_birth
        d.national_id_hash = p.national_id_hash
        svc._db.commit()
        proposal = engine.propose_merge(p.health_number, d.health_number)
        assert proposal is not None
        assert proposal.status == "pending"
        assert proposal.primary_hn == p.health_number
        assert proposal.duplicate_hn == d.health_number

    def test_propose_merge_below_threshold(self, svc, engine):
        p = svc.register_citizen(full_name="Alpha", national_id="THR-P")
        d = svc.register_citizen(full_name="Beta", national_id="THR-D")
        proposal = engine.propose_merge(p.health_number, d.health_number)
        assert proposal is None

    def test_propose_merge_returns_existing_pending(self, svc, engine):
        p = svc.register_citizen(full_name="Dupe Person", national_id="DUP-P")
        d = svc.register_unknown_patient(gender="male")
        d.full_name = "Dupe Person"
        d.national_id_hash = p.national_id_hash
        svc._db.commit()
        first = engine.propose_merge(p.health_number, d.health_number)
        second = engine.propose_merge(p.health_number, d.health_number)
        assert second is not None
        assert second.proposal_key == first.proposal_key

    def test_approve_merge(self, svc, engine):
        p = svc.register_citizen(full_name="Approved Person", national_id="APP-P")
        d = svc.register_unknown_patient(gender="male")
        d.full_name = "Approved Person"
        d.national_id_hash = p.national_id_hash
        svc._db.commit()
        proposal = engine.propose_merge(p.health_number, d.health_number)
        approved = engine.approve_merge(proposal.proposal_key, reviewed_by="admin", reason="Duplicate")
        assert approved.status == "approved"
        assert approved.reviewed_by == "admin"
        dup = svc._repo.get_by_health_number(d.health_number)
        assert dup.identity_status == "merged"

    def test_reject_merge(self, svc, engine):
        p = svc.register_citizen(full_name="Rejected Person", national_id="REJ-P")
        d = svc.register_unknown_patient(gender="male")
        d.full_name = "Rejected Person"
        d.national_id_hash = p.national_id_hash
        svc._db.commit()
        proposal = engine.propose_merge(p.health_number, d.health_number)
        rejected = engine.reject_merge(proposal.proposal_key, notes="Not a duplicate")
        assert rejected.status == "rejected"
        assert rejected.notes == "Not a duplicate"

    def test_get_proposal(self, svc, engine):
        p = svc.register_citizen(full_name="GetProp Person", national_id="GET-P")
        d = svc.register_unknown_patient(gender="male")
        d.full_name = "GetProp Person"
        d.national_id_hash = p.national_id_hash
        svc._db.commit()
        engine.propose_merge(p.health_number, d.health_number)
        found = engine.get_proposal(p.health_number, d.health_number)
        assert found is not None
        assert found.primary_hn == p.health_number

    def test_get_proposal_not_found(self, svc, engine):
        p = svc.register_citizen(full_name="NF-A", national_id="NF-A")
        d = svc.register_citizen(full_name="NF-B", national_id="NF-B")
        assert engine.get_proposal(p.health_number, d.health_number) is None

    def test_list_pending_proposals(self, svc, engine):
        p = svc.register_citizen(full_name="List Person", national_id="LST-A")
        d = svc.register_unknown_patient(gender="male")
        d.full_name = "List Person"
        d.national_id_hash = p.national_id_hash
        svc._db.commit()
        engine.propose_merge(p.health_number, d.health_number)
        pending = engine.list_pending_proposals()
        assert len(pending) >= 1

    def test_approve_nonexistent_proposal(self, engine):
        with pytest.raises(ValueError, match="not found"):
            engine.approve_merge("nonexistent:key")
