from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from typing import Any

from app.clinical.access.models import CoreAccessGrant
from app.clinical.appointments.authorization import (
    AppointmentAuthorizationError,
    AppointmentAuthorizationService,
)
from app.clinical.appointments.service import AppointmentError
from app.clinical.encounters.models import CoreClinicalNote, CoreEncounter
from app.clinical.imaging.models import CoreImagingReport, CoreImagingStudy
from app.clinical.pharmacy.models import CoreDispense, CorePrescription, CorePrescriptionItem
from app.clinical.results.models import CoreLabResult
from app.identity.api.workspaces import NiamActor
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService


class ClinicalRecordError(AppointmentError):
    code = "CLINICAL_RECORD_ERROR"
    status_code = 400


class ClinicalRecordNotFoundError(ClinicalRecordError):
    code = "RECORD_NOT_FOUND"
    status_code = 404


class ClinicalRecordService:
    """Read-only, provenance-aware projection; source domains remain owners."""

    allowed_sections = {"identity_summary", "conditions", "allergies", "medications", "encounters", "labs", "imaging", "procedures", "referrals", "documents", "timeline"}

    def __init__(self, db):
        self.db = db
        self.authz = AppointmentAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)

    def get_record(self, actor: NiamActor, *, patient_person_id: str, workspace_id: str, limit: int, cursor: str | None, sections: list[str] | None, purpose: str | None, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        selected = self._sections(sections)
        access_mode = self._authorize_read(actor, scope, patient_person_id, purpose)
        decoded_cursor = self._decode_cursor(cursor) if cursor else None
        snapshot = self._aggregate(scope, patient_person_id, selected, limit, decoded_cursor)
        snapshot["metadata"] = {"projection_version": "20260828.1", "consistency": "strong_snapshot", "access_mode": access_mode, "minimum_necessary": True, "correlation_id": correlation_id}
        self._audit(actor, scope, patient_person_id, correlation_id, request_id, access_mode, selected)
        return snapshot

    def _authorize_read(self, actor, scope, patient_person_id: str, purpose: str | None) -> str:
        if scope.actor_person_id == patient_person_id:
            return "OWNER"
        if not purpose or purpose not in {"treatment", "referral", "emergency", "insurance", "personal"}:
            raise AppointmentAuthorizationError("purpose_required", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        related = self.db.query(CoreEncounter.id).filter(CoreEncounter.patient_person_id == patient_person_id, CoreEncounter.provider_account_id == actor.account.id, CoreEncounter.organization_id == scope.organization_id, CoreEncounter.facility_id == scope.facility_id, CoreEncounter.workspace_id == scope.workspace_id).first()
        if related is not None:
            self.authz.require_permission(actor, scope, "clinical.record.read")
            return "TREATING_PROVIDER"
        grant = self.db.query(CoreAccessGrant).filter(CoreAccessGrant.patient_person_id == patient_person_id, CoreAccessGrant.grantee_account_id == actor.account.id, CoreAccessGrant.resource_type == "clinical_record", CoreAccessGrant.resource_id == patient_person_id, CoreAccessGrant.organization_id == scope.organization_id, CoreAccessGrant.facility_id == scope.facility_id, CoreAccessGrant.workspace_id == scope.workspace_id, CoreAccessGrant.status == "ACTIVE").first()
        now = datetime.now(UTC)
        if grant is None or grant.expires_at is None or (grant.expires_at.replace(tzinfo=UTC) if grant.expires_at.tzinfo is None else grant.expires_at) <= now or grant.purpose != purpose or grant.scope.get("read_record") is not True:
            raise AppointmentAuthorizationError("record_object_denied", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        return "GRANTED"

    def _aggregate(self, scope, patient_person_id: str, selected: set[str], limit: int, cursor: tuple[str, str] | None) -> dict[str, Any]:
        result: dict[str, Any] = {"subject": {"person_id": patient_person_id}, "identity_summary": {"person_id": patient_person_id}, "conditions": [], "allergies": [], "medications": [], "encounters": [], "labs": [], "imaging": [], "procedures": [], "referrals": [], "documents": [], "timeline": [], "next_cursor": None}
        encounters = self.db.query(CoreEncounter).filter(CoreEncounter.patient_person_id == patient_person_id, CoreEncounter.organization_id == scope.organization_id, CoreEncounter.facility_id == scope.facility_id, CoreEncounter.workspace_id == scope.workspace_id, CoreEncounter.status != "CANCELLED").order_by(CoreEncounter.created_at.desc(), CoreEncounter.id.desc()).limit(1001).all() if {"encounters", "timeline"} & selected else []
        if "encounters" in selected:
            result["encounters"] = [{"id": row.id, "status": row.status, "version": row.version, "date": self._iso(row.created_at), "source": {"domain": "encounter", "id": row.id, "version": row.version}} for row in encounters[:limit]]
        if "labs" in selected or "timeline" in selected:
            labs = self.db.query(CoreLabResult).filter(CoreLabResult.patient_person_id == patient_person_id, CoreLabResult.organization_id == scope.organization_id, CoreLabResult.facility_id == scope.facility_id, CoreLabResult.workspace_id == scope.workspace_id, CoreLabResult.status == "RELEASED").order_by(CoreLabResult.released_at.desc(), CoreLabResult.id.desc()).limit(1001).all()
            if "labs" in selected:
                result["labs"] = [{"id": row.id, "test_code": row.test_code, "test_name": row.test_name, "status": row.status, "version": row.version, "value_numeric": float(row.value_numeric) if row.value_numeric is not None else None, "value_text": row.value_text, "unit": row.unit, "abnormal_flag": row.abnormal_flag, "released_at": self._iso(row.released_at), "source": {"domain": "laboratory", "id": row.id, "version": row.version, "provenance": row.provenance_type}} for row in labs[:limit]]
        prescriptions = []
        dispenses = []
        if "medications" in selected or "timeline" in selected:
            prescriptions = self.db.query(CorePrescription).filter(CorePrescription.patient_person_id == patient_person_id, CorePrescription.organization_id == scope.organization_id, CorePrescription.facility_id == scope.facility_id, CorePrescription.workspace_id == scope.workspace_id, CorePrescription.status.in_(("SIGNED", "AMENDED", "COMPLETED"))).order_by(CorePrescription.created_at.desc(), CorePrescription.id.desc()).limit(1001).all()
            dispenses = self.db.query(CoreDispense).filter(CoreDispense.patient_person_id == patient_person_id, CoreDispense.organization_id == scope.organization_id, CoreDispense.facility_id == scope.facility_id, CoreDispense.workspace_id == scope.workspace_id, CoreDispense.status.in_(("PARTIAL", "COMPLETED"))).order_by(CoreDispense.dispensed_at.desc(), CoreDispense.id.desc()).limit(1001).all()
            if "medications" in selected:
                result["medications"] = [self._medication_summary(row) for row in prescriptions[:limit]] + [{"id": row.id, "type": "dispense", "status": row.status, "quantity": row.quantity, "dispensed_at": self._iso(row.dispensed_at), "source": {"domain": "pharmacy", "id": row.id, "version": row.version}} for row in dispenses[:limit]]
        studies = []
        reports = []
        if "imaging" in selected or "timeline" in selected:
            studies = self.db.query(CoreImagingStudy).filter(CoreImagingStudy.patient_person_id == patient_person_id, CoreImagingStudy.organization_id == scope.organization_id, CoreImagingStudy.facility_id == scope.facility_id, CoreImagingStudy.workspace_id == scope.workspace_id, CoreImagingStudy.status == "COMPLETED").order_by(CoreImagingStudy.completed_at.desc(), CoreImagingStudy.id.desc()).limit(1001).all()
            reports = self.db.query(CoreImagingReport).filter(CoreImagingReport.patient_person_id == patient_person_id, CoreImagingReport.organization_id == scope.organization_id, CoreImagingReport.facility_id == scope.facility_id, CoreImagingReport.workspace_id == scope.workspace_id, CoreImagingReport.status == "RELEASED").order_by(CoreImagingReport.released_at.desc(), CoreImagingReport.id.desc()).limit(1001).all()
            if "imaging" in selected:
                result["imaging"] = [{"id": row.id, "study_id": row.study_id, "accession_number": row.accession_number, "modality": row.modality, "status": row.status, "version": row.version, "completed_at": self._iso(row.completed_at), "source": {"domain": "imaging", "id": row.id, "version": row.version, "provenance": row.provenance_type}} for row in studies[:limit]] + [{"id": row.id, "report_id": row.report_id, "study_id": row.study_id, "status": row.status, "version": row.version, "impression": row.impression, "released_at": self._iso(row.released_at), "source": {"domain": "imaging_report", "id": row.id, "version": row.version}} for row in reports[:limit]]
        notes = self.db.query(CoreClinicalNote).filter(CoreClinicalNote.patient_person_id == patient_person_id, CoreClinicalNote.organization_id == scope.organization_id, CoreClinicalNote.facility_id == scope.facility_id, CoreClinicalNote.workspace_id == scope.workspace_id, CoreClinicalNote.status.in_(("SIGNED", "AMENDED"))).order_by(CoreClinicalNote.created_at.desc(), CoreClinicalNote.id.desc()).limit(1001).all() if "timeline" in selected else []
        if "timeline" in selected:
            events = []
            events.extend({"event_date": row.created_at, "id": row.id, "source_domain": "encounter", "source_id": row.id, "source_version": row.version, "status": row.status, "provenance": "canonical"} for row in encounters)
            events.extend({"event_date": row.released_at or row.created_at, "id": row.id, "source_domain": "laboratory", "source_id": row.id, "source_version": row.version, "status": row.status, "provenance": row.provenance_type} for row in (labs if "labs" in locals() else []))
            events.extend({"event_date": row.created_at, "id": row.id, "source_domain": "medication", "source_id": row.id, "source_version": row.version, "status": row.status, "provenance": "canonical"} for row in prescriptions)
            events.extend({"event_date": row.dispensed_at, "id": row.id, "source_domain": "dispensing", "source_id": row.id, "source_version": row.version, "status": row.status, "provenance": "canonical"} for row in dispenses)
            events.extend({"event_date": row.completed_at or row.received_at, "id": row.id, "source_domain": "imaging_study", "source_id": row.id, "source_version": row.version, "status": row.status, "provenance": row.provenance_type} for row in studies)
            events.extend({"event_date": row.released_at or row.created_at, "id": row.id, "source_domain": "imaging_report", "source_id": row.id, "source_version": row.version, "status": row.status, "provenance": "canonical"} for row in reports)
            events.extend({"event_date": row.created_at, "id": row.id, "source_domain": "clinical_note", "source_id": row.id, "source_version": row.version, "status": row.status, "provenance": "canonical"} for row in notes)
            events.sort(key=lambda item: (item["event_date"] or datetime.min.replace(tzinfo=UTC), item["id"]), reverse=True)
            if cursor:
                cursor_date, cursor_id = cursor
                events = [event for event in events if (self._iso(event["event_date"]), event["id"]) < (cursor_date, cursor_id)]
            page = events[: limit + 1]
            result["timeline"] = [{"event_date": self._iso(event["event_date"]), "source": {"domain": event["source_domain"], "id": event["source_id"], "version": event["source_version"], "provenance": event["provenance"]}, "status": event["status"]} for event in page[:limit]]
            if len(page) > limit:
                last = page[limit - 1]
                result["next_cursor"] = self._encode_cursor(self._iso(last["event_date"]), last["id"])
        return result

    def _medication_summary(self, row):
        items = self.db.query(CorePrescriptionItem).filter(CorePrescriptionItem.prescription_row_id == row.id).order_by(CorePrescriptionItem.id.asc()).limit(50).all()
        return {"id": row.id, "type": "prescription", "status": row.status, "version": row.version, "purpose": row.purpose, "signed_at": self._iso(row.signed_at), "items": [{"medication_code": item.medication_code, "medication_name": item.medication_name, "dose_value": item.dose_value, "dose_unit": item.dose_unit, "frequency": item.frequency, "route": item.route, "duration_days": item.duration_days, "quantity": item.quantity, "quantity_unit": item.quantity_unit} for item in items], "source": {"domain": "pharmacy", "id": row.id, "version": row.version}}

    def _sections(self, sections: list[str] | None) -> set[str]:
        if not sections:
            return set(self.allowed_sections)
        selected = {part.strip() for part in sections if part.strip()}
        if not selected or not selected.issubset(self.allowed_sections):
            raise ClinicalRecordError("Unknown or empty clinical-record section", status_code=422, code="INVALID_RECORD_SECTION")
        return selected

    @staticmethod
    def _iso(value):
        return value.isoformat() if value else None

    @staticmethod
    def _encode_cursor(event_date: str, event_id: str) -> str:
        raw = json.dumps({"date": event_date, "id": event_id}, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> tuple[str, str]:
        try:
            padded = cursor + "=" * (-len(cursor) % 4)
            value = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
            if not isinstance(value, dict) or not isinstance(value.get("date"), str) or not isinstance(value.get("id"), str):
                raise ValueError
            return value["date"], value["id"]
        except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ClinicalRecordError("The clinical-record cursor is invalid", status_code=422, code="INVALID_RECORD_CURSOR") from exc

    def _audit(self, actor, scope, patient_person_id, correlation_id, request_id, access_mode, selected):
        self.audit.record(AuditEventInput(event_type="CLINICAL_RECORD_VIEWED", category="clinical_record", action="record.read", actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type="clinical_record", target_id=patient_person_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", changes={"access_mode": access_mode, "sections": sorted(selected), "purpose": "redacted"}))
