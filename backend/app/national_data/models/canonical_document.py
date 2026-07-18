from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.national_data.base import DataPlatformBase
from app.ehr.models.attachment import ClinicalAttachment
from app.ehr.models.clinical_note import ClinicalNote
from app.national.domain.patient import Patient as NationalPatient


class CanonicalDocument(DataPlatformBase):
    __abstract__ = True

    document_id: str
    source: str
    document_type: str
    title: str | None
    content_summary: str | None
    patient_id: str
    citizen_id: str | None
    encounter_id: str | None
    practitioner_id: str | None
    created_at: datetime | None
    lab_id: int | None
    file_url: str | None
    mime_type: str | None

    @classmethod
    def query_all(cls, db: Session, lab_id: int | None = None, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        np_sub = db.query(NationalPatient).subquery()

        note_q = db.query(
            ClinicalNote.id.label("document_id"),
            ("clinical_note").label("source"),
            ("clinical_note").label("document_type"),
            ClinicalNote.title,
            ClinicalNote.content.label("content_summary"),
            ClinicalNote.patient_id,
            ClinicalNote.citizen_id,
            ClinicalNote.encounter_id,
            ClinicalNote.author_id.label("practitioner_id"),
            ClinicalNote.created_at,
            np_sub.c.lab_id,
            None.label("file_url"),
            None.label("mime_type"),
        ).outerjoin(
            np_sub, np_sub.c.id == ClinicalNote.patient_id,
        )

        attach_q = db.query(
            ClinicalAttachment.id.label("document_id"),
            ("attachment").label("source"),
            ClinicalAttachment.doc_type.label("document_type"),
            ClinicalAttachment.title,
            ClinicalAttachment.description.label("content_summary"),
            ClinicalAttachment.patient_id,
            ClinicalAttachment.citizen_id,
            ClinicalAttachment.encounter_id,
            None.label("practitioner_id"),
            ClinicalAttachment.created_at,
            np_sub.c.lab_id,
            ClinicalAttachment.file_url,
            ClinicalAttachment.mime_type,
        ).outerjoin(
            np_sub, np_sub.c.id == ClinicalAttachment.patient_id,
        )

        union_q = note_q.union_all(attach_q).subquery()

        query = db.query(union_q).select_entity_from(union_q)

        if lab_id is not None:
            query = query.filter(union_q.c.lab_id == lab_id)

        rows = query.order_by(union_q.c.created_at.desc().nullslast()).offset(skip).limit(limit).all()
        return [dict(row._mapping) for row in rows]
