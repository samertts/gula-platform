"""Unit tests for GULA-ARCHITECT-001 — audit (Phase 0) + system model (Phase 1)."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.architect.audit import (
    AUDIT_PATTERNS,
    audit_system,
    render_markdown,
)
from scripts.architect.core import BOUNDED_CONTEXT_SEEDS, TRUST_BOUNDARIES
from scripts.architect.model import (
    CONTEXT_TRUST,
    build_model,
    build_relationships,
    persist_model,
)


class TestAudit:
    def test_audit_patterns_cover_all_components(self):
        from scripts.architect.core import ARCHITECTURE_COMPONENTS

        for component in ARCHITECTURE_COMPONENTS:
            assert component in AUDIT_PATTERNS

    def test_audit_system_returns_sixteen_items(self):
        items = audit_system()
        assert len(items) == 16
        assert all(item.item_id.startswith("ARC-") for item in items)

    def test_audit_detects_backend(self):
        items = {item.title: item for item in audit_system()}
        assert items["backend"].status == "measured"
        assert "backend/app" in items["backend"].body

    def test_audit_render_contains_verdict(self):
        text = render_markdown(audit_system())
        assert "ARCHITECTURE AUDIT COMPLETE" in text
        assert "architecture surfaces present" in text

    def test_audit_fhir_hl7_present(self):
        items = {item.title: item for item in audit_system()}
        assert items["fhir-hl7"].status == "measured"

    def test_audit_ai_engines_present(self):
        items = {item.title: item for item in audit_system()}
        assert items["ai-engines"].status == "measured"


class TestModel:
    def test_build_model_discovers_contexts(self, tmp_path):
        (tmp_path / "backend" / "app" / "services").mkdir(parents=True)
        (tmp_path / "backend" / "app" / "services" / "patient_service.py").write_text(
            "x", encoding="utf-8"
        )
        (tmp_path / "backend" / "app" / "models").mkdir(parents=True)
        (tmp_path / "backend" / "app" / "models" / "patient.py").write_text(
            "class Patient(Base):\n    pass\n", encoding="utf-8"
        )
        (tmp_path / "backend" / "app" / "routes").mkdir(parents=True)
        (tmp_path / "backend" / "app" / "routes" / "patient.py").write_text(
            "x", encoding="utf-8"
        )
        contexts = build_model(tmp_path)
        assert any(c.name == "patient" for c in contexts)
        patient = next(c for c in contexts if c.name == "patient")
        assert patient.trust_boundary == "authenticated"
        assert "Patient" in patient.entities

    def test_build_model_contexts_have_subdomains(self, tmp_path):
        (tmp_path / "backend" / "app" / "services").mkdir(parents=True)
        (tmp_path / "backend" / "app" / "services" / "lab_service.py").write_text(
            "x", encoding="utf-8"
        )
        contexts = build_model(tmp_path)
        lab = next(c for c in contexts if c.name == "lab")
        assert "core" in lab.subdomains
        assert lab.trust_boundary == "internal"

    def test_empty_repo_yields_no_contexts(self, tmp_path):
        contexts = build_model(tmp_path)
        assert contexts == []

    def test_trust_boundaries_are_valid(self, tmp_path):
        (tmp_path / "backend" / "app" / "services").mkdir(parents=True)
        for seed in BOUNDED_CONTEXT_SEEDS:
            (tmp_path / "backend" / "app" / "services" / f"{seed}_service.py").write_text(
                "x", encoding="utf-8"
            )
        contexts = build_model(tmp_path)
        assert contexts
        for context in contexts:
            assert context.trust_boundary in TRUST_BOUNDARIES

    def test_relationships_are_symmetric_deterministic(self, tmp_path):
        (tmp_path / "backend" / "app" / "services").mkdir(parents=True)
        for seed in BOUNDED_CONTEXT_SEEDS:
            (tmp_path / "backend" / "app" / "services" / f"{seed}_service.py").write_text(
                "x", encoding="utf-8"
            )
        first = build_relationships(tmp_path)
        second = build_relationships(tmp_path)
        assert [r.to_dict() for r in first] == [r.to_dict() for r in second]

    def test_relationships_empty_without_modules(self, tmp_path):
        assert build_relationships(tmp_path) == []

    def test_persist_model_writes_files(self, tmp_path):
        (tmp_path / "backend" / "app" / "services").mkdir(parents=True)
        (tmp_path / "backend" / "app" / "services" / "lab_service.py").write_text(
            "x", encoding="utf-8"
        )
        contexts_path, relationships_path = persist_model(tmp_path)
        assert contexts_path.exists()
        assert relationships_path.exists()
        import json

        data = json.loads(contexts_path.read_text(encoding="utf-8"))
        assert "contexts" in data
        assert data["contexts"][0]["name"] == "lab"

    def test_render_contains_flows(self):
        from scripts.architect.model import render_markdown

        text = render_markdown(build_model(), build_relationships())
        assert "Data Flow" in text
        assert "Trust Boundaries" in text

    def test_context_trust_maps_every_seed(self):
        for seed in BOUNDED_CONTEXT_SEEDS:
            assert seed in CONTEXT_TRUST
