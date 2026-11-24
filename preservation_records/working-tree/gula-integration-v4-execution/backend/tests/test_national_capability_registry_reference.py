"""Synthetic verification of the National Capability Registry static index (W-079 / CC-010).

Engineering scope only. This suite proves the capability index is a *reference-only,
non-executing* artifact that stays consistent with the canonical engine inventory and
never becomes a routing authority or single point of failure. It does **not** verify any
engine at runtime, activate any dormant service, mount the national CDS route, or produce
a production-readiness / clinical-safety claim. No app behavior is changed by this file.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_national_capability_registry import (
    EXPECTED_COUNTS,
    _find_app_imports,
    verify,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX = REPO_ROOT / "GOVERNANCE" / "national_capability_index.json"
INVENTORY = REPO_ROOT / "GOVERNANCE" / "AUTONOMOUS_ENGINES_INVENTORY.md"

CANONICAL = {
    "INTEGRATION_VERIFIED": 9,
    "UNIT_VERIFIED": 15,
    "PARTIAL_VERIFIED": 2,
    "SOURCE_PRESENT": 11,
    "DORMANT": 1,
    "UNVERIFIABLE": 1,
    "RUNTIME_VERIFIED": 0,
    "PRODUCTION_VERIFIED": 0,
}


def _load():
    return json.loads(INDEX.read_text(encoding="utf-8"))


def test_index_is_a_reference_only_non_executing_artifact():
    doc = _load()
    assert doc["kind"] == "reference_only_static_index"
    assert doc["executing"] is False
    assert doc["authority"].lower().startswith("none")
    assert "advisory" in doc["authority"].lower()
    # No routing/dispatch keys that would turn the index into an executing component.
    assert not ({"routes", "handlers", "workers", "dispatch"} & set(doc))


def test_verifier_passes_all_checks():
    result = verify(REPO_ROOT)
    assert result["verdict"] == "PASS", result
    assert result["failed_checks"] == []
    assert result["checks_total"] == 20
    assert result["checks_passed"] == 20


def test_verifier_is_deterministic_and_idempotent():
    a = verify(REPO_ROOT)
    b = verify(REPO_ROOT)
    assert a == b  # no mutation, no cache, no side effect


def test_all_39_engines_present_and_unique():
    doc = _load()
    ids = [e["id"] for e in doc["engines"]]
    assert len(ids) == 39
    assert len(set(ids)) == 39
    assert set(ids) == {
        *(f"ENG-A{i:02d}" for i in range(1, 13)),
        *(f"ENG-B{i:02d}" for i in range(1, 13)),
        *(f"ENG-C{i:02d}" for i in range(1, 10)),
        *(f"ENG-D{i:02d}" for i in range(1, 7)),
    }


def test_status_distribution_matches_frozen_baseline():
    doc = _load()
    recomputed = {s: 0 for s in CANONICAL}
    for engine in doc["engines"]:
        recomputed[engine["status"]] += 1
    assert recomputed == CANONICAL
    assert doc["status_counts"] == recomputed
    assert recomputed == EXPECTED_COUNTS
    # Explicitly no runtime/production verification was invented.
    assert recomputed["RUNTIME_VERIFIED"] == 0
    assert recomputed["PRODUCTION_VERIFIED"] == 0


def test_dormant_and_unmounted_engines_stay_so():
    doc = _load()
    by_id = {e["id"]: e for e in doc["engines"]}
    assert by_id["ENG-A12"]["status"] == "DORMANT"
    assert by_id["ENG-B09"]["status"] == "UNVERIFIABLE"
    assert "never activate" in doc["special_states"]["ENG-A12"].lower()
    assert "unmounted" in doc["special_states"]["ENG-B09"].lower()
    assert "do not enable" in doc["special_states"]["ENG-B09"].lower()


def test_every_indexed_source_path_exists():
    doc = _load()
    missing = [e["id"] for e in doc["engines"]
               if not (REPO_ROOT / "backend" / e["source"]).exists()]
    assert missing == [], f"index points to nonexistent source: {missing}"


def test_application_never_imports_the_index():
    # The index is advisory: the app must work when it is absent, so no app module may import it.
    assert _find_app_imports(REPO_ROOT) == []


def test_negative_control_executing_flag_is_detected(tmp_path):
    doc = _load()
    doc["executing"] = True  # tamper: turn the reference index into a claimed executing component
    tampered = tmp_path / "tampered_executing.json"
    tampered.write_text(json.dumps(doc), encoding="utf-8")
    result = verify(REPO_ROOT, tampered)
    assert result["verdict"] == "FAIL"
    names = [c["name"] for c in result["failed_checks"]]
    assert "executing_false" in names


def test_negative_control_status_inflation_is_detected(tmp_path):
    doc = _load()
    # Tamper: invent a runtime-verified engine (a forbidden readiness claim).
    doc["engines"][0]["status"] = "RUNTIME_VERIFIED"
    tampered = tmp_path / "tampered_status.json"
    tampered.write_text(json.dumps(doc), encoding="utf-8")
    result = verify(REPO_ROOT, tampered)
    assert result["verdict"] == "FAIL"
    names = [c["name"] for c in result["failed_checks"]]
    assert "status_counts_canonical" in names


def test_negative_control_dormant_activation_is_detected(tmp_path):
    doc = _load()
    for engine in doc["engines"]:
        if engine["id"] == "ENG-A12":
            engine["status"] = "UNIT_VERIFIED"  # tamper: activate the dormant scaffold
    tampered = tmp_path / "tampered_dormant.json"
    tampered.write_text(json.dumps(doc), encoding="utf-8")
    result = verify(REPO_ROOT, tampered)
    assert result["verdict"] == "FAIL"
    names = [c["name"] for c in result["failed_checks"]]
    assert "eng_a12_dormant" in names


def test_canonical_inventory_still_carries_39_rows():
    text = INVENTORY.read_text(encoding="utf-8")
    import re
    assert len(re.findall(r"^\|\s*ENG-[A-D]\d{2}\b", text, re.M)) == 39
