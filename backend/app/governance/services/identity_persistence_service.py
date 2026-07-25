from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.governance.models.health_number import MergedIdentityRecord
from app.governance.models.identity import (
    GovernanceBreakGlassAccess,
    GovernanceIdentityRecord,
    MergeProposal,
)
from app.governance.repositories.base import OptimisticLockError
from app.governance.repositories.break_glass_repository import BreakGlassAccessRepository
from app.governance.repositories.identity_repository import IdentityRecordRepository
from app.governance.repositories.merge_repository import (
    MergedIdentityRecordRepository,
    MergeProposalRepository,
)

PERSISTED_IDENTITY_VERSION = 1


class PersistedIdentityGovernanceService:
    def __init__(self, db: Session, nid_hmac_key: str = ""):
        self._db = db
        self._repo = IdentityRecordRepository(db)
        self._nid_hmac_key = nid_hmac_key

    def register_citizen(
        self,
        full_name: str,
        national_id: str,
        date_of_birth: date | None = None,
        gender: str = "",
        phone: str = "",
        email: str = "",
        address: str = "",
    ) -> GovernanceIdentityRecord:
        nid_hash = self._hash_national_id(national_id)
        existing = self._repo.get_by_national_id_hash(nid_hash)
        if existing:
            raise ValueError("National ID already registered")
        health_number = self._generate_health_number(national_id)
        record = GovernanceIdentityRecord(
            id=str(uuid.uuid4()),
            health_number=health_number,
            national_id_hash=nid_hash,
            full_name=full_name,
            date_of_birth=date_of_birth
            if isinstance(date_of_birth, datetime)
            else (datetime.combine(date_of_birth, datetime.min.time()) if date_of_birth else None),
            gender=gender,
            phone=phone,
            email=email,
            address=address,
            identity_type="citizen",
            identity_status="active",
            version=1,
            documents_json={
                "iraqi_national_id": {
                    "document_number": national_id,
                    "issuing_authority": "Iraq Ministry of Interior",
                    "issuing_country": "IQ",
                    "verification_status": "unverified",
                },
            },
            history_json=[
                {
                    "action": "citizen_registered",
                    "actor": "system",
                    "description": "Citizen registered with National ID",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ],
        )
        self._repo.add(record)
        self._db.commit()
        return record

    def register_newborn(
        self,
        full_name: str,
        date_of_birth: date,
        gender: str,
        parent_national_id: str,
        birth_certificate_number: str = "",
    ) -> GovernanceIdentityRecord:
        health_number = self._generate_health_number(str(uuid.uuid4()))
        documents = {}
        if birth_certificate_number:
            documents["birth_certificate"] = {
                "document_number": birth_certificate_number,
                "issuing_authority": "Iraq Ministry of Health",
                "verification_status": "unverified",
            }
        record = GovernanceIdentityRecord(
            id=str(uuid.uuid4()),
            health_number=health_number,
            full_name=full_name,
            date_of_birth=datetime.combine(date_of_birth, datetime.min.time()),
            gender=gender,
            identity_type="newborn",
            identity_status="active",
            version=1,
            documents_json=documents or None,
            history_json=[
                {
                    "action": "newborn_registered",
                    "parent_national_id": self._hash_national_id(parent_national_id),
                    "description": "Newborn registered via birth certificate",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ],
        )
        self._repo.add(record)
        self._db.commit()
        return record

    def register_foreigner(
        self,
        full_name: str,
        passport_number: str,
        country_of_origin: str,
        date_of_birth: date | None = None,
        gender: str = "",
        visa_number: str = "",
    ) -> GovernanceIdentityRecord:
        health_number = self._generate_health_number(passport_number)
        documents = {
            "passport": {
                "document_number": passport_number,
                "issuing_authority": country_of_origin,
                "issuing_country": country_of_origin,
                "verification_status": "unverified",
            },
        }
        if visa_number:
            documents["visa"] = {
                "document_number": visa_number,
                "issuing_authority": "Iraq Ministry of Interior",
                "verification_status": "unverified",
            }
        record = GovernanceIdentityRecord(
            id=str(uuid.uuid4()),
            health_number=health_number,
            full_name=full_name,
            date_of_birth=datetime.combine(date_of_birth, datetime.min.time())
            if date_of_birth
            else None,
            gender=gender,
            identity_type="foreigner",
            identity_status="active",
            version=1,
            documents_json=documents,
            history_json=[
                {
                    "action": "foreigner_registered",
                    "passport": passport_number,
                    "country": country_of_origin,
                    "description": "Foreigner registered with passport",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ],
        )
        self._repo.add(record)
        self._db.commit()
        return record

    def register_unknown_patient(
        self,
        gender: str = "",
        approximate_age: int | None = None,
        presenting_complaint: str = "",
    ) -> GovernanceIdentityRecord:
        health_number = self._generate_health_number(str(uuid.uuid4()))
        record = GovernanceIdentityRecord(
            id=str(uuid.uuid4()),
            health_number=health_number,
            full_name="Unknown Patient",
            gender=gender,
            identity_type="unknown",
            identity_status="pending_verification",
            version=1,
            metadata_json={
                "approximate_age": approximate_age,
                "presenting_complaint": presenting_complaint,
            },
            history_json=[
                {
                    "action": "unknown_patient_registered",
                    "description": "Unknown patient registered for emergency care",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ],
        )
        self._repo.add(record)
        self._db.commit()
        return record

    def link_document(
        self,
        health_number: str,
        doc_type: str,
        doc_number: str,
        issuing_authority: str = "",
        expected_version: int | None = None,
    ) -> GovernanceIdentityRecord:
        record = self._repo.get_by_health_number(health_number)
        if not record:
            raise ValueError(f"Identity not found: {health_number}")
        if expected_version is not None and record.version != expected_version:
            raise OptimisticLockError(
                f"GovernanceIdentityRecord {record.id} version {record.version} != expected {expected_version}",
            )
        docs = record.documents_json or {}
        docs[doc_type] = {
            "document_number": doc_number,
            "issuing_authority": issuing_authority,
            "verification_status": "unverified",
        }
        record.documents_json = docs
        history = record.history_json or []
        history.append(
            {
                "action": f"{doc_type}_linked",
                "document_type": doc_type,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        record.history_json = history
        record.version += 1
        self._repo.update(record)
        self._db.commit()
        return record

    def verify_document(
        self,
        health_number: str,
        doc_type: str,
        verified_by: str = "",
        expected_version: int | None = None,
    ) -> GovernanceIdentityRecord:
        record = self._repo.get_by_health_number(health_number)
        if not record:
            raise ValueError(f"Identity not found: {health_number}")
        if expected_version is not None and record.version != expected_version:
            raise OptimisticLockError(
                f"GovernanceIdentityRecord {record.id} version {record.version} != expected {expected_version}",
            )
        docs = record.documents_json or {}
        if doc_type not in docs:
            raise ValueError(f"Document {doc_type} not found for {health_number}")
        docs[doc_type]["verification_status"] = "verified"
        docs[doc_type]["verified_at"] = datetime.now(UTC).isoformat()
        docs[doc_type]["verified_by"] = verified_by
        record.documents_json = docs
        history = record.history_json or []
        history.append(
            {
                "action": "document_verified",
                "document_type": doc_type,
                "verified_by": verified_by,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        record.history_json = history
        record.version += 1
        self._repo.update(record)
        self._db.commit()
        return record

    def get_identity_history(self, health_number: str) -> list[dict[str, Any]]:
        record = self._repo.get_by_health_number(health_number)
        if not record:
            raise ValueError(f"Identity not found: {health_number}")
        return record.history_json or []

    def get_identity_summary(self, health_number: str) -> dict[str, Any]:
        record = self._repo.get_by_health_number(health_number)
        if not record:
            raise ValueError(f"Identity not found: {health_number}")
        docs = record.documents_json or {}
        history = record.history_json or []
        return {
            "health_number": record.health_number,
            "has_national_id": bool(record.national_id_hash),
            "identity_type": record.identity_type,
            "status": record.identity_status,
            "document_count": len(docs),
            "history_count": len(history),
            "documents": {
                dt: {"status": d.get("verification_status", "unknown")} for dt, d in docs.items()
            },
        }

    def get_healthcare_view(self, health_number: str) -> dict[str, Any]:
        record = self._repo.get_by_health_number(health_number)
        if not record:
            raise ValueError(f"Identity not found: {health_number}")
        docs = record.documents_json or {}
        return {
            "health_number": record.health_number,
            "full_name": record.full_name,
            "date_of_birth": record.date_of_birth.isoformat() if record.date_of_birth else None,
            "gender": record.gender,
            "phone": record.phone,
            "email": record.email,
            "identity_type": record.identity_type,
            "status": record.identity_status,
            "documents": {
                dt: {"status": d.get("verification_status", "unknown")} for dt, d in docs.items()
            },
        }

    def search(self, query: str, skip: int = 0, limit: int = 20) -> list[GovernanceIdentityRecord]:
        return self._repo.search(query, skip=skip, limit=limit)

    def _hash_national_id(self, nid: str) -> str:
        if not nid or not self._nid_hmac_key:
            return hashlib.sha256(nid.encode()).hexdigest()
        return hmac.new(self._nid_hmac_key.encode(), nid.encode(), hashlib.sha256).hexdigest()

    def _generate_health_number(self, seed: str) -> str:
        raw = (seed + str(uuid.uuid4())).encode()
        h = hashlib.sha256(raw).hexdigest()[:16].upper()
        return f"HN-{h[:8]}-{h[8:12]}-{h[12:16]}"


class PersistedBreakGlassService:
    def __init__(self, db: Session):
        self._repo = BreakGlassAccessRepository(db)
        self._db = db

    def request_access(
        self,
        user_id: str,
        user_name: str,
        user_role: str,
        reason: str,
        reason_detail: str = "",
        resource_type: str = "",
        resource_id: str = "",
        patient_id: str = "",
        duration_minutes: int = 60,
    ) -> GovernanceBreakGlassAccess:
        access = GovernanceBreakGlassAccess(
            id=str(uuid.uuid4()),
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            reason=reason,
            reason_detail=reason_detail,
            resource_type=resource_type,
            resource_id=resource_id,
            patient_id=patient_id,
            version=1,
            accessed_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=duration_minutes),
            is_active=True,
        )
        self._repo.add(access)
        self._db.commit()
        return access

    def revoke_access(self, access_id: str, reviewer: str = "", notes: str | None = None) -> None:
        access = self._repo.get(access_id)
        if access:
            access.is_active = False
            access.reviewed_by = reviewer
            access.reviewed_at = datetime.now(UTC)
            access.review_notes = notes
            access.version += 1
            self._repo.update(access)
            self._db.commit()

    def is_access_valid(self, access_id: str) -> bool:
        access = self._repo.get_active(access_id)
        if not access:
            return False
        if access.expires_at and access.expires_at < datetime.now(UTC):
            access.is_active = False
            access.version += 1
            self._db.commit()
            return False
        return True

    def get_active_accesses(self, user_id: str | None = None) -> list[GovernanceBreakGlassAccess]:
        return self._repo.list_active(user_id=user_id)

    def expire_stale(self) -> int:
        return self._repo.expire_stale()


class PersistedIdentityMergeEngine:
    def __init__(self, db: Session, identity_service: PersistedIdentityGovernanceService):
        self._db = db
        self._proposal_repo = MergeProposalRepository(db)
        self._merge_repo = MergedIdentityRecordRepository(db)
        self._identity = identity_service

    def calculate_confidence(self, primary_hn: str, duplicate_hn: str) -> float:
        primary = self._identity._repo.get_by_health_number(primary_hn)
        duplicate = self._identity._repo.get_by_health_number(duplicate_hn)
        if not primary or not duplicate:
            raise ValueError(f"Identity not found: {primary_hn if not primary else duplicate_hn}")
        score = 0.0
        if primary.national_id_hash and primary.national_id_hash == duplicate.national_id_hash:
            score += 0.5
        if primary.full_name and duplicate.full_name:
            from difflib import SequenceMatcher

            ratio = SequenceMatcher(
                None, primary.full_name.lower(), duplicate.full_name.lower()
            ).ratio()
            if ratio > 0.9:
                score += 0.2
        if (
            primary.date_of_birth
            and duplicate.date_of_birth
            and primary.date_of_birth == duplicate.date_of_birth
        ):
            score += 0.15
        if primary.phone and duplicate.phone and primary.phone == duplicate.phone:
            score += 0.1
        return min(score, 1.0)

    def propose_merge(
        self, primary_hn: str, duplicate_hn: str, confidence_threshold: float = 0.6
    ) -> MergeProposal | None:
        confidence = self.calculate_confidence(primary_hn, duplicate_hn)
        if confidence < confidence_threshold:
            return None
        proposal_key = f"{primary_hn}:{duplicate_hn}"
        existing = self._proposal_repo.get_by_key(proposal_key)
        if existing and existing.status == "pending":
            return existing
        proposal = MergeProposal(
            proposal_key=proposal_key,
            primary_hn=primary_hn,
            duplicate_hn=duplicate_hn,
            confidence_score=confidence,
            status="pending",
            version=1,
        )
        self._proposal_repo.add(proposal)
        self._db.commit()
        return proposal

    def approve_merge(
        self, proposal_key: str, reviewed_by: str = "", reason: str = ""
    ) -> MergeProposal:
        proposal = self._proposal_repo.get_by_key(proposal_key)
        if not proposal:
            raise ValueError(f"Merge proposal not found: {proposal_key}")
        primary = self._identity._repo.get_by_health_number(proposal.primary_hn)
        duplicate = self._identity._repo.get_by_health_number(proposal.duplicate_hn)
        if not primary or not duplicate:
            raise ValueError("Primary or duplicate identity not found")
        duplicate.identity_status = "merged"
        duplicate.version += 1
        dh = duplicate.history_json or []
        dh.append(
            {
                "action": "identity_merged",
                "merged_into": proposal.primary_hn,
                "confidence": proposal.confidence_score,
                "reviewed_by": reviewed_by,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        duplicate.history_json = dh
        ph = primary.history_json or []
        ph.append(
            {
                "action": "received_merged_identity",
                "merged_from": proposal.duplicate_hn,
                "confidence": proposal.confidence_score,
            }
        )
        primary.history_json = ph
        primary.version += 1
        merge_rec = MergedIdentityRecord(
            primary_health_number=proposal.primary_hn,
            secondary_health_number=proposal.duplicate_hn,
            primary_citizen_ulid=primary.id,
            secondary_citizen_ulid=duplicate.id,
            action="merged",
            reason=reason,
            decision_by=reviewed_by,
        )
        self._merge_repo.add(merge_rec)
        proposal.status = "approved"
        proposal.resolved_at = datetime.now(UTC)
        proposal.reviewed_by = reviewed_by
        proposal.version += 1
        self._db.commit()
        return proposal

    def reject_merge(self, proposal_key: str, notes: str = "") -> MergeProposal:
        proposal = self._proposal_repo.get_by_key(proposal_key)
        if not proposal:
            raise ValueError(f"Merge proposal not found: {proposal_key}")
        proposal.status = "rejected"
        proposal.resolved_at = datetime.now(UTC)
        proposal.notes = notes
        proposal.version += 1
        self._db.commit()
        return proposal

    def get_proposal(self, primary_hn: str, duplicate_hn: str) -> MergeProposal | None:
        return self._proposal_repo.get_by_key(f"{primary_hn}:{duplicate_hn}")

    def list_pending_proposals(self) -> list[MergeProposal]:
        return self._proposal_repo.list_pending()
