"""Unit tests for GULA-BUILDER-001 Phase 3 — Engineering Analyzer."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.builder.analyzer import analyze
from scripts.builder.impact import analyze_impact, impact_summary


class TestImpact:
    def test_backend_feature(self):
        impact = analyze_impact(analyze("Build Patient Management with API"))
        assert "backend/app" in impact.affected_modules
        assert "api" in impact.affected_apis

    def test_database_signals(self):
        impact = analyze_impact(analyze("Add database migration for patients"))
        assert "database" in impact.affected_database or "migration" in impact.affected_database

    def test_frontend_signals(self):
        impact = analyze_impact(analyze("Build a dashboard page in the frontend"))
        assert "frontend-v3/src" in impact.affected_frontend

    def test_registry_always_touched(self):
        impact = analyze_impact(analyze("Fix a small bug"))
        assert impact.affected_registry
        assert ".ai/core/registry/REGISTRY.md" in impact.affected_registry

    def test_knowledge_index_touched(self):
        impact = analyze_impact(analyze("Fix a small bug"))
        assert ".ai/core/index/INDEX.md" in impact.affected_knowledge

    def test_security_type(self):
        impact = analyze_impact(analyze("Add security audit logging"))
        assert "security config" in impact.affected_security or impact.affected_security

    def test_no_duplicates(self):
        impact = analyze_impact(analyze("Add api and api and api"))
        for area in impact.to_dict():
            values = getattr(impact, area)
            if isinstance(values, list):
                assert len(values) == len(set(values))

    def test_to_dict(self):
        impact = analyze_impact(analyze("Build Patient Management"))
        data = impact.to_dict()
        assert data["mission_id"]
        assert "affected_modules" in data

    def test_summary(self):
        impact = analyze_impact(analyze("Build Patient Management"))
        summary = impact_summary(impact)
        assert impact.mission_id in summary
        assert "areas" in summary
