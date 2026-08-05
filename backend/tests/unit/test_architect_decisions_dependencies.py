"""Unit tests for GULA-ARCHITECT-001 — decisions (Phase 2) + dependencies (Phase 3)."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.architect.decisions import (
    STRATEGIC_DECISIONS,
    build_decisions,
    discover_adrs,
    persist_decisions,
    render_markdown,
)
from scripts.architect.dependencies import (
    DependencyEdge,
    _find_cycles,
    _find_skip_layer,
    _find_technology_lockin,
    build_edges,
    detect_dependencies,
    module_imports,
    persist_dependencies,
)


class TestDecisions:
    def test_build_decisions_returns_ten(self):
        decisions = build_decisions()
        assert len(decisions) == 10

    def test_decisions_carry_full_record(self):
        for decision in build_decisions():
            assert decision.alternatives
            assert decision.trade_offs
            assert decision.cost
            assert decision.rollback
            assert decision.review_status in {"reviewed", "pending-review"}
            assert decision.consequences

    def test_decisions_have_valid_status(self):
        for decision in build_decisions():
            assert decision.status in {"accepted", "proposed"}

    def test_accepted_decisions_reviewed(self):
        for decision in build_decisions():
            if decision.status == "accepted":
                assert decision.review_status == "reviewed"

    def test_persist_decisions_writes_file(self, tmp_path):
        path = persist_decisions(tmp_path)
        assert path.exists()
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data["decisions"]) == len(build_decisions(tmp_path))
        assert "adr_files" in data

    def test_render_has_registry_table(self):
        text = render_markdown(build_decisions(), len(discover_adrs()))
        assert "## Decision Records" in text
        assert "Rollback strategy" in text
        assert "accepted" in text

    def test_missing_adr_marks_proposed(self, tmp_path):
        decisions = build_decisions(tmp_path)
        for decision in decisions:
            assert decision.status == "proposed"

    def test_all_strategic_decisions_have_adr_ref(self):
        for record in STRATEGIC_DECISIONS:
            assert record["adr_ref"]


class TestDependencies:
    def test_module_imports_detects_app_packages(self, tmp_path):
        (tmp_path / "backend" / "app" / "routes").mkdir(parents=True)
        (tmp_path / "backend" / "app" / "routes" / "a.py").write_text(
            "from app.services.patient import x\n", encoding="utf-8"
        )
        imports = dict(module_imports(tmp_path))
        assert "backend/app/routes/a.py" in imports
        assert imports["backend/app/routes/a.py"] == ("services",)

    def test_module_imports_empty_root(self, tmp_path):
        assert module_imports(tmp_path) == ()

    def test_build_edges_produces_edges(self, tmp_path):
        (tmp_path / "backend" / "app" / "routes").mkdir(parents=True)
        (tmp_path / "backend" / "app" / "routes" / "a.py").write_text(
            "from app.services.patient import x\n", encoding="utf-8"
        )
        edges = build_edges(tmp_path)
        assert any(e.source == "routes" and e.target == "services" for e in edges)

    def test_cycle_detection_finds_two_node_cycle(self):
        graph = {"a": {"b"}, "b": {"a"}}
        cycles = _find_cycles(graph)
        assert len(cycles) == 1
        assert set(cycles[0]) == {"a", "b"}

    def test_cycle_detection_deduplicates_rotations(self):
        graph = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
        cycles = _find_cycles(graph)
        assert len(cycles) == 1
        assert set(cycles[0]) == {"a", "b", "c"}

    def test_cycle_detection_no_false_positive(self):
        graph = {"a": {"b"}, "b": {"c"}}
        assert _find_cycles(graph) == []

    def test_skip_layer_detection(self):
        edges = [
            DependencyEdge(source="routes", target="models", kind="calls"),
            DependencyEdge(source="routes", target="services", kind="calls"),
        ]
        findings = _find_skip_layer(edges)
        assert len(findings) == 1
        assert findings[0].kind == "skip-layer"
        assert findings[0].source == "routes"
        assert findings[0].target == "models"

    def test_technology_lockin_detects_vendor_sdk(self, tmp_path):
        (tmp_path / "backend").mkdir(parents=True)
        (tmp_path / "backend" / "requirements.txt").write_text(
            "boto3==1.0\nflask\n", encoding="utf-8"
        )
        findings = _find_technology_lockin(tmp_path)
        assert any(f.kind == "technology-lock-in" and f.target == "aws"
                   for f in findings)

    def test_technology_lockin_clean_repo(self, tmp_path):
        (tmp_path / "backend").mkdir(parents=True)
        (tmp_path / "backend" / "requirements.txt").write_text(
            "fastapi\npsycopg2\n", encoding="utf-8"
        )
        assert _find_technology_lockin(tmp_path) == []

    def test_detect_dependencies_real_repo_returns_list(self):
        findings = detect_dependencies()
        assert isinstance(findings, list)
        kinds = {f.kind for f in findings}
        assert kinds <= {"circular", "skip-layer", "cross-context",
                         "technology-lock-in"}

    def test_persist_dependencies_writes_file(self, tmp_path):
        (tmp_path / "backend" / "app" / "routes").mkdir(parents=True)
        (tmp_path / "backend" / "app" / "routes" / "a.py").write_text(
            "from app.models.claim import Claim\n", encoding="utf-8"
        )
        path = persist_dependencies(tmp_path)
        assert path.exists()
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        assert "edges" in data
        assert "findings" in data
