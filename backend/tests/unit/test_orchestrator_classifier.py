"""Unit tests for GULA-ORCHESTRATOR-001 — Phase 1 Classifier."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.orchestrator.classifier import classify


class TestMissionTypeDetection:
    def test_build_detects_feature(self):
        c = classify("Build Patient Management")
        assert c.mission_type == "feature"

    def test_bug_detection(self):
        c = classify("Fix the login crash")
        assert c.mission_type == "bug"

    def test_refactor_detection(self):
        c = classify("Refactor the service layer")
        assert c.mission_type == "refactor"

    def test_deploy_detection(self):
        c = classify("Deploy the release to staging")
        assert c.mission_type == "deployment"

    def test_security_detection(self):
        c = classify("Harden the authentication system")
        assert c.mission_type == "security"

    def test_documentation_detection(self):
        c = classify("Document the FHIR API")
        assert c.mission_type == "documentation"

    def test_research_detection(self):
        c = classify("Investigate the message queue options")
        assert c.mission_type == "research"

    def test_unknown_objective_defaults_research(self):
        c = classify("zzz zzz")
        assert c.mission_type == "research"

    def test_empty_objective_raises_value_error(self):
        import pytest

        with pytest.raises(ValueError):
            classify("")

    def test_priority_assigned(self):
        c = classify("Deploy the release to production now")
        assert c.priority in {"low", "medium", "high", "critical"}

    def test_complexity_assigned(self):
        c = classify("Build a full national FHIR platform")
        assert c.complexity in {"trivial", "low", "moderate", "high", "critical"}

    def test_risk_assigned(self):
        c = classify("Harden the authentication system")
        assert c.risk in {"negligible", "low", "moderate", "high", "critical"}

    def test_duration_positive(self):
        c = classify("Build Patient Management")
        assert c.duration_minutes > 0

    def test_required_specialists_for_feature(self):
        c = classify("Build Patient Management")
        assert "builder" in c.required_specialists

    def test_rationale_recorded(self):
        c = classify("Build Patient Management")
        assert c.rationale

    def test_classified_at_set(self):
        c = classify("Build Patient Management")
        assert c.classified_at


class TestDeterminism:
    def test_classify_is_deterministic(self):
        assert classify("Build Patient Management").mission_type == classify(
            "Build Patient Management"
        ).mission_type
        assert classify("Fix the login crash").mission_type == classify(
            "Fix the login crash"
        ).mission_type
