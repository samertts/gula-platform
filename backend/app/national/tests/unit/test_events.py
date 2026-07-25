from __future__ import annotations

from app.national.events import (
    CitizenCreated,
    EncounterCreated,
    FamilyCreated,
    IdentityMergeApproved,
    WorkflowCompleted,
    WorkflowStarted,
)


class TestDomainEvents:
    def test_citizen_created_event(self):
        event = CitizenCreated(aggregate_id="CIT001", payload={"first_name": "Ali"})
        assert event.event_type == "national.citizen.created"
        assert event.aggregate_id == "CIT001"
        assert event.timestamp != ""

    def test_encounter_created_event(self):
        event = EncounterCreated(aggregate_id="ENC001", payload={"type": "outpatient"})
        assert event.event_type == "national.encounter.created"

    def test_family_created_event(self):
        event = FamilyCreated(aggregate_id="FAM001", payload={"name": "Al-Hassan"})
        assert event.event_type == "national.family.created"

    def test_workflow_events(self):
        start = WorkflowStarted(aggregate_id="WF001")
        complete = WorkflowCompleted(aggregate_id="WF001")
        assert start.event_type == "national.workflow.started"
        assert complete.event_type == "national.workflow.completed"

    def test_identity_events(self):
        merge = IdentityMergeApproved(
            aggregate_id="MERGE001", payload={"primary": "CIT001", "secondary": "CIT002"},
        )
        assert merge.event_type == "national.identity.merge_approved"

    def test_event_correlation(self):
        event = CitizenCreated(aggregate_id="CIT001")
        assert event.correlation_id == "CIT001"
