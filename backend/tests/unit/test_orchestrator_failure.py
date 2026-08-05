"""Unit tests for GULA-ORCHESTRATOR-001 — Phase 6 Failure Manager."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.orchestrator.failure import (
    classify_failure,
    escalate,
    retry_allowed,
)


class TestClassification:
    def test_timeout_is_temporary(self):
        d = classify_failure("OTASK-1", "request timed out after 30s")
        assert d.failure_class == "temporary"
        assert d.action == "retry"
        assert d.retry_allowed

    def test_connection_refused_is_temporary(self):
        d = classify_failure("OTASK-1", "connection refused to postgres")
        assert d.failure_class == "temporary"

    def test_unauthorized_is_credential(self):
        d = classify_failure("OTASK-1", "401 unauthorized: invalid api-key")
        assert d.failure_class == "credential"
        assert d.human_action_required

    def test_missing_config_is_configuration(self):
        d = classify_failure("OTASK-1", "KeyError: MISSING_ENV")
        assert d.failure_class == "configuration"

    def test_type_error_is_implementation(self):
        d = classify_failure("OTASK-1", "TypeError: 'NoneType' is not callable")
        assert d.failure_class == "implementation"
        assert d.action == "resume_after_fix"

    def test_unknown_is_permanent(self):
        d = classify_failure("OTASK-1", "an inexplicable cosmic error")
        assert d.failure_class == "permanent"
        assert d.action == "escalate"

    def test_503_is_temporary(self):
        d = classify_failure("OTASK-1", "503 service temporarily unavailable")
        assert d.failure_class == "temporary"

    def test_docker_error_is_infrastructure(self):
        d = classify_failure("OTASK-1", "docker daemon not responding")
        assert d.failure_class == "infrastructure"


class TestActions:
    def test_retry_allowed_under_budget(self):
        d = classify_failure("OTASK-1", "timeout")
        assert retry_allowed(d, attempt=0)
        assert retry_allowed(d, attempt=2)
        assert not retry_allowed(d, attempt=3)

    def test_non_retryable_never_retries(self):
        d = classify_failure("OTASK-1", "401 unauthorized")
        assert not retry_allowed(d, attempt=0)

    def test_escalate_requires_human_for_credential(self):
        d = classify_failure("OTASK-1", "invalid api token")
        assert escalate(d)

    def test_temporary_not_escalated(self):
        d = classify_failure("OTASK-1", "timeout")
        assert not escalate(d)


class TestDeterminism:
    def test_classification_is_deterministic(self):
        a = classify_failure("OTASK-1", "connection refused to postgres")
        b = classify_failure("OTASK-1", "connection refused to postgres")
        assert a.failure_class == b.failure_class
        assert a.action == b.action
