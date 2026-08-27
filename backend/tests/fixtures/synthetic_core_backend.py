from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any
from uuid import uuid4

from app.contracts.clinical_core import (
    APPOINTMENT,
    CLINICAL_NOTE,
    CLINICAL_RECORD,
    CONSENT,
    DISPENSE,
    ENCOUNTER,
    IMAGING_ORDER,
    IMAGING_REPORT,
    IMAGING_STUDY,
    LAB_ORDER,
    PRESCRIPTION,
    RESULT,
    SPECIMEN,
    require_transition,
)


class SyntheticCoreError(Exception):
    pass


class SyntheticAuthorizationError(SyntheticCoreError):
    pass


class SyntheticConflictError(SyntheticCoreError):
    pass


@dataclass(frozen=True)
class SyntheticActor:
    id: str
    kind: str
    organization_id: str
    workspace_id: str
    roles: frozenset[str] = frozenset()
    patient_id: str | None = None
    account_id: str | None = None
    session_id: str | None = None
    identity_id: str | None = None


@dataclass(frozen=True)
class SyntheticIdentity:
    id: str
    account_id: str
    person_id: str
    kind: str
    active: bool = True


@dataclass
class SyntheticSession:
    id: str
    account_id: str
    device_id: str
    state: str = "ACTIVE"
    version: int = 1
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(hours=1))


@dataclass(frozen=True)
class SyntheticWorkspace:
    id: str
    organization_id: str
    facility_id: str
    active: bool = True


@dataclass(frozen=True)
class SyntheticMembership:
    account_id: str
    workspace_id: str
    roles: frozenset[str]
    active: bool = True


@dataclass
class SyntheticRecord:
    id: str
    state: str
    version: int = 1
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SyntheticAuditEvent:
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    before: str | None
    after: str | None
    version: int


class SyntheticCoreBackend:
    """Test-only backend with no production imports, network, or persistence."""

    def __init__(self) -> None:
        self.identities: dict[str, SyntheticIdentity] = {}
        self.sessions: dict[str, SyntheticSession] = {}
        self.workspaces: dict[str, SyntheticWorkspace] = {}
        self.memberships: dict[tuple[str, str], SyntheticMembership] = {}
        self.appointments: dict[str, SyntheticRecord] = {}
        self.encounters: dict[str, SyntheticRecord] = {}
        self.notes: dict[str, SyntheticRecord] = {}
        self.lab_orders: dict[str, SyntheticRecord] = {}
        self.specimens: dict[str, SyntheticRecord] = {}
        self.results: dict[str, SyntheticRecord] = {}
        self.consents: dict[str, SyntheticRecord] = {}
        self.medications: dict[str, SyntheticRecord] = {}
        self.prescriptions: dict[str, SyntheticRecord] = {}
        self.dispenses: dict[str, SyntheticRecord] = {}
        self.imaging_orders: dict[str, SyntheticRecord] = {}
        self.imaging_studies: dict[str, SyntheticRecord] = {}
        self.imaging_reports: dict[str, SyntheticRecord] = {}
        self._appointment_idempotency: dict[tuple[str, str], str] = {}
        self._used_slots: dict[tuple[str, str], str] = {}
        self.audit: list[SyntheticAuditEvent] = []
        self._booking_lock = Lock()
        self._clinical_lock = Lock()
        self._specimen_idempotency: dict[tuple[str, str], str] = {}
        self._result_idempotency: dict[tuple[str, str], str] = {}
        self._consent_idempotency: dict[tuple[str, str], str] = {}
        self._pharmacy_idempotency: dict[tuple[str, str], str] = {}
        self._imaging_idempotency: dict[tuple[str, str], str] = {}
        self._used_dicom_uids: set[str] = set()
        self.access_history: list[dict[str, Any]] = []

    def register_identity(self, *, account_id: str, person_id: str, kind: str = "citizen") -> SyntheticIdentity:
        identity = SyntheticIdentity(str(uuid4()), account_id, person_id, kind)
        self.identities[identity.id] = identity
        return identity

    def open_session(self, *, account_id: str, device_id: str, expires_at: datetime | None = None) -> SyntheticSession:
        session = SyntheticSession(str(uuid4()), account_id, device_id, expires_at=expires_at or (datetime.now(UTC) + timedelta(hours=1)))
        self.sessions[session.id] = session
        return session

    def revoke_session(self, session_id: str) -> None:
        session = self._get(self.sessions, session_id)
        session.state = "REVOKED"
        session.version += 1

    def register_workspace(self, *, workspace_id: str, organization_id: str, facility_id: str) -> SyntheticWorkspace:
        workspace = SyntheticWorkspace(workspace_id, organization_id, facility_id)
        self.workspaces[workspace.id] = workspace
        return workspace

    def add_membership(self, *, account_id: str, workspace_id: str, roles: frozenset[str]) -> SyntheticMembership:
        membership = SyntheticMembership(account_id, workspace_id, roles)
        self.memberships[(account_id, workspace_id)] = membership
        return membership

    def build_actor(
        self,
        *,
        actor_id: str,
        account_id: str,
        identity_id: str,
        organization_id: str,
        workspace_id: str,
        roles: frozenset[str] = frozenset(),
        patient_id: str | None = None,
        session_id: str,
    ) -> SyntheticActor:
        return SyntheticActor(actor_id, "citizen" if patient_id else "professional", organization_id, workspace_id, roles, patient_id, account_id, session_id, identity_id)

    def book_appointment(self, actor: SyntheticActor, *, patient_id: str, practitioner_id: str, slot: str, idempotency_key: str) -> SyntheticRecord:
        self._require_active_context(actor, "appointment:book")
        self._require(actor, patient_id == actor.patient_id or "scheduler" in actor.roles, "appointment:book")
        with self._booking_lock:
            key = (actor.id, idempotency_key)
            existing_id = self._appointment_idempotency.get(key)
            if existing_id:
                existing = self.appointments[existing_id]
                if existing.fields["slot"] != slot or existing.fields["patient_id"] != patient_id:
                    raise SyntheticConflictError("idempotency key reused with a different request")
                return existing
            slot_key = (actor.organization_id, slot)
            if slot_key in self._used_slots:
                raise SyntheticConflictError("slot already booked")
            appointment = SyntheticRecord(str(uuid4()), "REQUESTED", fields={"patient_id": patient_id, "practitioner_id": practitioner_id, "slot": slot, "organization_id": actor.organization_id, "workspace_id": actor.workspace_id})
            self.appointments[appointment.id] = appointment
            self._appointment_idempotency[key] = appointment.id
            self._used_slots[slot_key] = appointment.id
            self._audit(actor, "appointment.booked", "appointment", appointment.id, None, appointment.state, appointment.version)
            return appointment

    def confirm_appointment(self, actor: SyntheticActor, appointment_id: str) -> SyntheticRecord:
        appointment = self._get(self.appointments, appointment_id)
        self._require_active_context(actor, "appointment:confirm")
        if actor.account_id or actor.session_id or actor.identity_id:
            self._require(
                actor,
                actor.organization_id == appointment.fields["organization_id"]
                and actor.workspace_id == appointment.fields["workspace_id"],
                "appointment:confirm",
            )
        self._require(actor, "scheduler" in actor.roles or actor.id == appointment.fields["practitioner_id"], "appointment:confirm")
        self._transition(appointment, APPOINTMENT, "CONFIRMED")
        self._audit(actor, "appointment.confirmed", "appointment", appointment.id, "REQUESTED", appointment.state, appointment.version)
        return appointment

    def check_in(self, actor: SyntheticActor, appointment_id: str) -> SyntheticRecord:
        appointment = self._get(self.appointments, appointment_id)
        self._require(actor, actor.patient_id == appointment.fields["patient_id"] or "receptionist" in actor.roles, "appointment:check_in")
        self._transition(appointment, APPOINTMENT, "CHECKED_IN")
        self._audit(actor, "appointment.checked_in", "appointment", appointment.id, "CONFIRMED", appointment.state, appointment.version)
        return appointment

    def create_encounter(self, actor: SyntheticActor, appointment_id: str) -> SyntheticRecord:
        appointment = self._get(self.appointments, appointment_id)
        self._require(actor, actor.id == appointment.fields["practitioner_id"], "encounter:create")
        if appointment.state != "CHECKED_IN":
            raise SyntheticConflictError("encounter requires checked-in appointment")
        encounter = SyntheticRecord(str(uuid4()), "DRAFT", fields={"appointment_id": appointment.id, "patient_id": appointment.fields["patient_id"], "practitioner_id": actor.id, "organization_id": actor.organization_id})
        self.encounters[encounter.id] = encounter
        self._audit(actor, "encounter.created", "encounter", encounter.id, None, encounter.state, encounter.version)
        return encounter

    def complete_and_sign_note(self, actor: SyntheticActor, encounter_id: str, *, expected_version: int = 1) -> SyntheticRecord:
        encounter = self._get(self.encounters, encounter_id)
        self._require(actor, actor.id == encounter.fields["practitioner_id"], "clinical-note:sign")
        if encounter.version != expected_version:
            raise SyntheticConflictError("stale encounter version")
        self._transition(encounter, ENCOUNTER, "IN_PROGRESS")
        self._transition(encounter, ENCOUNTER, "COMPLETED")
        self._transition(encounter, ENCOUNTER, "SIGNED")
        note = SyntheticRecord(str(uuid4()), "DRAFT", fields={"encounter_id": encounter.id, "patient_id": encounter.fields["patient_id"], "text": "synthetic clinical note"})
        self._transition(note, CLINICAL_NOTE, "IN_PROGRESS")
        self._transition(note, CLINICAL_NOTE, "COMPLETED")
        self._transition(note, CLINICAL_NOTE, "SIGNED")
        self.notes[note.id] = note
        self._audit(actor, "clinical-note.signed", "clinical-note", note.id, "COMPLETED", note.state, note.version)
        return note

    def place_lab_order(self, actor: SyntheticActor, encounter_id: str, *, idempotency_key: str) -> SyntheticRecord:
        encounter = self._get(self.encounters, encounter_id)
        self._require(actor, actor.id == encounter.fields["practitioner_id"], "lab-order:create")
        if encounter.state != "SIGNED":
            raise SyntheticConflictError("lab order requires signed encounter")
        existing = next((order for order in self.lab_orders.values() if order.fields.get("idempotency_key") == idempotency_key and order.fields.get("organization_id") == actor.organization_id), None)
        if existing:
            return existing
        order = SyntheticRecord(str(uuid4()), "DRAFT", fields={"encounter_id": encounter.id, "patient_id": encounter.fields["patient_id"], "organization_id": actor.organization_id, "idempotency_key": idempotency_key})
        self._transition(order, LAB_ORDER, "PLACED")
        self.lab_orders[order.id] = order
        self._audit(actor, "lab-order.placed", "lab-order", order.id, "DRAFT", order.state, order.version)
        return order

    def collect_and_receive_specimen(self, actor: SyntheticActor, order_id: str, *, idempotency_key: str | None = None) -> SyntheticRecord:
        self._require_active_context(actor, "specimen:collect")
        order = self._get(self.lab_orders, order_id)
        self._require(actor, "lab_technician" in actor.roles and actor.organization_id == order.fields["organization_id"], "specimen:collect")
        with self._clinical_lock:
            if idempotency_key:
                existing_id = self._specimen_idempotency.get((actor.id, idempotency_key))
                if existing_id:
                    return self.specimens[existing_id]
            existing = next((item for item in self.specimens.values() if item.fields.get("order_id") == order.id), None)
            if existing:
                raise SyntheticConflictError("specimen already exists")
            self._transition(order, LAB_ORDER, "ACCEPTED")
            self._transition(order, LAB_ORDER, "IN_PROGRESS")
            specimen = SyntheticRecord(str(uuid4()), "ORDERED", fields={"order_id": order.id, "patient_id": order.fields["patient_id"], "collector_id": actor.id, "receiver_id": actor.id, "organization_id": actor.organization_id, "barcode": f"SYN-{uuid4().hex[:8].upper()}"})
            self._transition(specimen, SPECIMEN, "COLLECTED")
            self._transition(specimen, SPECIMEN, "RECEIVED")
            self._transition(specimen, SPECIMEN, "PROCESSING")
            self._transition(specimen, SPECIMEN, "ANALYZING")
            self.specimens[specimen.id] = specimen
            if idempotency_key:
                self._specimen_idempotency[(actor.id, idempotency_key)] = specimen.id
            self._audit(actor, "specimen.received", "specimen", specimen.id, "COLLECTED", specimen.state, specimen.version)
            return specimen

    def release_result(self, actor: SyntheticActor, specimen_id: str, *, idempotency_key: str | None = None) -> SyntheticRecord:
        self._require_active_context(actor, "result:create")
        specimen = self._get(self.specimens, specimen_id)
        self._require(actor, "lab_technician" in actor.roles and actor.organization_id == specimen.fields["organization_id"], "result:create")
        with self._clinical_lock:
            if idempotency_key:
                existing_id = self._result_idempotency.get((actor.id, idempotency_key))
                if existing_id:
                    return self.results[existing_id]
            if specimen.state != "ANALYZING":
                raise SyntheticConflictError("result requires an analyzing specimen")
            self._transition(specimen, SPECIMEN, "VALIDATED")
            result = SyntheticRecord(str(uuid4()), "DRAFT", fields={"specimen_id": specimen.id, "patient_id": specimen.fields["patient_id"], "organization_id": specimen.fields["organization_id"], "value": "synthetic-normal", "version": 1})
            self._transition(result, RESULT, "TECHNICALLY_VALIDATED")
            self._require(actor, "senior_lab" in actor.roles, "result:clinical_validate")
            self._transition(result, RESULT, "CLINICALLY_VALIDATED")
            self._transition(result, RESULT, "RELEASED")
            self.results[result.id] = result
            if idempotency_key:
                self._result_idempotency[(actor.id, idempotency_key)] = result.id
            self._audit(actor, "result.released", "result", result.id, "CLINICALLY_VALIDATED", result.state, result.version)
            self._transition(order := self._get(self.lab_orders, specimen.fields["order_id"]), LAB_ORDER, "COMPLETED")
            self._audit(actor, "lab-order.completed", "lab-order", order.id, "IN_PROGRESS", order.state, order.version)
            return result

    def grant_result_share(self, actor: SyntheticActor, *, recipient_id: str, recipient_organization_id: str, result_id: str, scope: str, duration_hours: int, idempotency_key: str | None = None) -> SyntheticRecord:
        result = self._get(self.results, result_id)
        self._require(actor, actor.patient_id == result.fields["patient_id"] and result.state == "RELEASED", "consent:grant")
        self._require(actor, actor.organization_id == recipient_organization_id, "consent:recipient_scope")
        self._require(actor, scope == "lab_results" and 1 <= duration_hours <= 72, "consent:bounded_scope")
        with self._clinical_lock:
            if idempotency_key:
                existing_id = self._consent_idempotency.get((actor.id, idempotency_key))
                if existing_id:
                    return self.consents[existing_id]
            if any(consent.state == "ACTIVE" and consent.fields["recipient_id"] == recipient_id and consent.fields["result_id"] == result.id for consent in self.consents.values()):
                raise SyntheticConflictError("active share already exists")
            consent = SyntheticRecord(str(uuid4()), "ACTIVE", fields={"patient_id": actor.patient_id, "recipient_id": recipient_id, "recipient_organization_id": recipient_organization_id, "result_id": result_id, "scope": scope, "expires_at": datetime.now(UTC) + timedelta(hours=duration_hours)})
            self.consents[consent.id] = consent
            if idempotency_key:
                self._consent_idempotency[(actor.id, idempotency_key)] = consent.id
            self.access_history.append({"action": "GRANT_CREATED", "decision": "ALLOW", "result_id": result.id, "actor_id": actor.id, "purpose": "TREATMENT"})
            self._audit(actor, "consent.granted", "consent", consent.id, None, consent.state, consent.version)
            return consent

    def revoke_share(self, actor: SyntheticActor, consent_id: str, *, expected_version: int | None = None, idempotency_key: str | None = None) -> SyntheticRecord:
        consent = self._get(self.consents, consent_id)
        self._require(actor, actor.patient_id == consent.fields["patient_id"], "consent:revoke")
        with self._clinical_lock:
            if idempotency_key:
                existing_id = self._consent_idempotency.get((actor.id, idempotency_key))
                if existing_id:
                    return self.consents[existing_id]
            if expected_version is not None and expected_version != consent.version:
                raise SyntheticConflictError("version conflict")
            if consent.state != "ACTIVE":
                raise SyntheticConflictError("share is not active")
            self._transition(consent, CONSENT, "REVOKED")
            if idempotency_key:
                self._consent_idempotency[(actor.id, idempotency_key)] = consent.id
            self.access_history.append({"action": "GRANT_REVOKED", "decision": "ALLOW", "result_id": consent.fields["result_id"], "actor_id": actor.id, "purpose": "TREATMENT"})
            self._audit(actor, "consent.revoked", "consent", consent.id, "ACTIVE", consent.state, consent.version)
            return consent

    def read_result(self, actor: SyntheticActor, result_id: str) -> SyntheticRecord:
        self._require_active_context(actor, "result:read")
        result = self._get(self.results, result_id)
        if actor.patient_id == result.fields["patient_id"]:
            self._require(actor, result.state == "RELEASED", "result:read")
            return result
        allowed = any(
            consent.state == "ACTIVE"
            and consent.fields["recipient_id"] == actor.id
            and consent.fields["recipient_organization_id"] == actor.organization_id
            and consent.fields["result_id"] == result.id
            and consent.fields["scope"] == "lab_results"
            and consent.fields["expires_at"] > datetime.now(UTC)
            for consent in self.consents.values()
        )
        self._require(actor, allowed, "result:read")
        self.access_history.append({"action": "ACCESS_USED", "decision": "ALLOW", "result_id": result.id, "actor_id": actor.id, "purpose": "TREATMENT"})
        return result

    def list_access_history(self, actor: SyntheticActor, *, result_id: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self._require_active_context(actor, "access:history")
        entries = [entry for entry in self.access_history if result_id is None or entry.get("result_id") == result_id]
        entries = [entry for entry in entries if entry.get("actor_id") == actor.id or actor.patient_id is not None]
        return entries[offset : offset + min(limit, 100)]

    def create_medication(self, actor: SyntheticActor, *, code: str, name: str, idempotency_key: str) -> SyntheticRecord:
        self._require_active_context(actor, "medication:create")
        self._require(actor, bool(actor.roles & {"doctor", "pharmacist", "catalog_manager"}), "medication:create")
        key = (actor.id, f"medication:{idempotency_key}")
        with self._clinical_lock:
            existing_id = self._pharmacy_idempotency.get(key)
            if existing_id:
                existing = self.medications[existing_id]
                if existing.fields["code"] != code or existing.fields["name"] != name:
                    raise SyntheticConflictError("idempotency key reused with a different medication")
                return existing
            medication = SyntheticRecord(str(uuid4()), "ACTIVE", fields={"code": code, "name": name, "organization_id": actor.organization_id, "workspace_id": actor.workspace_id, "stock": 0})
            self.medications[medication.id] = medication
            self._pharmacy_idempotency[key] = medication.id
            self._audit(actor, "medication.created", "medication", medication.id, None, medication.state, medication.version)
            return medication

    def receive_medication_stock(self, actor: SyntheticActor, medication_id: str, *, quantity: int) -> SyntheticRecord:
        self._require_active_context(actor, "inventory:receive")
        self._require(actor, "pharmacist" in actor.roles, "inventory:receive")
        if quantity <= 0:
            raise SyntheticConflictError("stock quantity must be positive")
        medication = self._get(self.medications, medication_id)
        with self._clinical_lock:
            before = int(medication.fields.get("stock", 0))
            medication.fields["stock"] = before + quantity
            medication.version += 1
            self._audit(actor, "inventory.received", "medication", medication.id, str(before), str(medication.fields["stock"]), medication.version)
            return medication

    def create_prescription(self, actor: SyntheticActor, encounter_id: str, *, medication_id: str, quantity: int, idempotency_key: str) -> SyntheticRecord:
        self._require_active_context(actor, "prescription:create")
        self._require(actor, "doctor" in actor.roles, "prescription:create")
        encounter = self._get(self.encounters, encounter_id)
        self._require(actor, actor.id == encounter.fields["practitioner_id"] and encounter.state == "SIGNED", "prescription:create")
        medication = self._get(self.medications, medication_id)
        if quantity <= 0:
            raise SyntheticConflictError("prescription quantity must be positive")
        key = (actor.id, f"prescription:{idempotency_key}")
        with self._clinical_lock:
            existing_id = self._pharmacy_idempotency.get(key)
            if existing_id:
                existing = self.prescriptions[existing_id]
                if existing.fields["medication_id"] != medication.id or existing.fields["quantity"] != quantity:
                    raise SyntheticConflictError("idempotency key reused with a different prescription")
                return existing
            prescription = SyntheticRecord(str(uuid4()), "DRAFT", fields={"encounter_id": encounter.id, "patient_id": encounter.fields["patient_id"], "practitioner_id": actor.id, "medication_id": medication.id, "medication_code": medication.fields["code"], "quantity": quantity, "organization_id": actor.organization_id, "workspace_id": actor.workspace_id})
            self.prescriptions[prescription.id] = prescription
            self._pharmacy_idempotency[key] = prescription.id
            self._audit(actor, "prescription.created", "prescription", prescription.id, None, prescription.state, prescription.version)
            return prescription

    def sign_prescription(self, actor: SyntheticActor, prescription_id: str, *, expected_version: int = 1) -> SyntheticRecord:
        self._require_active_context(actor, "prescription:sign")
        prescription = self._get(self.prescriptions, prescription_id)
        self._require(actor, "doctor" in actor.roles and actor.id == prescription.fields["practitioner_id"], "prescription:sign")
        if prescription.version != expected_version:
            raise SyntheticConflictError("prescription version conflict")
        with self._clinical_lock:
            self._transition(prescription, PRESCRIPTION, "SIGNED")
            self._audit(actor, "prescription.signed", "prescription", prescription.id, "DRAFT", prescription.state, prescription.version)
            return prescription

    def amend_prescription(self, actor: SyntheticActor, prescription_id: str, *, quantity: int, reason: str, expected_version: int) -> SyntheticRecord:
        self._require_active_context(actor, "prescription:amend")
        original = self._get(self.prescriptions, prescription_id)
        self._require(actor, "doctor" in actor.roles and actor.id == original.fields["practitioner_id"], "prescription:amend")
        if original.version != expected_version or original.state not in {"SIGNED", "AMENDED"}:
            raise SyntheticConflictError("prescription is not amendable")
        if not reason.strip() or quantity <= 0:
            raise SyntheticConflictError("amendment reason and positive quantity are required")
        with self._clinical_lock:
            new_version = original.version + 1
            self._transition(original, PRESCRIPTION, "AMENDED")
            amended = SyntheticRecord(str(uuid4()), "DRAFT", version=new_version, fields={**original.fields, "quantity": quantity, "amendment_reason": reason.strip(), "supersedes_id": original.id})
            self.prescriptions[amended.id] = amended
            self._audit(actor, "prescription.amended", "prescription", amended.id, "SIGNED", amended.state, amended.version)
            return amended

    def prepare_dispense(self, actor: SyntheticActor, prescription_id: str, *, quantity: int, idempotency_key: str) -> SyntheticRecord:
        self._require_active_context(actor, "dispense:prepare")
        self._require(actor, "pharmacist" in actor.roles, "dispense:prepare")
        prescription = self._get(self.prescriptions, prescription_id)
        self._require(actor, prescription.state in {"SIGNED", "AMENDED"} and actor.organization_id == prescription.fields["organization_id"], "dispense:prepare")
        medication = self._get(self.medications, prescription.fields["medication_id"])
        if quantity <= 0 or quantity > prescription.fields["quantity"]:
            raise SyntheticConflictError("over-dispense")
        key = (actor.id, f"dispense:{idempotency_key}")
        with self._clinical_lock:
            existing_id = self._pharmacy_idempotency.get(key)
            if existing_id:
                return self.dispenses[existing_id]
            fulfilled = sum(item.fields["quantity"] for item in self.dispenses.values() if item.fields["prescription_id"] == prescription.id and item.state in {"PARTIAL", "COMPLETED"})
            if quantity > prescription.fields["quantity"] - fulfilled:
                raise SyntheticConflictError("over-dispense")
            if medication.fields.get("stock", 0) < quantity:
                raise SyntheticConflictError("insufficient stock")
            dispense = SyntheticRecord(str(uuid4()), "PREPARED", fields={"prescription_id": prescription.id, "medication_id": medication.id, "quantity": quantity, "prepared_by": actor.id, "organization_id": actor.organization_id, "workspace_id": actor.workspace_id})
            self.dispenses[dispense.id] = dispense
            self._pharmacy_idempotency[key] = dispense.id
            self._audit(actor, "dispense.prepared", "dispense", dispense.id, None, dispense.state, dispense.version)
            return dispense

    def complete_dispense(self, actor: SyntheticActor, dispense_id: str, *, expected_version: int = 1) -> SyntheticRecord:
        self._require_active_context(actor, "dispense:complete")
        self._require(actor, "pharmacist" in actor.roles, "dispense:complete")
        dispense = self._get(self.dispenses, dispense_id)
        self._require(actor, actor.id != dispense.fields["prepared_by"] and actor.organization_id == dispense.fields["organization_id"], "dispense:complete")
        if dispense.version != expected_version or dispense.state != "PREPARED":
            raise SyntheticConflictError("dispense version or state conflict")
        with self._clinical_lock:
            medication = self._get(self.medications, dispense.fields["medication_id"])
            if medication.fields.get("stock", 0) < dispense.fields["quantity"]:
                raise SyntheticConflictError("insufficient stock")
            prescription = self._get(self.prescriptions, dispense.fields["prescription_id"])
            fulfilled = sum(item.fields["quantity"] for item in self.dispenses.values() if item.fields["prescription_id"] == prescription.id and item.state in {"PARTIAL", "COMPLETED"})
            next_state = "COMPLETED" if fulfilled + dispense.fields["quantity"] >= prescription.fields["quantity"] else "PARTIAL"
            medication.fields["stock"] -= dispense.fields["quantity"]
            medication.version += 1
            self._transition(dispense, DISPENSE, next_state)
            dispense.fields["verified_by"] = actor.id
            dispense.fields["dispensed_by"] = actor.id
            self._audit(actor, "dispense.completed", "dispense", dispense.id, "PREPARED", dispense.state, dispense.version)
            return dispense

    def place_imaging_order(self, actor: SyntheticActor, encounter_id: str, *, modality: str, idempotency_key: str) -> SyntheticRecord:
        self._require_active_context(actor, "imaging-order:create")
        self._require(actor, "doctor" in actor.roles, "imaging-order:create")
        encounter = self._get(self.encounters, encounter_id)
        self._require(actor, actor.id == encounter.fields["practitioner_id"] and encounter.state == "SIGNED", "imaging-order:create")
        key = (actor.id, f"imaging-order:{idempotency_key}")
        with self._clinical_lock:
            existing_id = self._imaging_idempotency.get(key)
            if existing_id:
                return self.imaging_orders[existing_id]
            order = SyntheticRecord(str(uuid4()), "DRAFT", fields={"encounter_id": encounter.id, "patient_id": encounter.fields["patient_id"], "practitioner_id": actor.id, "modality": modality, "organization_id": actor.organization_id, "workspace_id": actor.workspace_id, "accession": f"SYN-ACC-{uuid4().hex[:10].upper()}"})
            self._transition(order, IMAGING_ORDER, "PLACED")
            self.imaging_orders[order.id] = order
            self._imaging_idempotency[key] = order.id
            self._audit(actor, "imaging-order.placed", "imaging-order", order.id, "DRAFT", order.state, order.version)
            return order

    def ingest_imaging_study(self, actor: SyntheticActor, order_id: str, *, study_uid: str, source_message_id: str, idempotency_key: str) -> SyntheticRecord:
        self._require_active_context(actor, "imaging-study:ingest")
        self._require(actor, bool(actor.roles & {"imaging_technician", "imaging_adapter"}), "imaging-study:ingest")
        order = self._get(self.imaging_orders, order_id)
        self._require(actor, actor.organization_id == order.fields["organization_id"], "imaging-study:ingest")
        key = (actor.id, f"imaging-study:{idempotency_key}")
        with self._clinical_lock:
            existing_id = self._imaging_idempotency.get(key)
            if existing_id:
                return self.imaging_studies[existing_id]
            if study_uid in self._used_dicom_uids or any(item.fields["source_message_id"] == source_message_id for item in self.imaging_studies.values()):
                raise SyntheticConflictError("duplicate DICOM source message or study UID")
            if order.state == "PLACED":
                self._transition(order, IMAGING_ORDER, "SCHEDULED")
            if order.state == "SCHEDULED":
                self._transition(order, IMAGING_ORDER, "IN_PROGRESS")
            study = SyntheticRecord(str(uuid4()), "RECEIVED", fields={"order_id": order.id, "patient_id": order.fields["patient_id"], "study_uid": study_uid, "source_message_id": source_message_id, "organization_id": order.fields["organization_id"], "workspace_id": order.fields["workspace_id"], "instances": 0})
            self.imaging_studies[study.id] = study
            self._imaging_idempotency[key] = study.id
            self._used_dicom_uids.add(study_uid)
            self._audit(actor, "imaging-study.received", "imaging-study", study.id, None, study.state, study.version)
            return study

    def complete_imaging_study(self, actor: SyntheticActor, study_id: str) -> SyntheticRecord:
        self._require_active_context(actor, "imaging-study:complete")
        self._require(actor, "imaging_technician" in actor.roles, "imaging-study:complete")
        study = self._get(self.imaging_studies, study_id)
        self._require(actor, actor.organization_id == study.fields["organization_id"], "imaging-study:complete")
        with self._clinical_lock:
            self._transition(study, IMAGING_STUDY, "MATCHED")
            self._transition(study, IMAGING_STUDY, "ACQUIRED")
            self._transition(study, IMAGING_STUDY, "COMPLETED")
            order = self._get(self.imaging_orders, study.fields["order_id"])
            if order.state == "IN_PROGRESS":
                self._transition(order, IMAGING_ORDER, "COMPLETED")
            self._audit(actor, "imaging-study.completed", "imaging-study", study.id, "RECEIVED", study.state, study.version)
            return study

    def release_imaging_report(self, actor: SyntheticActor, study_id: str, *, critical: bool = False) -> SyntheticRecord:
        self._require_active_context(actor, "imaging-report:release")
        self._require(actor, "radiologist" in actor.roles, "imaging-report:release")
        study = self._get(self.imaging_studies, study_id)
        self._require(actor, study.state == "COMPLETED" and actor.organization_id == study.fields["organization_id"], "imaging-report:release")
        with self._clinical_lock:
            report = SyntheticRecord(str(uuid4()), "DRAFT", fields={"study_id": study.id, "patient_id": study.fields["patient_id"], "radiologist_id": actor.id, "impression": "synthetic impression", "critical": critical, "organization_id": study.fields["organization_id"], "workspace_id": study.fields["workspace_id"]})
            self._transition(report, IMAGING_REPORT, "SIGNED")
            self._transition(report, IMAGING_REPORT, "RELEASED")
            self.imaging_reports[report.id] = report
            self._audit(actor, "imaging-report.released", "imaging-report", report.id, "DRAFT", report.state, report.version)
            return report

    def unified_clinical_record(self, actor: SyntheticActor, *, patient_id: str, limit: int = 50, cursor: str | None = None, sections: frozenset[str] | None = None) -> dict[str, Any]:
        self._require_active_context(actor, "clinical-record:read")
        allowed_sections = {"encounters", "medications", "imaging", "timeline"}
        requested = sections or frozenset(allowed_sections)
        self._require(actor, requested.issubset(allowed_sections), "clinical-record:sections")
        self._require(actor, actor.patient_id == patient_id or "record_reader" in actor.roles, "clinical-record:read")
        if not 1 <= limit <= 100:
            raise SyntheticConflictError("record limit is out of bounds")
        try:
            start = int(cursor or "0")
        except ValueError as exc:
            raise SyntheticConflictError("invalid record cursor") from exc
        if start < 0:
            raise SyntheticConflictError("invalid record cursor")
        events: list[dict[str, Any]] = []
        if "encounters" in requested or "timeline" in requested:
            events.extend({"type": "encounter", "id": row.id, "status": row.state, "source": {"domain": "encounter", "version": row.version}} for row in self.encounters.values() if row.fields.get("patient_id") == patient_id and row.state == "SIGNED")
        if "medications" in requested or "timeline" in requested:
            events.extend({"type": "prescription", "id": row.id, "status": row.state, "source": {"domain": "pharmacy", "version": row.version}, "medication_code": row.fields["medication_code"], "quantity": row.fields["quantity"]} for row in self.prescriptions.values() if row.fields.get("patient_id") == patient_id and row.state in {"SIGNED", "AMENDED", "COMPLETED"})
        if "imaging" in requested or "timeline" in requested:
            events.extend({"type": "imaging_report", "id": row.id, "status": row.state, "source": {"domain": "imaging", "version": row.version}, "impression": row.fields["impression"]} for row in self.imaging_reports.values() if row.fields.get("patient_id") == patient_id and row.state == "RELEASED")
        page = events[start : start + limit]
        next_cursor = str(start + limit) if start + limit < len(events) else None
        self._audit(actor, "clinical-record.projected", "clinical-record", patient_id, None, "PROJECTED", 1)
        return {"state": "PROJECTED", "patient_id": patient_id, "items": page, "next_cursor": next_cursor, "minimum_necessary": True}

    def _require_active_context(self, actor: SyntheticActor, action: str) -> None:
        # Existing legacy fixtures omit identity/session objects; retain their
        # appointment semantics while making the new context-aware path strict.
        if actor.account_id is None and actor.session_id is None and actor.identity_id is None:
            return
        identity = self.identities.get(actor.identity_id or "")
        session = self.sessions.get(actor.session_id or "")
        workspace = self.workspaces.get(actor.workspace_id)
        membership = self.memberships.get((actor.account_id or "", actor.workspace_id))
        now = datetime.now(UTC)
        valid = (
            identity is not None
            and identity.active
            and identity.account_id == actor.account_id
            and session is not None
            and session.account_id == actor.account_id
            and session.state == "ACTIVE"
            and session.expires_at.replace(tzinfo=UTC) > now
            and workspace is not None
            and workspace.active
            and workspace.organization_id == actor.organization_id
            and membership is not None
            and membership.active
            and actor.roles.issubset(membership.roles)
        )
        self._require(actor, valid, action)

    @staticmethod
    def _get(collection: dict[str, SyntheticRecord], record_id: str) -> SyntheticRecord:
        try:
            return collection[record_id]
        except KeyError as exc:
            raise SyntheticCoreError("record not found") from exc

    @staticmethod
    def _require(actor: SyntheticActor, condition: bool, action: str) -> None:
        if not condition:
            raise SyntheticAuthorizationError(f"DENY:{action}")

    @staticmethod
    def _transition(record: SyntheticRecord, contract: Any, requested: str) -> None:
        previous = record.state
        try:
            require_transition(contract.domain, previous, requested)
        except (KeyError, ValueError) as exc:
            raise SyntheticConflictError(str(exc)) from exc
        record.state = requested
        record.version += 1

    def _audit(self, actor: SyntheticActor, action: str, entity_type: str, entity_id: str, before: str | None, after: str | None, version: int) -> None:
        self.audit.append(SyntheticAuditEvent(actor.id, action, entity_type, entity_id, before, after, version))
