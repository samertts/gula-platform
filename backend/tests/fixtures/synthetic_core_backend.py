from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any
from uuid import uuid4

from app.contracts.clinical_core import (
    APPOINTMENT,
    CLINICAL_NOTE,
    CONSENT,
    ENCOUNTER,
    LAB_ORDER,
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
        self._appointment_idempotency: dict[tuple[str, str], str] = {}
        self._used_slots: dict[tuple[str, str], str] = {}
        self.audit: list[SyntheticAuditEvent] = []
        self._booking_lock = Lock()

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

    def collect_and_receive_specimen(self, actor: SyntheticActor, order_id: str) -> SyntheticRecord:
        order = self._get(self.lab_orders, order_id)
        self._require(actor, "lab_technician" in actor.roles and actor.organization_id == order.fields["organization_id"], "specimen:collect")
        self._transition(order, LAB_ORDER, "ACCEPTED")
        self._transition(order, LAB_ORDER, "IN_PROGRESS")
        specimen = SyntheticRecord(str(uuid4()), "ORDERED", fields={"order_id": order.id, "patient_id": order.fields["patient_id"], "collector_id": actor.id, "receiver_id": actor.id, "organization_id": actor.organization_id, "barcode": f"SYN-{uuid4().hex[:8].upper()}"})
        self._transition(specimen, SPECIMEN, "COLLECTED")
        self._transition(specimen, SPECIMEN, "RECEIVED")
        self._transition(specimen, SPECIMEN, "PROCESSING")
        self._transition(specimen, SPECIMEN, "ANALYZING")
        self.specimens[specimen.id] = specimen
        self._audit(actor, "specimen.received", "specimen", specimen.id, "COLLECTED", specimen.state, specimen.version)
        return specimen

    def release_result(self, actor: SyntheticActor, specimen_id: str) -> SyntheticRecord:
        specimen = self._get(self.specimens, specimen_id)
        self._require(actor, "lab_technician" in actor.roles and actor.organization_id == specimen.fields["organization_id"], "result:create")
        self._transition(specimen, SPECIMEN, "VALIDATED")
        result = SyntheticRecord(str(uuid4()), "DRAFT", fields={"specimen_id": specimen.id, "patient_id": specimen.fields["patient_id"], "organization_id": specimen.fields["organization_id"], "value": "synthetic-normal"})
        self._transition(result, RESULT, "TECHNICALLY_VALIDATED")
        self._require(actor, "senior_lab" in actor.roles, "result:clinical_validate")
        self._transition(result, RESULT, "CLINICALLY_VALIDATED")
        self._transition(result, RESULT, "RELEASED")
        self.results[result.id] = result
        self._audit(actor, "result.released", "result", result.id, "CLINICALLY_VALIDATED", result.state, result.version)
        self._transition(order := self._get(self.lab_orders, specimen.fields["order_id"]), LAB_ORDER, "COMPLETED")
        self._audit(actor, "lab-order.completed", "lab-order", order.id, "IN_PROGRESS", order.state, order.version)
        return result

    def grant_result_share(self, actor: SyntheticActor, *, recipient_id: str, recipient_organization_id: str, result_id: str, scope: str, duration_hours: int) -> SyntheticRecord:
        self._require(actor, actor.patient_id == self._get(self.results, result_id).fields["patient_id"], "consent:grant")
        self._require(actor, actor.organization_id == recipient_organization_id, "consent:recipient_scope")
        consent = SyntheticRecord(str(uuid4()), "ACTIVE", fields={"patient_id": actor.patient_id, "recipient_id": recipient_id, "recipient_organization_id": recipient_organization_id, "result_id": result_id, "scope": scope, "expires_at": datetime.now(UTC) + timedelta(hours=duration_hours)})
        self.consents[consent.id] = consent
        self._audit(actor, "consent.granted", "consent", consent.id, None, consent.state, consent.version)
        return consent

    def revoke_share(self, actor: SyntheticActor, consent_id: str) -> SyntheticRecord:
        consent = self._get(self.consents, consent_id)
        self._require(actor, actor.patient_id == consent.fields["patient_id"], "consent:revoke")
        self._transition(consent, CONSENT, "REVOKED")
        self._audit(actor, "consent.revoked", "consent", consent.id, "ACTIVE", consent.state, consent.version)
        return consent

    def read_result(self, actor: SyntheticActor, result_id: str) -> SyntheticRecord:
        result = self._get(self.results, result_id)
        if actor.patient_id == result.fields["patient_id"]:
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
        return result

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
