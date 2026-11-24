"""Phase F (F-072 / D-023) — certification engine, synthetic data only.

No DB, no network, no real patient data. Evaluators are replaced with tiny
deterministic fakes; everything runs under pytest's tmp_path.

SCOPE DISCLAIMER (F-072): this engine scores a source tree against 13 static
dimensions. It is NOT a production-readiness or clinical-safety authority, and
its output must never be used as release evidence. A high score is a
maintenance signal only. Human security review (D-020) and Clinical Safety
Owner sign-off (D-021) remain the binding gates.

Covers: path-traversal guard + F-079 idempotency regression, threshold mapping,
deterministic scoring, evidence/dimension validation, serialization, role of
failed evidence flags, and the scope disclaimer.

Evidence id: E-059 (see GOVERNANCE/GECS/EVIDENCE_REGISTRY.md).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.certification.dimensions import DimensionResult, Evidence, Remediation
from app.certification.engine import CertificationEngine
from app.certification.enums import CertificationDimension, CertificationLevel
from app.certification.report import CertificationReport


class _FakeEvaluator:
    """Deterministic evaluator returning a scripted DimensionResult."""

    calls: list[str] = []

    def __init__(self, project_root=None, result: DimensionResult | None = None):
        self.result = result if result is not None else DimensionResult(score=0.8, passed=True)
        self.project_root = project_root

    def evaluate(self, module_path=None):
        _FakeEvaluator.calls.append(str(module_path))
        return self.result


@pytest.fixture(autouse=True)
def _reset_calls():
    _FakeEvaluator.calls = []
    yield
    _FakeEvaluator.calls = []


@pytest.fixture
def engine(tmp_path: Path) -> CertificationEngine:
    return CertificationEngine(tmp_path)


# ---------------------------------------------------------------------------
# Path safety + F-079 route regression
# ---------------------------------------------------------------------------


class TestPathSafety:
    @pytest.mark.parametrize("bad", ["../outside", "a/../../etc", "..", "/abs/path"])
    def test_unsafe_paths_rejected(self, engine, bad):
        # Absolute paths outside the project root are rejected; relative
        # traversal and dot segments are rejected by the original guard.
        # ("./ok" is intentionally NOT here: Path normalizes it to ("ok",)
        # and it is a legitimate in-root path, so it must be accepted.)
        if bad.startswith("/"):
            with pytest.raises(ValueError):
                engine._safe_path(bad)
        else:
            with pytest.raises(ValueError, match="relative|unsafe segment"):
                engine._safe_path(bad)

    def test_no_module_path_returns_root(self, engine, tmp_path):
        assert engine._safe_path(None) == tmp_path.resolve()

    def test_valid_relative_path(self, engine, tmp_path):
        assert engine._safe_path("app/module") == tmp_path.resolve() / "app" / "module"

    def test_f079_route_double_resolution_no_longer_500(self, engine):
        # F-079 regression: routes._safe_target returns an absolute in-root
        # path, then passes it back to evaluate_module. _safe_path must be
        # idempotent for such paths (outside-root absolute still rejected).
        target = engine._safe_path("app/module")
        assert target.is_absolute()
        assert engine._safe_path(str(target)) == target
        with pytest.raises(ValueError):
            engine._safe_path("/etc/passwd")


# ---------------------------------------------------------------------------
# Threshold mapping (deterministic)
# ---------------------------------------------------------------------------


class TestLevelThresholds:
    @pytest.mark.parametrize("score, level", [
        (0.95, CertificationLevel.DIAMOND),
        (0.94, CertificationLevel.PLATINUM),
        (0.85, CertificationLevel.PLATINUM),
        (0.84, CertificationLevel.GOLD),
        (0.75, CertificationLevel.GOLD),
        (0.74, CertificationLevel.SILVER),
        (0.60, CertificationLevel.SILVER),
        (0.59, CertificationLevel.BRONZE),
        (0.40, CertificationLevel.BRONZE),
        (0.0, CertificationLevel.BRONZE),
        (1.0, CertificationLevel.DIAMOND),
    ])
    def test_determine_level(self, engine, score, level):
        assert engine._determine_level(score) == level


# ---------------------------------------------------------------------------
# Report scoring / evidence / serialization
# ---------------------------------------------------------------------------


class TestCertificationReport:
    def test_calculate_overall_is_plain_mean(self):
        report = CertificationReport()
        report.add_dimension(CertificationDimension.SECURITY, DimensionResult(score=1.0))
        report.add_dimension(CertificationDimension.OFFLINE, DimensionResult(score=0.5))
        assert report.calculate_overall() == 0.75

    def test_empty_report_scores_zero(self):
        assert CertificationReport().calculate_overall() == 0.0

    def test_dimension_result_clamps_and_threshold(self):
        from app.certification.dimensions import DimensionEvaluator

        class _E(DimensionEvaluator):
            def __init__(self, score):
                super().__init__()
                self.score = score

            def evaluate(self, module_path=None):
                return self._result(self.score)

        assert _E(0.7).evaluate().passed is True  # >= 0.7 threshold
        assert _E(0.69).evaluate().passed is False
        assert _E(1.5).evaluate().score == 1.0   # clamped upper
        assert _E(-1).evaluate().score == 0.0    # clamped lower

    def test_failed_evidence_is_serialized_not_silently_dropped(self):
        report = CertificationReport()
        report.add_dimension(CertificationDimension.TEST_COVERAGE, DimensionResult(
            score=0.8,
            passed=True,
            evidence=[Evidence(name="coverage", value=0.2, source="synthetic", passed=False)],
            remediations=[Remediation(severity="high", message="synthetic", effort="low")],
        ))
        data = report.to_dict()
        ev = data["dimensions"]["test_coverage"]["evidence"][0]
        assert ev["passed"] is False
        assert data["dimensions"]["test_coverage"]["remediations"][0]["severity"] == "high"
        # NOTE (residual F-080): `DimensionResult.passed` is derived from the
        # score alone (>=0.7), so a dimension can be marked passed even with a
        # failed evidence item. Serialization keeps the truth; consumers must
        # inspect evidence, not rely on the single `passed` flag.

    def test_serializers_are_deterministic_and_utf8_safe(self):
        report = CertificationReport(module_path="synthetic/module", overall_score=0.9)
        report.summary = "تقرير اصطناعي — synthetic"
        data = report.to_dict()
        assert data["module_path"] == "synthetic/module"
        assert data["overall_score"] == 0.9
        assert "تقرير اصطناعي" in report.to_json()
        assert "synthetic/module" in report.to_markdown()
        assert "synthetic/module" in report.to_html()
        assert report.to_json() == report.to_json()  # stable

    def test_generate_summary_mentions_weak_dimensions(self):
        engine = CertificationEngine("/tmp")
        report = CertificationReport()
        report.add_dimension(CertificationDimension.SECURITY, DimensionResult(score=0.95, passed=True))
        report.add_dimension(CertificationDimension.OFFLINE, DimensionResult(score=0.4, passed=False))
        report.overall_score = 0.675
        report.certification_level = CertificationLevel.SILVER
        summary = engine._generate_summary(report)
        assert "1/2 dimensions passed" in summary
        assert "offline" in summary
        assert "SILVER" in summary


# ---------------------------------------------------------------------------
# Engine evaluation with deterministic fake evaluators
# ---------------------------------------------------------------------------


class TestEngineEvaluation:
    def test_evaluate_dimension_isolated(self, engine, monkeypatch):
        monkeypatch.setattr(engine, "_evaluators", {CertificationDimension.OFFLINE: _FakeEvaluator})
        report = engine.evaluate_dimension(CertificationDimension.OFFLINE, "app/module")
        assert CertificationDimension.OFFLINE in report.dimensions
        assert report.overall_score == 0.8
        # 0.8 sits in the GOLD band (0.75–0.85); PLATINUM requires >= 0.85.
        assert report.certification_level == CertificationLevel.GOLD
        assert len(_FakeEvaluator.calls) == 1

    def test_evaluate_unknown_dimension_raises(self, engine, monkeypatch):
        monkeypatch.setattr(engine, "_evaluators", {})
        with pytest.raises(ValueError, match="Unknown dimension"):
            engine.evaluate_dimension("not_a_dimension", "app")

    def test_evaluate_module_runs_all_registered_evaluators(self, engine, monkeypatch):
        monkeypatch.setattr(engine, "_evaluators", {
            CertificationDimension.SECURITY: _FakeEvaluator,
            CertificationDimension.OFFLINE: _FakeEvaluator,
        })
        report = engine.evaluate_module("app/module")
        assert set(report.dimensions) == {
            CertificationDimension.SECURITY, CertificationDimension.OFFLINE,
        }
        assert report.overall_score == 0.8
        assert report.summary
        assert len(_FakeEvaluator.calls) == 2

    def test_get_certification_level_reuses_report(self, engine, monkeypatch):
        monkeypatch.setattr(engine, "_evaluators", {CertificationDimension.SECURITY: _FakeEvaluator})
        # score 0.8 → GOLD (0.75–0.85)
        assert engine.get_certification_level("app") == CertificationLevel.GOLD


# ---------------------------------------------------------------------------
# Scope disclaimer — F-072 acceptance
# ---------------------------------------------------------------------------


class TestScopeDisclaimer:
    def test_engine_output_carries_no_production_ready_or_clinical_certified_claim(self, engine, monkeypatch):
        # A perfect static score must not be presented as a release decision.
        monkeypatch.setattr(engine, "_evaluators", {CertificationDimension.SECURITY: _FakeEvaluator})
        high = DimensionResult(score=1.0, passed=True, evidence=[
            Evidence(name="synthetic", value=True, source="synthetic", passed=True)
        ])
        report = CertificationReport(module_path="synthetic", overall_score=1.0)
        report.add_dimension(CertificationDimension.SECURITY, high)
        report.certification_level = CertificationLevel.DIAMOND
        report.summary = engine._generate_summary(report)
        blob = (report.summary + report.to_markdown()).lower()
        assert "production ready" not in blob
        assert "production-ready" not in blob
        assert "clinical safety certified" not in blob
        # The report describes dimension scores only — no approval semantics.
        assert "dimensions passed" in report.summary

    def test_engine_has_no_certificate_lifecycle_api(self, engine):
        # F-072 scope note: expiry/renewal/revocation/role-separation and
        # duplicate-certificate concepts do not exist in this engine; those
        # belong to other modules. Do not imply they are verified here.
        for name in ("revoke", "renew", "expire", "issue_certificate"):
            assert not hasattr(engine, name)
