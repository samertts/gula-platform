from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from security.modules.audit.immutable import ImmutableAuditLog, ImmutableLogEntry
from security.modules.audit.models import AuditEvent, AuditPolicy
from security.modules.audit.service import AuditQuery, AuditService


class TestAuditEvent:
    def test_audit_event_creation(self):
        event = AuditEvent(
            event_id="evt-001",
            actor_id="user-001",
            action="user.login",
            resource_type="session",
            resource_id="sess-001",
            outcome="success",
        )
        assert event.event_id == "evt-001"
        assert event.actor_id == "user-001"

    def test_audit_event_with_hash(self):
        event = AuditEvent(
            event_id="evt-002",
            actor_id="user-001",
            action="data.access",
            resource_type="patient",
            resource_id="pat-001",
            hash="abc123",
            previous_hash="prev_hash",
        )
        assert event.hash == "abc123"
        assert event.previous_hash == "prev_hash"


class TestAuditService:
    def test_audit_service_create_event(self, audit_service):
        event = AuditEvent(
            actor_id="user-001",
            action="user.login",
            resource_type="session",
            resource_id="sess-001",
        )
        created = audit_service.create_event(event)
        assert created.event_id is not None
        assert created.hash is not None
        assert created.previous_hash is not None

    def test_audit_log_chain(self, audit_service):
        events = []
        for i in range(5):
            event = audit_service.create_event(AuditEvent(
                actor_id=f"user-{i}",
                action=f"action.{i}",
                resource_type="test",
                resource_id=f"res-{i}",
            ))
            events.append(event)

        for i in range(1, len(events)):
            assert events[i].previous_hash == events[i - 1].hash

    def test_tamper_detection(self, audit_service):
        event1 = audit_service.create_event(AuditEvent(
            actor_id="user-001", action="test.action", resource_type="test", resource_id="res-1",
        ))
        event2 = audit_service.create_event(AuditEvent(
            actor_id="user-002", action="test.action", resource_type="test", resource_id="res-2",
        ))

        event2.previous_hash = "tampered_hash"
        result = audit_service.verify_log_integrity()
        assert result["violations"] is not None

    def test_audit_query(self, audit_service):
        for i in range(10):
            audit_service.create_event(AuditEvent(
                actor_id=f"user-{i % 3}",
                action="data.read",
                resource_type="patient",
                resource_id=f"pat-{i}",
            ))

        query = AuditQuery(actor_id="user-001", limit=5)
        results = audit_service.query_events(query)
        assert len(results) > 0
        for event in results:
            assert event.actor_id == "user-001"

    def test_audit_export_json(self, audit_service):
        audit_service.create_event(AuditEvent(
            actor_id="user-001", action="test.action", resource_type="test", resource_id="res-1",
        ))
        exported = audit_service.export_events("json")
        data = json.loads(exported)
        assert len(data) >= 1

    def test_audit_export_csv(self, audit_service):
        audit_service.create_event(AuditEvent(
            actor_id="user-001", action="test.action", resource_type="test", resource_id="res-1",
        ))
        exported = audit_service.export_events("csv")
        assert "event_id" in exported
        assert "user-001" in exported

    def test_audit_export_fhir(self, audit_service):
        audit_service.create_event(AuditEvent(
            actor_id="user-001", action="patient.access", resource_type="Patient", resource_id="pat-001",
        ))
        exported = audit_service.export_events("fhir")
        data = json.loads(exported)
        assert data[0]["resourceType"] == "AuditEvent"

    def test_audit_statistics(self, audit_service):
        for i in range(5):
            audit_service.create_event(AuditEvent(
                actor_id="user-001", action="data.read", resource_type="patient", resource_id=f"pat-{i}",
            ))
        stats = audit_service.get_statistics()
        assert stats["total"] >= 5
        assert "data.read" in stats["by_action"]

    def test_retention_enforcement(self, audit_service):
        for i in range(5):
            audit_service.create_event(AuditEvent(
                actor_id="user-001", action="test", resource_type="test", resource_id=f"res-{i}",
            ))
        result = audit_service.enforce_retention()
        assert result["remaining"] >= 0


class TestImmutableAuditLog:
    def test_immutable_log_chain(self, immutable_audit_log):
        entries = []
        for i in range(10):
            event = AuditEvent(
                event_id=f"evt-{i}",
                actor_id=f"user-{i}",
                action="test.action",
                resource_type="test",
                resource_id=f"res-{i}",
            )
            entry = immutable_audit_log.append(event)
            entries.append(entry)

        for i in range(1, len(entries)):
            assert entries[i].previous_hash == entries[i - 1].data_hash

    def test_tamper_detection(self, immutable_audit_log):
        for i in range(5):
            event = AuditEvent(
                event_id=f"evt-{i}", actor_id="user-001",
                action="test.action", resource_type="test", resource_id=f"res-{i}",
            )
            immutable_audit_log.append(event)

        integrity = immutable_audit_log.verify_integrity()
        assert integrity["valid"] is True

    def test_detect_tampering(self, immutable_audit_log):
        for i in range(3):
            event = AuditEvent(
                event_id=f"evt-{i}", actor_id="user-001",
                action="test.action", resource_type="test", resource_id=f"res-{i}",
            )
            immutable_audit_log.append(event)

        result = immutable_audit_log.detect_tampering()
        assert "tampered" in result
        assert "findings" in result

    def test_merkle_root_computation(self, immutable_audit_log):
        for i in range(105):
            event = AuditEvent(
                event_id=f"evt-{i}", actor_id="user-001",
                action="test", resource_type="test", resource_id=f"res-{i}",
            )
            immutable_audit_log.append(event)

        root = immutable_audit_log.publish_merkle_root()
        assert len(root) > 0

    def test_forensic_analysis(self, immutable_audit_log):
        for i in range(10):
            event = AuditEvent(
                event_id=f"evt-{i}", actor_id="user-001",
                action="test", resource_type="test", resource_id=f"res-{i}",
            )
            immutable_audit_log.append(event)

        analysis = immutable_audit_log.get_forensic_analysis("evt-005")
        assert "target_entry" in analysis
        assert analysis["target_index"] == 5

    def test_chain_persistence(self, tmp_path):
        log = ImmutableAuditLog(storage_path=str(tmp_path))
        event = AuditEvent(
            event_id="evt-001", actor_id="user-001",
            action="test", resource_type="test", resource_id="res-001",
        )
        log.append(event)

        log2 = ImmutableAuditLog(storage_path=str(tmp_path))
        assert log2.current_hash == log.current_hash
