from __future__ import annotations

import hashlib
import hmac
import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.identity.governance")


class IdentityDocumentType(Enum):
    IRAQI_NATIONAL_ID = "iraqi_national_id"
    HEALTH_NUMBER = "health_number"
    BIRTH_CERTIFICATE = "birth_certificate"
    PASSPORT = "passport"
    VISA = "visa"
    RESIDENCY = "residency"
    FAMILY_ID = "family_id"


class DocumentVerificationStatus(Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RelationshipType(Enum):
    GUARDIAN = "guardian"
    PARENT = "parent"
    CHILD = "child"
    SPOUSE = "spouse"
    SIBLING = "sibling"
    EMERGENCY_CONTACT = "emergency_contact"
    LEGAL_REPRESENTATIVE = "legal_representative"


@dataclass
class IdentityDocument:
    document_type: IdentityDocumentType
    document_number: str = ""
    issuing_authority: str = ""
    issuing_country: str = "IQ"
    issued_date: date | None = None
    expiry_date: date | None = None
    verification_status: DocumentVerificationStatus = DocumentVerificationStatus.UNVERIFIED
    verified_at: datetime | None = None
    verified_by: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.expiry_date is None:
            return False
        return date.today() > self.expiry_date


@dataclass
class IdentityRecord:
    id: str = ""
    health_number: str = ""
    national_id_hash: str = ""
    full_name: str = ""
    date_of_birth: date | None = None
    gender: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    documents: dict[str, IdentityDocument] = field(default_factory=dict)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    status: str = "active"
    identity_type: str = "citizen"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    def add_document(self, doc: IdentityDocument) -> None:
        self.documents[doc.document_type.value] = doc

    def get_document(self, doc_type: IdentityDocumentType) -> IdentityDocument | None:
        return self.documents.get(doc_type.value)

    def add_history_entry(self, entry: dict[str, Any]) -> None:
        entry["timestamp"] = entry.get("timestamp", datetime.now(UTC).isoformat())
        self.history.append(entry)

    def to_healthcare_view(self) -> dict[str, Any]:
        return {
            "health_number": self.health_number,
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "phone": self.phone,
            "email": self.email,
            "identity_type": self.identity_type,
            "status": self.status,
        }


class IdentityGovernanceService:
    def __init__(self, nid_hmac_key: str = ""):
        self._nid_hmac_key = nid_hmac_key
        self._records: dict[str, IdentityRecord] = {}
        self._health_index: dict[str, str] = {}
        self._nid_index: dict[str, str] = {}

    def register_citizen(
        self,
        full_name: str,
        national_id: str,
        date_of_birth: date | None = None,
        gender: str = "",
        phone: str = "",
        email: str = "",
        address: str = "",
    ) -> IdentityRecord:
        nid_hash = self._hash_national_id(national_id)
        existing = self._nid_index.get(nid_hash)
        if existing:
            raise ValueError("National ID already registered")

        health_number = self._generate_health_number(national_id)
        record = IdentityRecord(
            health_number=health_number,
            national_id_hash=nid_hash,
            full_name=full_name,
            date_of_birth=date_of_birth,
            gender=gender,
            phone=phone,
            email=email,
            address=address,
            identity_type="citizen",
        )
        record.add_document(
            IdentityDocument(
                document_type=IdentityDocumentType.IRAQI_NATIONAL_ID,
                document_number=national_id,
                issuing_authority="Iraq Ministry of Interior",
                issuing_country="IQ",
            )
        )
        record.add_history_entry({
            "action": "citizen_registered",
            "actor": "system",
            "description": "Citizen registered with National ID",
        })

        self._records[record.id] = record
        self._health_index[health_number] = record.id
        self._nid_index[nid_hash] = record.id
        logger.info("Citizen registered: %s (HN: %s)", full_name, health_number)
        return record

    def register_newborn(
        self,
        full_name: str,
        date_of_birth: date,
        gender: str,
        parent_national_id: str,
        birth_certificate_number: str = "",
    ) -> IdentityRecord:
        health_number = self._generate_health_number(str(uuid.uuid4()))
        record = IdentityRecord(
            health_number=health_number,
            full_name=full_name,
            date_of_birth=date_of_birth,
            gender=gender,
            identity_type="newborn",
        )
        if birth_certificate_number:
            record.add_document(
                IdentityDocument(
                    document_type=IdentityDocumentType.BIRTH_CERTIFICATE,
                    document_number=birth_certificate_number,
                    issuing_authority="Iraq Ministry of Health",
                )
            )
        record.add_history_entry({
            "action": "newborn_registered",
            "parent_national_id": self._hash_national_id(parent_national_id),
            "description": "Newborn registered via birth certificate",
        })

        self._records[record.id] = record
        self._health_index[health_number] = record.id
        logger.info("Newborn registered: %s (HN: %s)", full_name, health_number)
        return record

    def register_foreigner(
        self,
        full_name: str,
        passport_number: str,
        country_of_origin: str,
        date_of_birth: date | None = None,
        gender: str = "",
        visa_number: str = "",
    ) -> IdentityRecord:
        health_number = self._generate_health_number(passport_number)
        record = IdentityRecord(
            health_number=health_number,
            full_name=full_name,
            date_of_birth=date_of_birth,
            gender=gender,
            identity_type="foreigner",
        )
        record.add_document(
            IdentityDocument(
                document_type=IdentityDocumentType.PASSPORT,
                document_number=passport_number,
                issuing_authority=country_of_origin,
                issuing_country=country_of_origin,
            )
        )
        if visa_number:
            record.add_document(
                IdentityDocument(
                    document_type=IdentityDocumentType.VISA,
                    document_number=visa_number,
                    issuing_authority="Iraq Ministry of Interior",
                )
            )
        record.add_history_entry({
            "action": "foreigner_registered",
            "passport": passport_number,
            "country": country_of_origin,
            "description": "Foreigner registered with passport",
        })

        self._records[record.id] = record
        self._health_index[health_number] = record.id
        logger.info("Foreigner registered: %s (%s)", full_name, country_of_origin)
        return record

    def register_resident(
        self,
        full_name: str,
        residency_number: str,
        date_of_birth: date | None = None,
        gender: str = "",
        country_of_origin: str = "",
    ) -> IdentityRecord:
        health_number = self._generate_health_number(residency_number)
        record = IdentityRecord(
            health_number=health_number,
            full_name=full_name,
            date_of_birth=date_of_birth,
            gender=gender,
            identity_type="resident",
        )
        record.add_document(
            IdentityDocument(
                document_type=IdentityDocumentType.RESIDENCY,
                document_number=residency_number,
                issuing_authority="Iraq Ministry of Interior",
            )
        )
        record.add_history_entry({
            "action": "resident_registered",
            "residency": residency_number,
            "description": "Resident registered with residency document",
        })

        self._records[record.id] = record
        self._health_index[health_number] = record.id
        logger.info("Resident registered: %s", full_name)
        return record

    def register_visitor(
        self,
        full_name: str,
        passport_number: str,
        visa_number: str,
        country_of_origin: str,
        date_of_birth: date | None = None,
    ) -> IdentityRecord:
        health_number = self._generate_health_number(visa_number)
        record = IdentityRecord(
            health_number=health_number,
            full_name=full_name,
            date_of_birth=date_of_birth,
            identity_type="visitor",
        )
        record.add_document(
            IdentityDocument(
                document_type=IdentityDocumentType.PASSPORT,
                document_number=passport_number,
                issuing_authority=country_of_origin,
                issuing_country=country_of_origin,
            )
        )
        record.add_document(
            IdentityDocument(
                document_type=IdentityDocumentType.VISA,
                document_number=visa_number,
                issuing_authority="Iraq Ministry of Interior",
            )
        )
        record.add_history_entry({
            "action": "visitor_registered",
            "passport": passport_number,
            "visa": visa_number,
            "description": "Visitor registered with passport and visa",
        })

        self._records[record.id] = record
        self._health_index[health_number] = record.id
        logger.info("Visitor registered: %s", full_name)
        return record

    def register_unknown_patient(
        self,
        gender: str = "",
        approximate_age: int | None = None,
        presenting_complaint: str = "",
    ) -> IdentityRecord:
        health_number = self._generate_health_number(str(uuid.uuid4()))
        record = IdentityRecord(
            health_number=health_number,
            identity_type="unknown",
            metadata={
                "approximate_age": approximate_age,
                "presenting_complaint": presenting_complaint,
            },
        )
        record.add_history_entry({
            "action": "unknown_patient_registered",
            "description": "Unknown patient registered for emergency care",
        })

        self._records[record.id] = record
        self._health_index[health_number] = record.id
        logger.info("Unknown patient registered: %s", health_number)
        return record

    def link_birth_certificate(
        self, health_number: str, birth_certificate_number: str
    ) -> IdentityRecord:
        record = self._get_by_health_number(health_number)
        record.add_document(
            IdentityDocument(
                document_type=IdentityDocumentType.BIRTH_CERTIFICATE,
                document_number=birth_certificate_number,
                issuing_authority="Iraq Ministry of Health",
                verification_status=DocumentVerificationStatus.PENDING,
            )
        )
        record.add_history_entry({
            "action": "birth_certificate_linked",
            "birth_certificate": birth_certificate_number,
        })
        return record

    def link_passport(
        self, health_number: str, passport_number: str, issuing_country: str = "IQ"
    ) -> IdentityRecord:
        record = self._get_by_health_number(health_number)
        record.add_document(
            IdentityDocument(
                document_type=IdentityDocumentType.PASSPORT,
                document_number=passport_number,
                issuing_country=issuing_country,
            )
        )
        record.add_history_entry({
            "action": "passport_linked",
            "passport": passport_number,
        })
        return record

    def link_visa(
        self, health_number: str, visa_number: str
    ) -> IdentityRecord:
        record = self._get_by_health_number(health_number)
        record.add_document(
            IdentityDocument(
                document_type=IdentityDocumentType.VISA,
                document_number=visa_number,
                issuing_authority="Iraq Ministry of Interior",
            )
        )
        record.add_history_entry({
            "action": "visa_linked",
            "visa": visa_number,
        })
        return record

    def verify_document(
        self,
        health_number: str,
        doc_type: IdentityDocumentType,
        verified_by: str = "",
    ) -> IdentityRecord:
        record = self._get_by_health_number(health_number)
        doc = record.get_document(doc_type)
        if doc is None:
            raise ValueError(f"Document {doc_type.value} not found for {health_number}")
        doc.verification_status = DocumentVerificationStatus.VERIFIED
        doc.verified_at = datetime.now(UTC)
        doc.verified_by = verified_by
        record.add_history_entry({
            "action": "document_verified",
            "document_type": doc_type.value,
            "verified_by": verified_by,
        })
        return record

    def get_identity_history(self, health_number: str) -> list[dict[str, Any]]:
        record = self._get_by_health_number(health_number)
        return list(record.history)

    def get_identity_summary(self, health_number: str) -> dict[str, Any]:
        record = self._get_by_health_number(health_number)
        return {
            "health_number": record.health_number,
            "has_national_id": bool(record.national_id_hash),
            "identity_type": record.identity_type,
            "status": record.status,
            "document_count": len(record.documents),
            "relationship_count": len(record.relationships),
            "history_count": len(record.history),
            "documents": {
                dt: {
                    "status": doc.verification_status.value,
                    "issuing_country": doc.issuing_country,
                }
                for dt, doc in record.documents.items()
            },
        }

    def get_healthcare_view(self, health_number: str) -> dict[str, Any]:
        record = self._get_by_health_number(health_number)
        view = record.to_healthcare_view()
        view["documents"] = {
            dt: {"status": doc.verification_status.value}
            for dt, doc in record.documents.items()
        }
        return view

    def _hash_national_id(self, nid: str) -> str:
        if not nid or not self._nid_hmac_key:
            return hashlib.sha256(nid.encode()).hexdigest()
        return hmac.new(
            self._nid_hmac_key.encode(), nid.encode(), hashlib.sha256
        ).hexdigest()

    def _generate_health_number(self, seed: str) -> str:
        raw = (seed + str(uuid.uuid4())).encode()
        h = hashlib.sha256(raw).hexdigest()[:16].upper()
        return f"HN-{h[:8]}-{h[8:12]}-{h[12:16]}"

    def _get_by_health_number(self, health_number: str) -> IdentityRecord:
        record_id = self._health_index.get(health_number)
        if not record_id:
            raise ValueError(f"Identity not found: {health_number}")
        record = self._records.get(record_id)
        if not record:
            raise ValueError(f"Identity record not found: {health_number}")
        return record
