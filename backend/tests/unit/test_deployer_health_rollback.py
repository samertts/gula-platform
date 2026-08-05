"""Unit tests for GULA-DEPLOYER-001 — Phase 4 health + Phase 5 rollback."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.deployer.core import DeploymentSnapshot, ValidationCheck
from scripts.deployer.health import (
    CRITICAL_COMPONENTS,
    HEALTH_ENDPOINTS,
    deployment_rejected,
    health_endpoint,
    run_validation,
    validation_summary,
)
from scripts.deployer.rollback import (
    automatic_rollback,
    capture_snapshot,
    rollback_plan,
    verify_restore,
    version_history,
)


class TestHealth:
    def test_health_endpoint_for_api(self):
        assert "/health" in health_endpoint("api")

    def test_endpoints_cover_critical_components(self):
        for component in CRITICAL_COMPONENTS:
            assert component in HEALTH_ENDPOINTS

    def test_run_validation_all_healthy(self):
        checks = run_validation()
        assert len(checks) == len(HEALTH_ENDPOINTS)
        assert all(c.status == "pass" for c in checks)

    def test_run_validation_unhealthy_detected(self):
        checks = run_validation(healthy={"api", "database"})
        failed = [c for c in checks if c.status == "fail"]
        assert failed
        assert any(c.component == "redis" for c in failed)

    def test_latency_captured(self):
        checks = run_validation(latencies={"api": 250})
        api = next(c for c in checks if c.component == "api")
        assert api.latency_ms == 250

    def test_deployment_rejected_on_fail(self):
        checks = [ValidationCheck(component="api", check="reachable", status="fail")]
        assert deployment_rejected(checks) is True

    def test_deployment_accepted_when_healthy(self):
        checks = [ValidationCheck(component="api", check="reachable", status="pass")]
        assert deployment_rejected(checks) is False

    def test_critical_component_failure_rejects(self):
        checks = run_validation(healthy=set(HEALTH_ENDPOINTS) - {"database"})
        assert deployment_rejected(checks) is True

    def test_validation_summary_reports_counts(self):
        checks = run_validation()
        summary = validation_summary(checks)
        assert "pass" in summary


class TestRollback:
    def test_capture_snapshot_creates_id(self):
        snapshot = capture_snapshot("DEP-1", "1.0.0")
        assert snapshot.snapshot_id.startswith("SNAP-")
        assert snapshot.version == "1.0.0"

    def test_version_history_sorts_desc(self):
        records = [
            {"version": "1.0.0", "status": "live"},
            {"version": "1.1.0", "status": "rolled_back"},
        ]
        history = version_history(records)
        assert history[0]["version"] == "1.1.0"

    def test_rollback_plan_includes_three_kinds(self):
        snapshot = capture_snapshot("DEP-1", "1.0.0")
        plan = rollback_plan(snapshot)
        assert plan["snapshot_id"] == snapshot.snapshot_id
        assert plan["kinds"] == ["version", "configuration", "database"]
        assert plan["verify_after"] is True

    def test_automatic_rollback_triggers_on_reject(self):
        snapshot = capture_snapshot("DEP-1", "1.0.0")
        checks = [ValidationCheck(component="api", check="reachable", status="fail")]
        result = automatic_rollback(checks, snapshot)
        assert result["rolled_back"] is True
        assert result["snapshot_id"] == snapshot.snapshot_id
        assert result["restored"]["version"] == "1.0.0"

    def test_automatic_rollback_skips_when_healthy(self):
        snapshot = capture_snapshot("DEP-1", "1.0.0")
        checks = [ValidationCheck(component="api", check="reachable", status="pass")]
        result = automatic_rollback(checks, snapshot)
        assert result["rolled_back"] is False

    def test_verify_restore_requires_all(self):
        snapshot = capture_snapshot("DEP-1", "1.0.0")
        checks = [ValidationCheck(component="api", check="reachable", status="fail")]
        restored = automatic_rollback(checks, snapshot)
        assert verify_restore(restored) is True

    def test_verify_restore_fails_missing_database(self):
        assert verify_restore({"restored": {"version": "1.0.0", "configuration": "cfg"}}) is False

    def test_verify_restore_fails_missing_keys(self):
        assert verify_restore({}) is False

    def test_snapshot_default_backups_empty(self):
        snapshot = DeploymentSnapshot(snapshot_id="SNAP-1", deployment_id="DEP-1", version="1.0.0")
        assert snapshot.database_backup == ""
        assert snapshot.storage_backup == ""
