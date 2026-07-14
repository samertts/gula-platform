from datetime import date

from app.ehr.base import EHRBaseEntity, _ulid
from app.ehr.enums import DiagnosisType, ProblemStatus
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text


class ProblemListItem(EHRBaseEntity):
    __tablename__ = "ehr_problem_list_items"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    status = Column(SAEnum(ProblemStatus), nullable=False, default=ProblemStatus.ACTIVE)
    code = Column(String(50), nullable=True, index=True)
    code_system = Column(String(20), nullable=True)
    display = Column(String(300), nullable=False)
    display_ar = Column(String(300), nullable=True)

    clinical_status = Column(String(50), nullable=True)
    verification_status = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)

    severity = Column(String(50), nullable=True)
    onset_date = Column(Date, nullable=True)
    resolution_date = Column(Date, nullable=True)
    recorded_date = Column(DateTime(timezone=True), nullable=True)

    body_site = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_problem_patient", "patient_id", "status"),
        Index("ix_ehr_problem_citizen", "citizen_id"),
        Index("ix_ehr_problem_code", "code"),
        Index("ix_ehr_problem_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )


class ConditionRecord(EHRBaseEntity):
    __tablename__ = "ehr_conditions"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    clinical_status = Column(String(50), nullable=False, default="active")
    verification_status = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)
    severity = Column(String(50), nullable=True)

    code = Column(String(50), nullable=True, index=True)
    code_system = Column(String(20), nullable=True)
    code_display = Column(String(300), nullable=False)
    code_display_ar = Column(String(300), nullable=True)

    icd10_code = Column(String(20), nullable=True, index=True)
    icd10_description = Column(String(500), nullable=True)

    body_site = Column(String(200), nullable=True)
    laterality = Column(String(20), nullable=True)

    onset_date = Column(Date, nullable=True)
    abatement_date = Column(Date, nullable=True)
    recorded_date = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_condition_patient", "patient_id", "clinical_status"),
        Index("ix_ehr_condition_citizen", "citizen_id"),
        Index("ix_ehr_condition_encounter", "encounter_id"),
        Index("ix_ehr_condition_icd10", "icd10_code"),
        Index("ix_ehr_condition_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )


class DiagnosisRecord(EHRBaseEntity):
    __tablename__ = "ehr_diagnoses"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    diagnosis_type = Column(SAEnum(DiagnosisType), nullable=False, default=DiagnosisType.PRIMARY)
    rank = Column(Integer, default=0)

    icd10_code = Column(String(20), nullable=True, index=True)
    icd10_description = Column(String(500), nullable=True)
    snomed_code = Column(String(20), nullable=True)
    snomed_description = Column(String(500), nullable=True)
    diagnosis_text = Column(String(500), nullable=False)
    diagnosis_text_ar = Column(String(500), nullable=True)

    diagnosis_date = Column(Date, nullable=True)
    resolution_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    is_chronic = Column(Boolean, default=False)

    certainty = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_diagnosis_patient", "patient_id", "diagnosis_type"),
        Index("ix_ehr_diagnosis_citizen", "citizen_id"),
        Index("ix_ehr_diagnosis_encounter", "encounter_id"),
        Index("ix_ehr_diagnosis_icd10", "icd10_code"),
        Index("ix_ehr_diagnosis_active", "patient_id", "is_active"),
        {"extend_existing": True},
    )
