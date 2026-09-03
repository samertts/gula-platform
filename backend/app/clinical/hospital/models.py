from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


def _core_id() -> str:
    return uuid.uuid4().hex.upper()[:26]


def _now() -> datetime:
    return datetime.now(UTC)


class CoreHospitalFacility(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_facilities"

    id = Column(String(26), primary_key=True, default=_core_id)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, unique=True, index=True)
    name = Column(String(240), nullable=False)
    status = Column(String(24), nullable=False, default="ACTIVE", index=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','INACTIVE','SUSPENDED')", name="ck_core_hospital_facility_status"),
        CheckConstraint("version > 0", name="ck_core_hospital_facility_version"),
        UniqueConstraint("organization_id", "facility_id", name="uq_core_hospital_facility_scope"),
    )


class CoreHospitalWard(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_wards"

    id = Column(String(26), primary_key=True, default=_core_id)
    facility_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    department_id = Column(String(26), nullable=True, index=True)
    code = Column(String(80), nullable=False)
    name = Column(String(240), nullable=False)
    status = Column(String(24), nullable=False, default="ACTIVE", index=True)
    capacity = Column(Integer, nullable=False, default=0)
    metadata_ = Column("metadata", JSON, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("facility_id", "code", name="uq_core_hospital_ward_facility_code"),
        CheckConstraint("capacity >= 0", name="ck_core_hospital_ward_capacity"),
        CheckConstraint("status IN ('ACTIVE','INACTIVE','CLOSED')", name="ck_core_hospital_ward_status"),
        CheckConstraint("version > 0", name="ck_core_hospital_ward_version"),
        Index("ix_core_hospital_ward_scope_status", "organization_id", "facility_id", "status"),
    )


class CoreHospitalRoom(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_rooms"

    id = Column(String(26), primary_key=True, default=_core_id)
    ward_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    code = Column(String(80), nullable=False)
    name = Column(String(240), nullable=False)
    capacity = Column(Integer, nullable=False, default=1)
    status = Column(String(24), nullable=False, default="ACTIVE", index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("ward_id", "code", name="uq_core_hospital_room_ward_code"),
        CheckConstraint("capacity > 0", name="ck_core_hospital_room_capacity"),
        CheckConstraint("status IN ('ACTIVE','INACTIVE','CLOSED')", name="ck_core_hospital_room_status"),
    )


class CoreHospitalBed(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_beds"

    id = Column(String(26), primary_key=True, default=_core_id)
    room_id = Column(String(26), nullable=False, index=True)
    ward_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    code = Column(String(80), nullable=False)
    bed_type = Column(String(48), nullable=False, default="STANDARD")
    status = Column(String(24), nullable=False, default="AVAILABLE", index=True)
    version = Column(Integer, nullable=False, default=1)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("room_id", "code", name="uq_core_hospital_bed_room_code"),
        CheckConstraint("status IN ('AVAILABLE','RESERVED','OCCUPIED','CLEANING','MAINTENANCE','BLOCKED')", name="ck_core_hospital_bed_status"),
        CheckConstraint("version > 0", name="ck_core_hospital_bed_version"),
        Index("ix_core_hospital_bed_board", "organization_id", "facility_id", "ward_id", "status"),
    )


class CoreAdmission(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_admissions"

    id = Column(String(26), primary_key=True, default=_core_id)
    admission_request_id = Column(String(64), nullable=False, unique=True, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    encounter_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    ward_id = Column(String(26), nullable=False, index=True)
    admitting_provider_account_id = Column(String(26), nullable=False, index=True)
    admission_reason = Column(Text, nullable=False)
    admission_type = Column(String(24), nullable=False, default="ELECTIVE")
    status = Column(String(32), nullable=False, default="REQUESTED", index=True)
    version = Column(Integer, nullable=False, default=1)
    requested_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    admitted_at = Column(DateTime(timezone=True), nullable=True)
    discharged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("admission_type IN ('EMERGENCY','ELECTIVE','TRANSFER','OBSERVATION')", name="ck_core_admission_type"),
        CheckConstraint("status IN ('REQUESTED','ACCEPTED','ADMITTED','IN_CARE','DISCHARGE_PLANNED','DISCHARGED','CANCELLED','REJECTED','TRANSFERRED')", name="ck_core_admission_status"),
        CheckConstraint("version > 0", name="ck_core_admission_version"),
        Index("ix_core_admission_patient_time", "patient_person_id", "created_at"),
        Index("ix_core_admission_scope_status", "organization_id", "facility_id", "ward_id", "status"),
    )


class CoreBedAllocation(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_bed_allocations"

    id = Column(String(26), primary_key=True, default=_core_id)
    admission_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    bed_id = Column(String(26), nullable=False, index=True)
    ward_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    allocated_by_account_id = Column(String(26), nullable=False, index=True)
    allocated_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    released_at = Column(DateTime(timezone=True), nullable=True)
    release_reason = Column(String(500), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("version > 0", name="ck_core_bed_allocation_version"),
        Index("ix_core_bed_allocation_active_bed", "bed_id", "released_at"),
        Index("ix_core_bed_allocation_active_patient", "patient_person_id", "released_at"),
    )


class CoreCareTeamMember(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_care_team_members"

    id = Column(String(26), primary_key=True, default=_core_id)
    admission_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    account_id = Column(String(26), nullable=False, index=True)
    role = Column(String(40), nullable=False)
    scope = Column(String(240), nullable=False)
    purpose = Column(String(120), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(24), nullable=False, default="ACTIVE", index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','ENDED','REVOKED')", name="ck_core_care_team_status"),
        CheckConstraint("version > 0", name="ck_core_care_team_version"),
        Index("ix_core_care_team_patient_active", "patient_person_id", "status"),
    )


class CoreNursingTask(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_nursing_tasks"

    id = Column(String(26), primary_key=True, default=_core_id)
    admission_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    ward_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    task_type = Column(String(80), nullable=False)
    instructions = Column(Text, nullable=True)
    status = Column(String(24), nullable=False, default="OPEN", index=True)
    assigned_to_account_id = Column(String(26), nullable=True, index=True)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_note = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('OPEN','CLAIMED','IN_PROGRESS','COMPLETED','CANCELLED','DEFERRED')", name="ck_core_nursing_task_status"),
        CheckConstraint("version > 0", name="ck_core_nursing_task_version"),
        Index("ix_core_nursing_task_board", "organization_id", "facility_id", "ward_id", "status"),
    )


class CoreVitalObservation(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_vital_observations"

    id = Column(String(26), primary_key=True, default=_core_id)
    patient_person_id = Column(String(26), nullable=False, index=True)
    encounter_id = Column(String(26), nullable=False, index=True)
    admission_id = Column(String(26), nullable=True, index=True)
    observer_account_id = Column(String(26), nullable=False, index=True)
    device_reference = Column(String(160), nullable=True)
    vital_type = Column(String(64), nullable=False, index=True)
    value_numeric = Column(String(64), nullable=False)
    unit = Column(String(40), nullable=False)
    method = Column(String(80), nullable=False)
    source = Column(String(80), nullable=False, default="MANUAL")
    observed_at = Column(DateTime(timezone=True), nullable=False)
    validation_status = Column(String(24), nullable=False, default="VALID")
    warning_code = Column(String(80), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("validation_status IN ('VALID','WARNING','REJECTED')", name="ck_core_vital_validation_status"),
        CheckConstraint("version > 0", name="ck_core_vital_version"),
        Index("ix_core_vital_patient_time", "patient_person_id", "observed_at", "id"),
    )


class CoreMedicationAdministration(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_medication_administrations"

    id = Column(String(26), primary_key=True, default=_core_id)
    administration_key = Column(String(120), nullable=False, unique=True, index=True)
    admission_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    encounter_id = Column(String(26), nullable=False, index=True)
    prescription_id = Column(String(26), nullable=False, index=True)
    prescription_item_id = Column(String(26), nullable=False, index=True)
    medication_catalog_id = Column(String(26), nullable=False, index=True)
    administrator_account_id = Column(String(26), nullable=False, index=True)
    dose_value = Column(String(80), nullable=False)
    dose_unit = Column(String(40), nullable=False)
    route = Column(String(80), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    administered_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(24), nullable=False, default="ORDERED", index=True)
    reason = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('ORDERED','VERIFIED','SCHEDULED','ADMINISTERED','HELD','REFUSED','MISSED','CANCELLED')", name="ck_core_emar_status"),
        CheckConstraint("version > 0", name="ck_core_emar_version"),
        Index("ix_core_emar_patient_time", "patient_person_id", "created_at"),
    )


class CoreMedicationSafetyEvent(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_medication_safety_events"

    id = Column(String(26), primary_key=True, default=_core_id)
    administration_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    event_type = Column(String(80), nullable=False)
    severity = Column(String(24), nullable=False, default="LOW")
    description = Column(Text, nullable=False)
    reported_by_account_id = Column(String(26), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (CheckConstraint("severity IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_core_med_safety_severity"),)


class CorePatientTransfer(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_transfers"

    id = Column(String(26), primary_key=True, default=_core_id)
    transfer_request_id = Column(String(100), nullable=False, unique=True, index=True)
    admission_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    from_ward_id = Column(String(26), nullable=False, index=True)
    to_ward_id = Column(String(26), nullable=False, index=True)
    from_bed_id = Column(String(26), nullable=True, index=True)
    to_bed_id = Column(String(26), nullable=True, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    requested_by_account_id = Column(String(26), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="REQUESTED", index=True)
    reason = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    requested_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('REQUESTED','ACCEPTED','PREPARING','IN_TRANSIT','RECEIVED','COMPLETED','CANCELLED','REJECTED')", name="ck_core_transfer_status"),
        CheckConstraint("version > 0", name="ck_core_transfer_version"),
        Index("ix_core_transfer_patient_status", "patient_person_id", "status"),
    )


class CoreHandover(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_handovers"

    id = Column(String(26), primary_key=True, default=_core_id)
    handover_request_id = Column(String(100), nullable=False, unique=True, index=True)
    admission_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    sender_account_id = Column(String(26), nullable=False, index=True)
    receiver_account_id = Column(String(26), nullable=True, index=True)
    status = Column(String(24), nullable=False, default="SUBMITTED", index=True)
    minimal_summary = Column(JSON, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("status IN ('SUBMITTED','ACKNOWLEDGED','AMENDED','CANCELLED')", name="ck_core_handover_status"),
        CheckConstraint("version > 0", name="ck_core_handover_version"),
    )


class CoreDischarge(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_discharges"

    id = Column(String(26), primary_key=True, default=_core_id)
    discharge_request_id = Column(String(100), nullable=False, unique=True, index=True)
    admission_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    responsible_provider_account_id = Column(String(26), nullable=False, index=True)
    disposition = Column(String(32), nullable=False, default="HOME")
    status = Column(String(24), nullable=False, default="PLANNED", index=True)
    medication_reconciliation_complete = Column(Integer, nullable=False, default=0)
    pending_results_reviewed = Column(Integer, nullable=False, default=0)
    follow_up_plan = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    planned_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("disposition IN ('HOME','TRANSFER','OTHER_FACILITY','DEATH')", name="ck_core_discharge_disposition"),
        CheckConstraint("status IN ('PLANNED','APPROVED','COMPLETED','CANCELLED')", name="ck_core_discharge_status"),
        CheckConstraint("medication_reconciliation_complete IN (0,1)", name="ck_core_discharge_med_recon"),
        CheckConstraint("pending_results_reviewed IN (0,1)", name="ck_core_discharge_results_reviewed"),
        CheckConstraint("version > 0", name="ck_core_discharge_version"),
    )


class CoreDischargeSummary(Base):  # type: ignore[misc]
    __tablename__ = "core_hospital_discharge_summaries"

    id = Column(String(26), primary_key=True, default=_core_id)
    discharge_id = Column(String(26), nullable=False, index=True)
    summary_version = Column(Integer, nullable=False, default=1)
    status = Column(String(24), nullable=False, default="DRAFT", index=True)
    admission_reason = Column(Text, nullable=False)
    diagnoses = Column(JSON, nullable=False, default=list)
    procedures = Column(JSON, nullable=False, default=list)
    treatment = Column(Text, nullable=False)
    medications = Column(JSON, nullable=False, default=list)
    results = Column(JSON, nullable=False, default=list)
    condition = Column(Text, nullable=False)
    follow_up = Column(Text, nullable=True)
    authored_by_account_id = Column(String(26), nullable=False, index=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    signed_by_account_id = Column(String(26), nullable=True, index=True)
    correction_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','SIGNED','AMENDED')", name="ck_core_discharge_summary_status"),
        CheckConstraint("summary_version > 0", name="ck_core_discharge_summary_version"),
        UniqueConstraint("discharge_id", "summary_version", name="uq_core_discharge_summary_version"),
    )


__all__ = [
    "CoreAdmission",
    "CoreBedAllocation",
    "CoreCareTeamMember",
    "CoreDischarge",
    "CoreDischargeSummary",
    "CoreHandover",
    "CoreHospitalBed",
    "CoreHospitalFacility",
    "CoreHospitalRoom",
    "CoreHospitalWard",
    "CoreMedicationAdministration",
    "CoreMedicationSafetyEvent",
    "CoreNursingTask",
    "CorePatientTransfer",
    "CoreVitalObservation",
]
