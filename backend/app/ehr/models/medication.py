from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SAEnum

from app._compat import UTC
from app.ehr.base import EHRBaseEntity
from app.ehr.enums import MedicationAdministrationStatus, MedicationOrderStatus


class MedicationStatement(EHRBaseEntity):
    __tablename__ = "ehr_medication_statements"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    medication_code = Column(String(50), nullable=True, index=True)
    medication_code_system = Column(String(20), nullable=True)
    medication_name = Column(String(300), nullable=False)
    medication_name_ar = Column(String(300), nullable=True)
    medication_brand = Column(String(200), nullable=True)
    medication_form = Column(String(100), nullable=True)

    strength_value = Column(String(50), nullable=True)
    strength_unit = Column(String(50), nullable=True)
    dosage_text = Column(String(300), nullable=True)

    route = Column(String(100), nullable=True)
    frequency = Column(String(200), nullable=True)
    timing = Column(JSON, nullable=True)

    status = Column(String(50), nullable=False, default="active")
    category = Column(String(50), nullable=True)

    date_started = Column(Date, nullable=True)
    date_ended = Column(Date, nullable=True)
    date_recorded = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=True)

    reason_code = Column(String(50), nullable=True)
    reason_description = Column(String(500), nullable=True)
    note = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_medstmt_patient", "patient_id", "status"),
        Index("ix_ehr_medstmt_citizen", "citizen_id"),
        Index("ix_ehr_medstmt_encounter", "encounter_id"),
        Index("ix_ehr_medstmt_medication", "medication_code"),
        Index("ix_ehr_medstmt_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )


class MedicationRequest(EHRBaseEntity):
    __tablename__ = "ehr_medication_requests"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    prescriber_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    medication_code = Column(String(50), nullable=True, index=True)
    medication_code_system = Column(String(20), nullable=True)
    medication_name = Column(String(300), nullable=False)
    medication_name_ar = Column(String(300), nullable=True)
    medication_brand = Column(String(200), nullable=True)
    medication_form = Column(String(100), nullable=True)

    status = Column(SAEnum(MedicationOrderStatus), nullable=False, default=MedicationOrderStatus.DRAFT)
    intent = Column(String(50), nullable=False, default="order")
    priority = Column(String(20), default="routine")
    category = Column(String(50), nullable=True)

    dosage_instruction = Column(Text, nullable=True)
    dosage_instructions = Column(JSON, nullable=True)
    route = Column(String(100), nullable=True)
    frequency = Column(String(200), nullable=True)
    quantity = Column(Integer, nullable=True)
    quantity_unit = Column(String(50), nullable=True)
    refills = Column(Integer, default=0)
    duration_days = Column(Integer, nullable=True)

    reason_code = Column(String(50), nullable=True)
    reason_description = Column(String(500), nullable=True)
    clinical_indication = Column(Text, nullable=True)

    authored_on = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    dispense_interval_days = Column(Integer, nullable=True)
    substitution_allowed = Column(Boolean, default=True)

    note = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_medreq_patient", "patient_id", "status"),
        Index("ix_ehr_medreq_citizen", "citizen_id"),
        Index("ix_ehr_medreq_encounter", "encounter_id"),
        Index("ix_ehr_medreq_prescriber", "prescriber_id"),
        Index("ix_ehr_medreq_medication", "medication_code"),
        Index("ix_ehr_medreq_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )


class MedicationDispense(EHRBaseEntity):
    __tablename__ = "ehr_medication_dispenses"

    medication_request_id = Column(String(26), ForeignKey("ehr_medication_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    # Cross-domain identifiers are enforced by the database migrations. The ORM
    # intentionally keeps them as scalar IDs because EHRBase and NationalBase
    # use separate SQLAlchemy metadata collections in the test/runtime harness.
    patient_id = Column(String(26), nullable=False, index=True)
    citizen_id = Column(String(26), nullable=True, index=True)
    dispenser_id = Column(String(26), nullable=True, index=True)

    medication_code = Column(String(50), nullable=True, index=True)
    medication_code_system = Column(String(20), nullable=True)
    medication_name = Column(String(300), nullable=False)
    medication_name_ar = Column(String(300), nullable=True)
    medication_brand = Column(String(200), nullable=True)
    medication_form = Column(String(100), nullable=True)

    status = Column(String(50), nullable=False, default="prepared")
    category = Column(String(50), nullable=True)
    quantity = Column(Integer, nullable=False)
    quantity_unit = Column(String(50), nullable=True)
    days_supply = Column(Integer, nullable=True)

    dosage_instruction = Column(Text, nullable=True)
    route = Column(String(100), nullable=True)
    frequency = Column(String(200), nullable=True)

    prepared_by = Column(String(26), nullable=True)
    prepared_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(26), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    dispensed_at = Column(DateTime(timezone=True), nullable=True)

    lot_number = Column(String(100), nullable=True)
    expiry_date = Column(Date, nullable=True)

    note = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_meddisp_patient", "patient_id"),
        Index("ix_ehr_meddisp_citizen", "citizen_id"),
        Index("ix_ehr_meddisp_request", "medication_request_id"),
        Index("ix_ehr_meddisp_medication", "medication_code"),
        Index("ix_ehr_meddisp_dispenser", "dispenser_id"),
        Index("ix_ehr_meddisp_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )


class MedicationAdministration(EHRBaseEntity):
    __tablename__ = "ehr_medication_administrations"

    medication_request_id = Column(String(26), ForeignKey("ehr_medication_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    administrator_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    medication_code = Column(String(50), nullable=True, index=True)
    medication_code_system = Column(String(20), nullable=True)
    medication_name = Column(String(300), nullable=False)
    medication_name_ar = Column(String(300), nullable=True)

    status = Column(SAEnum(MedicationAdministrationStatus), nullable=False, default=MedicationAdministrationStatus.COMPLETED)
    category = Column(String(50), nullable=True)

    dose_value = Column(String(50), nullable=True)
    dose_unit = Column(String(50), nullable=True)
    route = Column(String(100), nullable=True)
    site = Column(String(100), nullable=True)
    method = Column(String(100), nullable=True)

    administration_time = Column(DateTime(timezone=True), nullable=False)
    recorded_time = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=True)

    reason_not_given = Column(String(500), nullable=True)

    note = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_medadm_patient", "patient_id"),
        Index("ix_ehr_medadm_citizen", "citizen_id"),
        Index("ix_ehr_medadm_encounter", "encounter_id"),
        Index("ix_ehr_medadm_request", "medication_request_id"),
        Index("ix_ehr_medadm_medication", "medication_code"),
        Index("ix_ehr_medadm_admin", "administrator_id"),
        Index("ix_ehr_medadm_time", "administration_time"),
        Index("ix_ehr_medadm_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )
