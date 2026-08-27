from __future__ import annotations

import secrets
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import func

from app.clinical.appointments.authorization import (
    AppointmentAuthorizationError,
    AppointmentAuthorizationService,
)
from app.clinical.appointments.service import AppointmentError, VersionConflictError
from app.clinical.command_guard import CanonicalClinicalCommandGuard
from app.contracts.clinical_core import require_transition
from app.identity.api.workspaces import NiamActor
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

from .models import (
    CoreDispense,
    CoreMedicationBatch,
    CoreMedicationCatalog,
    CoreMedicationStockLedger,
    CorePrescription,
    CorePrescriptionItem,
)


class PharmacyNotFoundError(AppointmentError):
    code = "PHARMACY_RESOURCE_NOT_FOUND"
    status_code = 404


class PharmacyStateConflictError(AppointmentError):
    code = "PHARMACY_STATE_CONFLICT"
    status_code = 409


class MedicationNotFoundError(PharmacyNotFoundError):
    code = "MEDICATION_NOT_FOUND"


class PrescriptionNotFoundError(PharmacyNotFoundError):
    code = "PRESCRIPTION_NOT_FOUND"


class DispenseNotFoundError(PharmacyNotFoundError):
    code = "DISPENSE_NOT_FOUND"


class InventoryConflictError(PharmacyStateConflictError):
    code = "INVENTORY_CONFLICT"


class OverDispenseError(PharmacyStateConflictError):
    code = "OVER_DISPENSE"


class ExpiredMedicationError(PharmacyStateConflictError):
    code = "EXPIRED_MEDICATION"


class ControlledMedicationPolicyError(AppointmentError):
    code = "CONTROLLED_MEDICATION_POLICY_REQUIRED"
    status_code = 422


class CanonicalPharmacyService:
    """Server-authoritative medication, prescription and dispensing workflow.

    Legacy pharmacy and EHR tables remain outside this owner boundary. This
    service emits no commercial/POS side effects and never calls a delivery
    channel. A completed dispense is the only operation that decrements stock,
    and it does so under a batch lock with an append-only ledger row.
    """

    def __init__(self, db):
        self.db = db
        self.authz = AppointmentAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)
        self.command_guard = CanonicalClinicalCommandGuard(db, actor_account_id=None)

    def create_medication(self, actor: NiamActor, *, workspace_id: str, code: str, code_system: str, generic_name: str, brand_name: str | None, strength_value: str | None, strength_unit: str | None, dosage_form: str | None, route: str | None, is_controlled: bool, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, "clinical.medication.catalog_manage")
        payload = {"workspace_id": scope.workspace_id, "code": code, "code_system": code_system, "generic_name": generic_name, "is_controlled": is_controlled}
        cached = self._claim(actor, "medication.catalog.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CoreMedicationCatalog).filter(CoreMedicationCatalog.code == code).first() is not None:
            raise PharmacyStateConflictError("Medication code already exists", code="MEDICATION_CODE_EXISTS")
        medication = CoreMedicationCatalog(code=code.strip(), code_system=code_system.strip(), generic_name=generic_name.strip(), brand_name=brand_name.strip() if brand_name else None, strength_value=strength_value.strip() if strength_value else None, strength_unit=strength_unit.strip() if strength_unit else None, dosage_form=dosage_form.strip() if dosage_form else None, route=route.strip() if route else None, is_controlled=1 if is_controlled else 0, is_active=1)
        self.db.add(medication)
        self.db.flush()
        response = self._medication_response(medication, correlation_id)
        self._complete(actor, "medication.catalog.create", idempotency_key, response, medication.id)
        self._audit(actor, "MEDICATION_CATALOG_CREATED", "medication", medication.id, scope, correlation_id, request_id, {"code": medication.code, "controlled": bool(medication.is_controlled)})
        return response

    def create_prescription(self, actor: NiamActor, *, encounter_id: str, workspace_id: str, purpose: str, note: str | None, items: list[dict[str, Any]], idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        encounter = self._encounter_for_scope(encounter_id, scope)
        if encounter.status not in {"IN_PROGRESS", "COMPLETED"}:
            raise PharmacyStateConflictError("Prescriptions require an active or completed encounter", code="ENCOUNTER_NOT_ELIGIBLE")
        if actor.account.id != encounter.provider_account_id:
            raise AppointmentAuthorizationError("prescriber_object_mismatch", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        self.authz.require_permission(actor, scope, "clinical.medication.prescribe")
        normalized = self._normalize_items(items)
        payload = {"encounter_id": encounter.id, "workspace_id": scope.workspace_id, "purpose": purpose, "items": normalized}
        cached = self._claim(actor, "prescription.create", idempotency_key, payload)
        if cached is not None:
            return cached
        medication_rows = self._catalog_rows(normalized)
        aggregate_id = _core_id()
        prescription = CorePrescription(id=aggregate_id, prescription_id=aggregate_id, prescription_number=f"RX-{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(4).upper()}", version=1, encounter_id=encounter.id, patient_person_id=encounter.patient_person_id, prescriber_account_id=actor.account.id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, status="DRAFT", purpose=purpose.strip(), controlled_policy_status="PENDING_POLICY_REVIEW" if any(row.is_controlled for row in medication_rows) else "NOT_CONTROLLED", note=note.strip() if note else None)
        self.db.add(prescription)
        self.db.flush()
        for item, medication in zip(normalized, medication_rows, strict=True):
            self.db.add(CorePrescriptionItem(prescription_row_id=prescription.id, medication_catalog_id=medication.id, medication_code=medication.code, medication_name=medication.generic_name, dose_value=item["dose_value"], dose_unit=item["dose_unit"], frequency=item["frequency"], route=item["route"], duration_days=item["duration_days"], quantity=item["quantity"], quantity_unit=item["quantity_unit"], substitution_allowed=0, instructions=item.get("instructions")))
        self.db.flush()
        response = self._prescription_response(prescription, correlation_id)
        self._complete(actor, "prescription.create", idempotency_key, response, prescription.id)
        self._audit(actor, "PRESCRIPTION_CREATED", "prescription", prescription.id, scope, correlation_id, request_id, {"state_after": prescription.status, "version": prescription.version, "item_count": len(normalized)})
        return response

    def sign_prescription(self, actor: NiamActor, *, prescription_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        prescription = self._prescription_for_update(prescription_id, scope)
        self._require_prescriber(actor, scope, prescription)
        self.authz.require_permission(actor, scope, "clinical.medication.sign")
        self._assert_version(prescription.version, expected_version)
        payload = {"resource_id": prescription.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "prescription.sign", idempotency_key, payload)
        if cached is not None:
            return cached
        if prescription.status != "DRAFT":
            raise PharmacyStateConflictError("Only a draft prescription can be signed", code="PRESCRIPTION_NOT_SIGNABLE")
        if prescription.controlled_policy_status != "NOT_CONTROLLED":
            raise ControlledMedicationPolicyError("Controlled medication requires an explicit policy review before signing")
        before = prescription.status
        require_transition("prescription", before, "SIGNED")
        prescription.status = "SIGNED"
        prescription.signed_by_account_id = actor.account.id
        prescription.signed_at = datetime.now(UTC)
        prescription.version += 1
        self.db.flush()
        response = self._prescription_response(prescription, correlation_id)
        self._complete(actor, "prescription.sign", idempotency_key, response, prescription.id)
        self._audit(actor, "PRESCRIPTION_SIGNED", "prescription", prescription.id, scope, correlation_id, request_id, {"state_before": before, "state_after": prescription.status, "content_immutable": True, "version": prescription.version})
        return response

    def amend_prescription(self, actor: NiamActor, *, prescription_id: str, workspace_id: str, expected_version: int, reason: str, items: list[dict[str, Any]], idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        original = self._prescription_for_update(prescription_id, scope)
        self._require_prescriber(actor, scope, original)
        self.authz.require_permission(actor, scope, "clinical.medication.amend")
        self._assert_version(original.version, expected_version)
        if original.status not in {"SIGNED", "AMENDED"}:
            raise PharmacyStateConflictError("Only a signed prescription can be amended", code="PRESCRIPTION_NOT_AMENDABLE")
        normalized = self._normalize_items(items)
        medication_rows = self._catalog_rows(normalized)
        payload = {"resource_id": original.id, "workspace_id": scope.workspace_id, "expected_version": expected_version, "reason": reason.strip(), "items": normalized}
        cached = self._claim(actor, "prescription.amend", idempotency_key, payload)
        if cached is not None:
            return cached
        original_before = original.status
        original.status = "AMENDED"
        next_row = CorePrescription(id=_core_id(), prescription_id=original.prescription_id, prescription_number=original.prescription_number, version=original.version + 1, encounter_id=original.encounter_id, patient_person_id=original.patient_person_id, prescriber_account_id=original.prescriber_account_id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, status="DRAFT", purpose=original.purpose, controlled_policy_status="PENDING_POLICY_REVIEW" if any(row.is_controlled for row in medication_rows) else "NOT_CONTROLLED", supersedes_id=original.id, amendment_reason=reason.strip(), note=original.note)
        self.db.add(next_row)
        self.db.flush()
        for item, medication in zip(normalized, medication_rows, strict=True):
            self.db.add(CorePrescriptionItem(prescription_row_id=next_row.id, medication_catalog_id=medication.id, medication_code=medication.code, medication_name=medication.generic_name, dose_value=item["dose_value"], dose_unit=item["dose_unit"], frequency=item["frequency"], route=item["route"], duration_days=item["duration_days"], quantity=item["quantity"], quantity_unit=item["quantity_unit"], substitution_allowed=0, instructions=item.get("instructions")))
        self.db.flush()
        response = self._prescription_response(next_row, correlation_id)
        self._complete(actor, "prescription.amend", idempotency_key, response, next_row.id)
        self._audit(actor, "PRESCRIPTION_AMENDED", "prescription", next_row.id, scope, correlation_id, request_id, {"supersedes_id": original.id, "state_before": original_before, "state_after": original.status, "version_before": expected_version, "version_after": next_row.version, "reason": reason.strip()})
        return response

    def create_batch(self, actor: NiamActor, *, workspace_id: str, medication_catalog_id: str, batch_number: str, expiry_date: date, quantity_received: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, "clinical.medication.inventory")
        medication = self.db.query(CoreMedicationCatalog).filter(CoreMedicationCatalog.id == medication_catalog_id, CoreMedicationCatalog.is_active == 1).first()
        if medication is None:
            raise MedicationNotFoundError("Medication catalog entry was not found")
        if expiry_date <= date.today():
            raise ExpiredMedicationError("Expired medication cannot be received into available stock")
        payload = {"workspace_id": scope.workspace_id, "medication_catalog_id": medication_catalog_id, "batch_number": batch_number, "expiry_date": expiry_date.isoformat(), "quantity_received": quantity_received}
        cached = self._claim(actor, "medication.batch.create", idempotency_key, payload)
        if cached is not None:
            return cached
        batch = CoreMedicationBatch(medication_catalog_id=medication.id, batch_number=batch_number.strip(), organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, expiry_date=expiry_date, quantity_received=quantity_received, quantity_available=quantity_received, quarantined=0)
        self.db.add(batch)
        self.db.flush()
        ledger = CoreMedicationStockLedger(batch_id=batch.id, medication_catalog_id=medication.id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, movement_type="RECEIPT", quantity_delta=quantity_received, reference_type="batch", reference_id=batch.id, actor_account_id=actor.account.id, correlation_id=correlation_id)
        self.db.add(ledger)
        self.db.flush()
        response = self._batch_response(batch, correlation_id)
        self._complete(actor, "medication.batch.create", idempotency_key, response, batch.id)
        self._audit(actor, "MEDICATION_BATCH_RECEIVED", "medication_batch", batch.id, scope, correlation_id, request_id, {"quantity": quantity_received, "expiry_date": expiry_date.isoformat()})
        return response

    def prepare_dispense(self, actor: NiamActor, *, prescription_row_id: str, prescription_item_id: str, batch_id: str, workspace_id: str, quantity: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, "clinical.medication.dispense")
        prescription, item = self._prescription_and_item(prescription_row_id, prescription_item_id, scope)
        if prescription.status not in {"SIGNED", "AMENDED"}:
            raise PharmacyStateConflictError("Only a signed prescription may be prepared for dispensing", code="PRESCRIPTION_NOT_DISPENSABLE")
        if prescription.controlled_policy_status != "NOT_CONTROLLED":
            raise ControlledMedicationPolicyError("Controlled medication requires an explicit policy review before dispensing")
        batch = self._batch_for_update(batch_id, scope)
        if batch.medication_catalog_id != item.medication_catalog_id:
            raise InventoryConflictError("The selected batch does not belong to the prescribed medication", code="MEDICATION_BATCH_MISMATCH")
        if batch.quarantined or batch.expiry_date <= date.today():
            raise ExpiredMedicationError("Expired or quarantined medication cannot be prepared")
        if batch.quantity_available < quantity:
            raise InventoryConflictError("Insufficient available stock")
        fulfilled = self.db.query(func.coalesce(func.sum(CoreDispense.quantity), 0)).filter(CoreDispense.prescription_item_id == item.id, CoreDispense.status.in_(("PARTIAL", "COMPLETED"))).scalar() or 0
        remaining = item.quantity - int(fulfilled)
        if remaining <= 0 or quantity > remaining:
            raise OverDispenseError("The requested quantity exceeds the remaining prescribed quantity")
        payload = {"prescription_row_id": prescription.id, "prescription_item_id": item.id, "batch_id": batch.id, "workspace_id": scope.workspace_id, "quantity": quantity}
        cached = self._claim(actor, "dispense.prepare", idempotency_key, payload)
        if cached is not None:
            return cached
        dispense = CoreDispense(prescription_row_id=prescription.id, prescription_item_id=item.id, patient_person_id=prescription.patient_person_id, medication_catalog_id=item.medication_catalog_id, batch_id=batch.id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, quantity=quantity, status="PREPARED", prepared_by_account_id=actor.account.id, version=1, correlation_id=correlation_id)
        self.db.add(dispense)
        self.db.flush()
        response = self._dispense_response(dispense)
        self._complete(actor, "dispense.prepare", idempotency_key, response, dispense.id)
        self._audit(actor, "DISPENSE_PREPARED", "dispense", dispense.id, scope, correlation_id, request_id, {"status_after": dispense.status, "quantity": quantity, "batch_id": batch.id})
        return response

    def complete_dispense(self, actor: NiamActor, *, dispense_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        dispense = self.db.query(CoreDispense).filter(CoreDispense.id == dispense_id, CoreDispense.organization_id == scope.organization_id, CoreDispense.facility_id == scope.facility_id, CoreDispense.workspace_id == scope.workspace_id).with_for_update().first()
        if dispense is None:
            raise DispenseNotFoundError("Dispense was not found")
        self.authz.require_permission(actor, scope, "clinical.medication.dispense")
        self._assert_version(dispense.version, expected_version)
        payload = {"resource_id": dispense.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "dispense.complete", idempotency_key, payload)
        if cached is not None:
            return cached
        if dispense.status != "PREPARED":
            raise PharmacyStateConflictError("Only a prepared dispense can be completed", code="DISPENSE_NOT_PREPARED")
        if dispense.prepared_by_account_id == actor.account.id:
            raise PharmacyStateConflictError("Preparation and verification require separate actors", code="SEPARATION_OF_DUTIES_REQUIRED", status_code=403)
        batch = self._batch_for_update(dispense.batch_id, scope)
        if batch.quarantined or batch.expiry_date <= date.today():
            raise ExpiredMedicationError("Expired or quarantined medication cannot be dispensed")
        item = self.db.query(CorePrescriptionItem).filter(CorePrescriptionItem.id == dispense.prescription_item_id, CorePrescriptionItem.prescription_row_id == dispense.prescription_row_id).first()
        if item is None:
            raise PharmacyNotFoundError("Prescription item was not found")
        fulfilled = self.db.query(func.coalesce(func.sum(CoreDispense.quantity), 0)).filter(CoreDispense.prescription_item_id == item.id, CoreDispense.status.in_(("PARTIAL", "COMPLETED"))).scalar() or 0
        remaining = item.quantity - int(fulfilled)
        if remaining <= 0 or dispense.quantity > remaining:
            raise OverDispenseError("The requested quantity exceeds the remaining prescribed quantity")
        if batch.quantity_available < dispense.quantity:
            raise InventoryConflictError("Insufficient available stock")
        before = dispense.status
        batch.quantity_available -= dispense.quantity
        dispense.status = "COMPLETED" if dispense.quantity == remaining else "PARTIAL"
        dispense.verified_by_account_id = actor.account.id
        dispense.dispensed_by_account_id = actor.account.id
        dispense.version += 1
        dispense.dispensed_at = datetime.now(UTC)
        self.db.add(CoreMedicationStockLedger(batch_id=batch.id, medication_catalog_id=batch.medication_catalog_id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, movement_type="DISPENSE", quantity_delta=-dispense.quantity, reference_type="dispense", reference_id=dispense.id, actor_account_id=actor.account.id, correlation_id=correlation_id))
        self.db.flush()
        response = self._dispense_response(dispense)
        self._complete(actor, "dispense.complete", idempotency_key, response, dispense.id)
        self._audit(actor, "DISPENSING_COMPLETED", "dispense", dispense.id, scope, correlation_id, request_id, {"state_before": before, "state_after": dispense.status, "quantity": dispense.quantity, "batch_remaining": batch.quantity_available, "version_after": dispense.version})
        return response

    def get_prescription(self, actor: NiamActor, *, prescription_id: str, workspace_id: str, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        prescription = self._prescription_for_scope(prescription_id, scope)
        self._require_read(actor, scope, prescription)
        return self._prescription_response(prescription, correlation_id)

    def fhir_prescription(self, actor: NiamActor, *, prescription_id: str, workspace_id: str, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        prescription = self._prescription_for_scope(prescription_id, scope)
        self._require_read(actor, scope, prescription)
        self._audit_read(actor, "PRESCRIPTION_FHIR_VIEWED", "prescription", prescription.id, scope, correlation_id)
        return self.fhir_medication_request(prescription)

    def fhir_dispense(self, actor: NiamActor, *, dispense_id: str, workspace_id: str, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        dispense = self._dispense_for_scope(dispense_id, scope)
        allowed = scope.actor_person_id == dispense.patient_person_id or actor.account.id in {dispense.prepared_by_account_id, dispense.verified_by_account_id, dispense.dispensed_by_account_id}
        if not allowed:
            raise AppointmentAuthorizationError("dispense_object_denied", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        if scope.actor_person_id == dispense.patient_person_id and dispense.status not in {"PARTIAL", "COMPLETED"}:
            raise AppointmentAuthorizationError("dispense_not_released", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        self._audit_read(actor, "DISPENSE_FHIR_VIEWED", "dispense", dispense.id, scope, correlation_id)
        return self.fhir_medication_dispense(dispense)

    def medication_history(self, actor: NiamActor, *, patient_person_id: str, workspace_id: str, limit: int, offset: int, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_self_patient(scope, patient_person_id)
        query = self.db.query(CorePrescription).filter(CorePrescription.patient_person_id == patient_person_id, CorePrescription.organization_id == scope.organization_id, CorePrescription.facility_id == scope.facility_id, CorePrescription.workspace_id == scope.workspace_id, CorePrescription.status.in_(("SIGNED", "AMENDED", "COMPLETED")))
        total = query.count()
        rows = query.order_by(CorePrescription.created_at.desc(), CorePrescription.id.desc()).offset(offset).limit(limit).all()
        return {"items": [self._prescription_response(row, correlation_id) for row in rows], "limit": limit, "offset": offset, "total": total, "correlation_id": correlation_id}

    def _encounter_for_scope(self, encounter_id: str, scope):
        from app.clinical.encounters.models import CoreEncounter
        encounter = self.db.query(CoreEncounter).filter(CoreEncounter.id == encounter_id, CoreEncounter.organization_id == scope.organization_id, CoreEncounter.facility_id == scope.facility_id, CoreEncounter.workspace_id == scope.workspace_id).first()
        if encounter is None:
            raise PharmacyNotFoundError("Encounter was not found", code="ENCOUNTER_NOT_FOUND")
        return encounter

    def _prescription_for_scope(self, prescription_id: str, scope):
        row = self.db.query(CorePrescription).filter(CorePrescription.id == prescription_id, CorePrescription.organization_id == scope.organization_id, CorePrescription.facility_id == scope.facility_id, CorePrescription.workspace_id == scope.workspace_id).first()
        if row is None:
            raise PrescriptionNotFoundError("Prescription was not found")
        return row

    def _dispense_for_scope(self, dispense_id: str, scope):
        row = self.db.query(CoreDispense).filter(CoreDispense.id == dispense_id, CoreDispense.organization_id == scope.organization_id, CoreDispense.facility_id == scope.facility_id, CoreDispense.workspace_id == scope.workspace_id).first()
        if row is None:
            raise DispenseNotFoundError("Dispense record was not found")
        return row

    def _prescription_for_update(self, prescription_id: str, scope):
        row = self.db.query(CorePrescription).filter(CorePrescription.id == prescription_id, CorePrescription.organization_id == scope.organization_id, CorePrescription.facility_id == scope.facility_id, CorePrescription.workspace_id == scope.workspace_id).with_for_update().first()
        if row is None:
            raise PrescriptionNotFoundError("Prescription was not found")
        return row

    def _prescription_and_item(self, prescription_row_id: str, prescription_item_id: str, scope):
        prescription = self._prescription_for_scope(prescription_row_id, scope)
        item = self.db.query(CorePrescriptionItem).filter(CorePrescriptionItem.id == prescription_item_id, CorePrescriptionItem.prescription_row_id == prescription.id).first()
        if item is None:
            raise PharmacyNotFoundError("Prescription item was not found", code="PRESCRIPTION_ITEM_NOT_FOUND")
        return prescription, item

    def _batch_for_scope(self, batch_id: str, scope):
        row = self.db.query(CoreMedicationBatch).filter(CoreMedicationBatch.id == batch_id, CoreMedicationBatch.organization_id == scope.organization_id, CoreMedicationBatch.facility_id == scope.facility_id, CoreMedicationBatch.workspace_id == scope.workspace_id).first()
        if row is None:
            raise InventoryConflictError("Medication batch was not found", code="BATCH_NOT_FOUND")
        return row

    def _batch_for_update(self, batch_id: str, scope):
        row = self.db.query(CoreMedicationBatch).filter(CoreMedicationBatch.id == batch_id, CoreMedicationBatch.organization_id == scope.organization_id, CoreMedicationBatch.facility_id == scope.facility_id, CoreMedicationBatch.workspace_id == scope.workspace_id).with_for_update().first()
        if row is None:
            raise InventoryConflictError("Medication batch was not found", code="BATCH_NOT_FOUND")
        return row

    def _catalog_rows(self, items: list[dict[str, Any]]) -> list[CoreMedicationCatalog]:
        rows = []
        for item in items:
            row = self.db.query(CoreMedicationCatalog).filter(CoreMedicationCatalog.id == item["medication_catalog_id"], CoreMedicationCatalog.is_active == 1).first()
            if row is None:
                raise MedicationNotFoundError("Medication catalog entry was not found")
            rows.append(row)
        return rows

    def _require_prescriber(self, actor: NiamActor, scope, prescription: CorePrescription) -> None:
        if prescription.prescriber_account_id != actor.account.id:
            raise AppointmentAuthorizationError("prescriber_object_mismatch", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)

    def _require_read(self, actor: NiamActor, scope, prescription: CorePrescription) -> None:
        if scope.actor_person_id == prescription.patient_person_id:
            if prescription.status in {"SIGNED", "AMENDED", "COMPLETED"}:
                return
            raise AppointmentAuthorizationError("prescription_not_released", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        if prescription.prescriber_account_id == actor.account.id:
            return
        self.authz.require_permission(actor, scope, "clinical.medication.read")
        encounter = self._encounter_for_scope(prescription.encounter_id, scope)
        if encounter.provider_account_id != actor.account.id:
            raise AppointmentAuthorizationError("patient_scope_denied", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)

    @staticmethod
    def _normalize_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len({item["medication_catalog_id"] for item in items}) != len(items):
            raise AppointmentError("Each medication may appear only once", status_code=422, code="DUPLICATE_MEDICATION")
        normalized = []
        for item in items:
            if item.get("substitution_allowed"):
                raise AppointmentError("Automatic substitution is not permitted", status_code=422, code="SUBSTITUTION_NOT_ALLOWED")
            normalized.append({key: value.strip() if isinstance(value, str) else value for key, value in item.items() if key != "substitution_allowed"})
        return normalized

    @staticmethod
    def _assert_version(actual: int, expected: int) -> None:
        if expected < 1 or actual != expected:
            raise VersionConflictError("The clinical resource changed before this operation")

    def _claim(self, actor, operation: str, key: str, payload: dict[str, Any]):
        self.command_guard.actor_account_id = actor.account.id
        try:
            return self.command_guard.claim(operation=operation, idempotency_key=key, payload=payload)
        except ValueError as exc:
            raise AppointmentError(str(exc), status_code=400, code="IDEMPOTENCY_CONFLICT") from exc

    def _complete(self, actor, operation: str, key: str, response: dict[str, Any], resource_id: str) -> None:
        self.command_guard.actor_account_id = actor.account.id
        self.command_guard.complete(operation=operation, idempotency_key=key, resource_id=resource_id, response_body=response)

    def _audit_read(self, actor, event_type: str, target_type: str, target_id: str, scope, correlation_id: str) -> None:
        self.audit.record(AuditEventInput(event_type=event_type, category="clinical_pharmacy", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="allow", correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", outcome="allowed"))

    def _audit(self, actor, event_type: str, target_type: str, target_id: str, scope, correlation_id: str, request_id: str | None, changes: dict[str, Any]) -> None:
        self.audit.record(AuditEventInput(event_type=event_type, category="clinical_pharmacy", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", changes=changes))

    def _prescription_response(self, row: CorePrescription, correlation_id: str) -> dict[str, Any]:
        items = self.db.query(CorePrescriptionItem).filter(CorePrescriptionItem.prescription_row_id == row.id).order_by(CorePrescriptionItem.created_at.asc(), CorePrescriptionItem.id.asc()).all()
        return {"id": row.id, "prescription_id": row.prescription_id, "prescription_number": row.prescription_number, "version": row.version, "encounter_id": row.encounter_id, "patient_person_id": row.patient_person_id, "prescriber_account_id": row.prescriber_account_id, "organization_id": row.organization_id, "facility_id": row.facility_id, "workspace_id": row.workspace_id, "status": row.status, "purpose": row.purpose, "controlled_policy_status": row.controlled_policy_status, "signed_at": row.signed_at.isoformat() if row.signed_at else None, "supersedes_id": row.supersedes_id, "items": [{"id": item.id, "medication_catalog_id": item.medication_catalog_id, "medication_code": item.medication_code, "medication_name": item.medication_name, "dose_value": item.dose_value, "dose_unit": item.dose_unit, "frequency": item.frequency, "route": item.route, "duration_days": item.duration_days, "quantity": item.quantity, "quantity_unit": item.quantity_unit, "instructions": item.instructions} for item in items], "correlation_id": correlation_id}

    @staticmethod
    def _medication_response(row: CoreMedicationCatalog, correlation_id: str) -> dict[str, Any]:
        return {"id": row.id, "code": row.code, "code_system": row.code_system, "generic_name": row.generic_name, "brand_name": row.brand_name, "strength_value": row.strength_value, "strength_unit": row.strength_unit, "dosage_form": row.dosage_form, "route": row.route, "is_controlled": bool(row.is_controlled), "is_active": bool(row.is_active), "correlation_id": correlation_id}

    @staticmethod
    def _batch_response(row: CoreMedicationBatch, correlation_id: str) -> dict[str, Any]:
        return {"id": row.id, "medication_catalog_id": row.medication_catalog_id, "batch_number": row.batch_number, "facility_id": row.facility_id, "workspace_id": row.workspace_id, "expiry_date": row.expiry_date.isoformat() if row.expiry_date else None, "quantity_received": row.quantity_received, "quantity_available": row.quantity_available, "quarantined": bool(row.quarantined), "correlation_id": correlation_id}

    @staticmethod
    def _dispense_response(row: CoreDispense) -> dict[str, Any]:
        return {"id": row.id, "prescription_row_id": row.prescription_row_id, "prescription_item_id": row.prescription_item_id, "patient_person_id": row.patient_person_id, "medication_catalog_id": row.medication_catalog_id, "batch_id": row.batch_id, "quantity": row.quantity, "status": row.status, "version": row.version, "prepared_by_account_id": row.prepared_by_account_id, "verified_by_account_id": row.verified_by_account_id, "dispensed_by_account_id": row.dispensed_by_account_id, "dispensed_at": row.dispensed_at.isoformat() if row.dispensed_at else None, "correlation_id": row.correlation_id}

    @staticmethod
    def fhir_medication_request(row: CorePrescription) -> dict[str, Any]:
        status = "completed" if row.status == "COMPLETED" else ("active" if row.status in {"SIGNED", "AMENDED"} else "draft")
        return {"resourceType": "MedicationRequest", "id": row.prescription_id, "status": status, "intent": "order", "subject": {"reference": f"Patient/{row.patient_person_id}"}, "encounter": {"reference": f"Encounter/{row.encounter_id}"}, "authoredOn": row.created_at.isoformat() if row.created_at else None, "requester": {"reference": f"Practitioner/{row.prescriber_account_id}"}, "dosageInstruction": [{"text": "Medication directions are available in the canonical prescription items."}], "identifier": [{"system": "urn:gula:prescription", "value": row.prescription_number}], "note": [{"text": row.note}] if row.note else []}

    @staticmethod
    def fhir_medication_dispense(row: CoreDispense) -> dict[str, Any]:
        status = "completed" if row.status in {"PARTIAL", "COMPLETED"} else ("preparation" if row.status == "PREPARED" else "stopped")
        return {"resourceType": "MedicationDispense", "id": row.id, "status": status, "subject": {"reference": f"Patient/{row.patient_person_id}"}, "authorizingPrescription": [{"reference": f"MedicationRequest/{row.prescription_row_id}"}], "quantity": {"value": row.quantity}, "whenHandedOver": row.dispensed_at.isoformat() if row.dispensed_at else None, "performer": [{"actor": {"reference": f"Practitioner/{row.dispensed_by_account_id or row.prepared_by_account_id}"}}]}


def _core_id() -> str:
    return secrets.token_hex(13).upper()
