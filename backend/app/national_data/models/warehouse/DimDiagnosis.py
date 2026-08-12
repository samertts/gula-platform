from sqlalchemy import Boolean, Column, Index, String

from app.national_data.base import BaseEntity


class DimDiagnosis(BaseEntity):
    __tablename__ = "dw_dim_diagnosis"

    icd10_code = Column(String(20), nullable=True, index=True)
    icd10_description = Column(String(500), nullable=True)
    icd11_code = Column(String(32), nullable=True)
    snomed_code = Column(String(20), nullable=True)

    diagnosis_text = Column(String(500), nullable=False)
    diagnosis_text_ar = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)

    is_chronic = Column(Boolean, default=False, nullable=False)
    is_billable = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("ix_dw_dim_diag_icd10", "icd10_code"),
        Index("ix_dw_dim_diag_category", "category"),
        {"extend_existing": True},
    )
