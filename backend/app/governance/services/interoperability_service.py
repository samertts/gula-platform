from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from ..enums import InteropProtocolStatus, InteropProtocolType
from ..models.interoperability import (
    CanonicalMapping,
    InteropProtocol,
    MasterDataAgreement,
    TerminologyMapping,
)


class InteroperabilityGovernanceService:
    def __init__(self, db: Session):
        self.db = db

    def register_protocol(
        self,
        protocol_code: str,
        name_ar: str,
        protocol_type: InteropProtocolType,
        name_en: str | None = None,
        version: str = "1.0",
        specification_url: str | None = None,
        profile: str | None = None,
        implementation_guide: str | None = None,
        security_profile: str | None = None,
        is_mandatory: bool = False,
        effective_date: date | None = None,
    ) -> InteropProtocol:
        protocol = InteropProtocol(
            protocol_code=protocol_code,
            name_ar=name_ar,
            name_en=name_en,
            protocol_type=protocol_type,
            version=version,
            status=InteropProtocolStatus.ACTIVE,
            specification_url=specification_url,
            profile=profile,
            implementation_guide=implementation_guide,
            security_profile=security_profile,
            is_mandatory=is_mandatory,
            effective_date=effective_date or date.today(),
        )
        self.db.add(protocol)
        return protocol

    def get_protocol(self, protocol_code: str) -> InteropProtocol | None:
        return (
            self.db.query(InteropProtocol)
            .filter(InteropProtocol.protocol_code == protocol_code)
            .first()
        )

    def list_active_protocols(
        self,
        protocol_type: InteropProtocolType | None = None,
    ) -> list[InteropProtocol]:
        q = self.db.query(InteropProtocol).filter(
            InteropProtocol.status == InteropProtocolStatus.ACTIVE,
        )
        if protocol_type:
            q = q.filter(InteropProtocol.protocol_type == protocol_type)
        return q.order_by(InteropProtocol.protocol_code).all()

    def create_master_data_agreement(
        self,
        agreement_code: str,
        name_ar: str,
        domain: str,
        source_system: str,
        target_system: str,
        mapping_rules: dict[str, Any] | None = None,
        sync_frequency: str | None = None,
        conflict_resolution: str | None = None,
        effective_date: date | None = None,
    ) -> MasterDataAgreement:
        agreement = MasterDataAgreement(
            agreement_code=agreement_code,
            name_ar=name_ar,
            domain=domain,
            source_system=source_system,
            target_system=target_system,
            mapping_rules=mapping_rules,
            sync_frequency=sync_frequency,
            conflict_resolution=conflict_resolution,
            effective_date=effective_date or date.today(),
        )
        self.db.add(agreement)
        return agreement

    def create_terminology_mapping(
        self,
        source_system: str,
        source_code: str,
        target_system: str,
        target_code: str,
        source_display: str | None = None,
        target_display: str | None = None,
        mapping_type: str = "equivalent",
        equivalence: str = "equivalent",
    ) -> TerminologyMapping:
        mapping = TerminologyMapping(
            source_system=source_system,
            source_code=source_code,
            source_display=source_display,
            target_system=target_system,
            target_code=target_code,
            target_display=target_display,
            mapping_type=mapping_type,
            equivalence=equivalence,
        )
        self.db.add(mapping)
        return mapping

    def create_canonical_mapping(
        self,
        canonical_type: str,
        source_system: str,
        source_field: str,
        canonical_field: str,
        transformation: str | None = None,
        is_required: bool = False,
        data_type: str | None = None,
        validation_rules: dict[str, Any] | None = None,
    ) -> CanonicalMapping:
        mapping = CanonicalMapping(
            canonical_type=canonical_type,
            source_system=source_system,
            source_field=source_field,
            canonical_field=canonical_field,
            transformation=transformation,
            is_required=is_required,
            data_type=data_type,
            validation_rules=validation_rules,
        )
        self.db.add(mapping)
        return mapping

    def lookup_terminology(
        self,
        source_system: str,
        source_code: str,
    ) -> list[TerminologyMapping]:
        return (
            self.db.query(TerminologyMapping)
            .filter(
                TerminologyMapping.source_system == source_system,
                TerminologyMapping.source_code == source_code,
                TerminologyMapping.is_active.is_(True),
            )
            .all()
        )

    def get_canonical_mappings(self, canonical_type: str) -> list[CanonicalMapping]:
        return (
            self.db.query(CanonicalMapping)
            .filter(
                CanonicalMapping.canonical_type == canonical_type,
                CanonicalMapping.is_active.is_(True),
            )
            .all()
        )
