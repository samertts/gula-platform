"""Regression tests for the PROGRAM-STABLE-001 domain-isolation scanner.

Guards the two defects fixed in PROGRAM-STABLE-002:
1. Relative imports (`from ..hospital.models import ...`) were invisible to
   `_target_domain` because AST strips the leading dots — the nhdw→hospital
   edge went undetected.
2. The `lims` package was absent from DOMAINS (only `lab` was listed), so the
   entire laboratory domain was never scanned.
"""
from __future__ import annotations

import ast
import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "program_stable_001.py"

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def stable_module():
    spec = importlib.util.spec_from_file_location("program_stable_001", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # The script executes a main() guard only; loading it is side-effect safe
    # for the pure helpers we test.
    spec.loader.exec_module(module)
    return module


class TestTargetDomain:
    def test_absolute_app_import(self, stable_module):
        assert stable_module._target_domain("app.ehr.models", "app.nhdw.kpi", 0) == "ehr"

    def test_relative_import_resolves_to_domain(self, stable_module):
        # nhdw/kpi.py does `from ..hospital.models import Bed`; AST gives
        # module="hospital.models", level=2, pkg_path="app.nhdw.kpi".
        assert (
            stable_module._target_domain("hospital.models", "app.nhdw.kpi", 2)
            == "hospital"
        )

    def test_relative_import_with_module_attr(self, stable_module):
        assert (
            stable_module._target_domain("hospital.models.Bed", "app.nhdw.kpi", 2)
            == "hospital"
        )

    def test_intra_package_same_name_is_not_domain(self, stable_module):
        # care_continuum/models/__init__.py does `from .public_health import ...`
        # — this is care_continuum.models.public_health, NOT the public_health
        # domain. Resolves to the care_continuum domain itself (same as source,
        # hence not a violation).
        assert (
            stable_module._target_domain("public_health", "app.care_continuum.models", 1)
            == "care_continuum"
        )

    def test_sibling_intra_package_is_not_domain(self, stable_module):
        assert (
            stable_module._target_domain("care_journey", "app.care_continuum.models", 1)
            == "care_continuum"
        )

    def test_relative_level_beyond_package_depth(self, stable_module):
        assert stable_module._target_domain("x", "app.nhdw", 3) is None

    def test_lims_is_a_known_domain(self, stable_module):
        assert "lims" in stable_module.DOMAINS
        assert "lab" in stable_module.DOMAINS

    def test_absolute_national_data(self, stable_module):
        assert (
            stable_module._target_domain("app.national_data.models", "app.nhdw.kpi", 0)
            == "national_data"
        )


class TestAllowedCross:
    def test_ehr_consumer_contracts_allowed(self, stable_module):
        for src in ("citizen_platform", "nursing", "national_data"):
            assert stable_module._allowed_cross(src, "ehr", "app/x/y.py") is True

    def test_nhdw_hospital_read_contract_allowed(self, stable_module):
        assert stable_module._allowed_cross("nhdw", "hospital", "app/nhdw/kpi.py") is True

    def test_unapproved_cross_domain_blocked(self, stable_module):
        assert stable_module._allowed_cross("lims", "pharmacy", "app/lims/x.py") is False
        assert stable_module._allowed_cross("ehr", "hospital", "app/ehr/x.py") is False

    def test_tests_always_allowed(self, stable_module):
        assert stable_module._allowed_cross("lims", "pharmacy", "app/tests/x.py") is True


class TestScannerOnRealTree:
    """End-to-end: run the scanner over the real backend tree.

    Must find zero unauthorized cross-domain edges with the current
    approved-contract allowlist.
    """

    def test_no_unauthorized_cross_domain_edges(self, stable_module):
        backend = ROOT / "backend"
        violations: list[str] = []
        domains = set(stable_module.DOMAINS)
        for p in (backend / "app").rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            rel = p.relative_to(backend).as_posix()
            src_pkg = rel.split("/")[1] if "/" in rel else None
            if src_pkg not in domains:
                continue
            pkg_path = rel[:-3].replace("/", ".")
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for a in node.names:
                        mod = (
                            (node.module + "." + a.name)
                            if a.name != "*"
                            else node.module
                        )
                        tgt = stable_module._target_domain(
                            mod, pkg_path, node.level
                        )
                        if (
                            tgt
                            and tgt != src_pkg
                            and not stable_module._allowed_cross(src_pkg, tgt, rel)
                        ):
                            violations.append(f"{rel}: imports {mod}")
                elif isinstance(node, ast.Import):
                    for a in node.names:
                        tgt = stable_module._target_domain(a.name, pkg_path, 0)
                        if (
                            tgt
                            and tgt != src_pkg
                            and not stable_module._allowed_cross(src_pkg, tgt, rel)
                        ):
                            violations.append(f"{rel}: imports {a.name}")
        assert violations == [], "\n".join(violations)
