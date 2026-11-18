"""Tests for the National Integration status-registry integrity validator.

These tests exercise the governance gate that keeps the machine-readable
registry honest. No test is skipped and no assertion is weakened.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.national_integration_verify import (
    CANONICAL_STATUS,
    EXPECTED_GOVERNANCE_IDS,
    EXPECTED_PROTECTED_PATHS,
    REPO_ROOT,
    REQUIRED_DOCS,
    file_md5,
    iter_statuses,
    load_registry,
    main,
    validate,
)

REAL_REGISTRY = (
    REPO_ROOT / "GOVERNANCE" / "NATIONAL_INTEGRATION" / "status_registry.json"
)


def _fixture_root(tmp_path: Path) -> tuple[dict, Path]:
    """Build a minimal but fully valid registry + repository root."""
    gi = tmp_path / "GOVERNANCE" / "NATIONAL_INTEGRATION"
    gi.mkdir(parents=True)
    for prefix in REQUIRED_DOCS:
        (gi / f"{prefix}_fixture.md").write_text("# fixture\n", encoding="utf-8")
    (gi / "survey.md").write_text("# survey\n", encoding="utf-8")

    protected = []
    for relpath in EXPECTED_PROTECTED_PATHS:
        target = tmp_path / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"protected evidence: {relpath}\n", encoding="utf-8")
        protected.append(
            {
                "path": relpath,
                "md5": hashlib.md5(target.read_bytes()).hexdigest(),
                "verdict": "HOLD" if "FINAL_DECISION" in relpath else "REJECT",
                "status": "INDEPENDENTLY VERIFIED",
            }
        )

    # Make the fixture a real git repo so HEAD checks are exercised.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-q",
            "-m",
            "fixture",
        ],
        cwd=tmp_path,
        check=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    registry = {
        "schema_version": "1.0",
        "status_vocabulary": list(CANONICAL_STATUS),
        "repositories": {
            "integration": {
                "path": str(tmp_path),
                "head": head,
            }
        },
        "protected_evidence": protected,
        "baseline": {"status": "TESTED"},
        "phases": {"A": {"status": "IMPLEMENTED"}},
        "workstreams": {
            "WS-01": {"status": "TESTED", "survey": "survey.md"},
            **{ws: {"status": "TESTED"} for ws in EXPECTED_WORKSTREAMS[1:]},
        },
        "governance_items": [
            {"id": gid, "status": "BLOCKED"} for gid in EXPECTED_GOVERNANCE_IDS
        ],
        "engineering_artifacts": [{"status": "TESTED"}],
        "production_ready_items": 0,
    }
    return registry, tmp_path


EXPECTED_WORKSTREAMS = tuple(f"WS-{n:02d}" for n in range(1, 8))


class TestRealRegistry:
    def test_registry_is_valid_json_with_expected_shape(self) -> None:
        registry = load_registry(REAL_REGISTRY)
        assert registry["schema_version"] == "1.0"
        assert registry["status_vocabulary"] == list(CANONICAL_STATUS)
        assert len(registry["workstreams"]) == 7
        assert len(registry["governance_items"]) >= 20

    def test_real_registry_validates_against_repository(self) -> None:
        registry = load_registry(REAL_REGISTRY)
        errors, _warnings = validate(registry, REPO_ROOT)
        assert errors == []

    def test_all_required_documents_exist(self) -> None:
        gi = REPO_ROOT / "GOVERNANCE" / "NATIONAL_INTEGRATION"
        for prefix in REQUIRED_DOCS:
            docs = list(gi.glob(f"{prefix}_*.md"))
            assert len(docs) == 1, f"expected exactly one {prefix}_* document"

    def test_registry_declares_seven_workstreams_and_zero_production_ready(self) -> None:
        registry = load_registry(REAL_REGISTRY)
        assert set(registry["workstreams"]) == set(EXPECTED_WORKSTREAMS)
        assert registry["production_ready_items"] == 0

    def test_cli_passes_on_real_registry(self) -> None:
        assert main(["--registry", str(REAL_REGISTRY), "--repo-root", str(REPO_ROOT)]) == 0

    def test_every_status_in_real_registry_is_canonical(self) -> None:
        registry = load_registry(REAL_REGISTRY)
        noncanonical = [
            (path, value)
            for path, value in iter_statuses(registry)
            if value not in CANONICAL_STATUS
        ]
        assert noncanonical == []


class TestValidatorNegativeCases:
    def test_valid_fixture_has_no_errors(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        errors, warnings = validate(registry, root)
        assert errors == []
        assert warnings == []

    def test_missing_required_document_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        (root / "GOVERNANCE" / "NATIONAL_INTEGRATION" / "00_fixture.md").unlink()
        errors, _ = validate(registry, root)
        assert any("00_*" in error for error in errors)

    def test_undeclared_status_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["phases"]["A"]["status"] = "MAGIC PASSED STATE"
        errors, _ = validate(registry, root)
        assert any("undeclared status" in error for error in errors)

    def test_changed_protected_md5_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        target = root / EXPECTED_PROTECTED_PATHS[0]
        target.write_text("tampered\n", encoding="utf-8")
        errors, _ = validate(registry, root)
        assert any("md5 changed" in error for error in errors)

    def test_missing_survey_file_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        (root / "GOVERNANCE" / "NATIONAL_INTEGRATION" / "survey.md").unlink()
        errors, _ = validate(registry, root)
        assert any("survey file missing" in error for error in errors)

    def test_production_ready_claim_is_rejected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["production_ready_items"] = 1
        errors, _ = validate(registry, root)
        assert any("production_ready_items" in error for error in errors)

    def test_malformed_head_is_rejected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["repositories"]["integration"]["head"] = "not-a-sha"
        errors, _ = validate(registry, root)
        assert any("malformed HEAD" in error for error in errors)

    def test_head_drift_is_only_a_warning(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["repositories"]["integration"]["head"] = "b" * 40
        errors, warnings = validate(registry, root)
        assert errors == []
        assert any("HEAD moved" in warning for warning in warnings)

    def test_missing_required_key_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        del registry["workstreams"]
        errors, _ = validate(registry, root)
        assert any("missing required key" in error for error in errors)

    def test_invalid_md5_format_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["protected_evidence"][0]["md5"] = "xyz"
        errors, _ = validate(registry, root)
        assert any("invalid md5" in error for error in errors)

    def test_file_md5_matches_hashlib(self, tmp_path: Path) -> None:
        target = tmp_path / "sample.bin"
        target.write_bytes(b"gula national integration\n")
        assert file_md5(target) == hashlib.md5(target.read_bytes()).hexdigest()

    def test_cli_returns_one_on_invalid_registry(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["production_ready_items"] = 99
        path = root / "bad_registry.json"
        path.write_text(json.dumps(registry), encoding="utf-8")
        assert main(["--registry", str(path), "--repo-root", str(root)]) == 1

    def test_cli_json_output_reports_fail(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        path = tmp_path / "missing.json"
        assert main(["--registry", str(path), "--json"]) == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["verdict"] == "FAIL"
        assert payload["errors"]

    def test_protected_evidence_bad_status_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["protected_evidence"][0]["status"] = "VERIFIED UNCHANGED"
        errors, _ = validate(registry, root)
        assert any("protected_evidence[0].status" in error for error in errors)

    def test_baseline_bad_status_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["baseline"]["status"] = "PASSED"
        errors, _ = validate(registry, root)
        assert any("baseline.status" in error for error in errors)

    def test_engineering_artifact_bad_status_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["engineering_artifacts"][0]["status"] = "DONE"
        errors, _ = validate(registry, root)
        assert any("engineering_artifacts[0].status" in error for error in errors)

    def test_registry_cannot_widen_its_own_vocabulary(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["status_vocabulary"] = ["IN PROGRESS"]

        def rewrite(node: Any) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "status":
                        node[key] = "IN PROGRESS"
                    rewrite(value)
            elif isinstance(node, list):
                for value in node:
                    rewrite(value)
        rewrite(registry)
        errors, _ = validate(registry, root)
        assert any("status_vocabulary" in error for error in errors)
        assert any("undeclared status 'IN PROGRESS'" in error for error in errors)

    def test_empty_protected_evidence_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["protected_evidence"] = []
        errors, _ = validate(registry, root)
        assert any("protected_evidence" in error for error in errors)

    def test_missing_protected_record_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["protected_evidence"] = registry["protected_evidence"][:2]
        errors, _ = validate(registry, root)
        assert any("missing required record" in error for error in errors)

    def test_empty_workstreams_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["workstreams"] = {}
        errors, _ = validate(registry, root)
        assert any("workstreams" in error for error in errors)

    def test_missing_workstream_id_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        del registry["workstreams"]["WS-07"]
        errors, _ = validate(registry, root)
        assert any("WS-07" in error for error in errors)

    def test_missing_governance_item_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["governance_items"] = [
            item for item in registry["governance_items"] if item["id"] != "HOLD"
        ]
        errors, _ = validate(registry, root)
        assert any("HOLD" in error for error in errors)

    def test_empty_governance_items_is_detected(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        registry["governance_items"] = []
        errors, _ = validate(registry, root)
        assert any("governance_items" in error for error in errors)


class TestRegistryImmutability:
    def test_validator_does_not_modify_registry(self) -> None:
        before = REAL_REGISTRY.read_bytes()
        load_registry(REAL_REGISTRY)
        validate(load_registry(REAL_REGISTRY), REPO_ROOT)
        assert REAL_REGISTRY.read_bytes() == before

    def test_deep_copy_negative_case_does_not_leak(self, tmp_path: Path) -> None:
        registry, root = _fixture_root(tmp_path)
        tampered = copy.deepcopy(registry)
        tampered["governance_items"][0]["status"] = "NOT IN VOCABULARY"
        assert validate(registry, root)[0] == []
        assert validate(tampered, root)[0] != []
