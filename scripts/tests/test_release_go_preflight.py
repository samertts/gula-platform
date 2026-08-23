from __future__ import annotations

import json
from pathlib import Path

from scripts.release_go_preflight import (
    REQUIRED_GATES,
    REQUIRED_SIGNATURES,
    evaluate_manifest,
    migration_heads,
)


def _complete_manifest(head: str) -> dict[str, object]:
    gates = {
        gate: {
            "status": "PASS",
            "owner": "test-owner",
            "recorded_at": "2026-08-23T00:00:00+00:00",
            "evidence": "https://example.invalid/evidence",
        }
        for gate in REQUIRED_GATES
    }
    gates["migration"].update(
        {
            "expected_head": head,
            "observed_heads": [head],
        },
    )
    signatures = {
        role: {
            "name": "Authorized Test Role",
            "signed_at": "2026-08-23T00:00:00+00:00",
            "decision": "APPROVED",
            "evidence": "https://example.invalid/signature",
        }
        for role in REQUIRED_SIGNATURES
    }
    return {
        "release": {
            "candidate_sha": "a" * 40,
            "target_branch": "release/test",
            "recorded_at": "2026-08-23T00:00:00+00:00",
        },
        "gates": gates,
        "signatures": signatures,
    }


def test_migration_heads_finds_the_single_child_head(tmp_path: Path) -> None:
    (tmp_path / "a_base.py").write_text(
        'revision = "base"\ndown_revision = None\n',
        encoding="utf-8",
    )
    (tmp_path / "b_head.py").write_text(
        'revision: str = "head"\ndown_revision: str | None = "base"\n',
        encoding="utf-8",
    )

    assert migration_heads(tmp_path) == ("head",)


def test_manifest_is_no_go_when_a_required_gate_is_pending() -> None:
    manifest = _complete_manifest("head")
    manifest["gates"]["ci"]["status"] = "PENDING"

    report = evaluate_manifest(manifest, ("head",))

    assert report.status == "NO_GO"
    assert "gates.ci.status must be PASS" in report.failures


def test_complete_evidence_requires_a_human_go_decision() -> None:
    report = evaluate_manifest(_complete_manifest("head"), ("head",))

    assert report.status == "HUMAN_GO_DECISION_REQUIRED"
    assert report.failures == ()
    assert report.warnings


def test_repository_template_is_default_deny() -> None:
    manifest_path = Path("docs/GO_LAUNCH_EVIDENCE_MANIFEST.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    report = evaluate_manifest(manifest, ("20260820_0005",))

    assert report.status == "NO_GO"
    assert report.failures
