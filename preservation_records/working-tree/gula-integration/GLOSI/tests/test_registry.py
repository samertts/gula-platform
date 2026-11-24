#!/usr/bin/env python3
"""Quality-gate tests for the GLOSI registry (stdlib unittest, no network)."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

GLOSI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GLOSI_ROOT / "tools"))

import build_initial_registry  # noqa: E402
import glosi_registry  # noqa: E402

REGISTRY_PATH = GLOSI_ROOT / "REGISTRY" / "registry.json"


def load() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def errors_for(data: dict) -> list[str]:
    return glosi_registry.validate_registry(data)


class RegistryStructureTests(unittest.TestCase):
    def test_initial_registry_is_valid(self) -> None:
        self.assertEqual(errors_for(load()), [])

    def test_builder_is_deterministic_and_matches_registry(self) -> None:
        self.assertEqual(build_initial_registry.build(), load())

    def test_decision_record_exists_for_every_record(self) -> None:
        data = load()
        for record in data["records"]:
            matches = list((GLOSI_ROOT / "DECISION_RECORDS").glob(f"{record['decision']['decision_id']}-*.md"))
            self.assertEqual(len(matches), 1)
            path = matches[0]
            text = path.read_text(encoding="utf-8")
            self.assertIn("**Status:** PROPOSED", text)
            self.assertNotIn("**Status:** APPROVED", text)

    def test_duplicate_registry_id_rejected(self) -> None:
        data = load()
        data["records"][1]["identity"]["registry_id"] = data["records"][0]["identity"]["registry_id"]
        self.assertTrue(any("duplicate registry_id" in e for e in errors_for(data)))

    def test_duplicate_decision_id_rejected(self) -> None:
        data = load()
        data["records"][1]["decision"]["decision_id"] = data["records"][0]["decision"]["decision_id"]
        self.assertTrue(any("duplicate decision_id" in e for e in errors_for(data)))

    def test_missing_required_identity_field_rejected(self) -> None:
        data = load()
        del data["records"][0]["identity"]["name"]
        self.assertTrue(any("identity.name" in e for e in errors_for(data)))

    def test_non_https_official_url_rejected(self) -> None:
        data = load()
        data["records"][0]["identity"]["official_url"] = "http://example.org"
        self.assertTrue(any("official_url must be https" in e for e in errors_for(data)))

    def test_weight_model_must_match_framework(self) -> None:
        data = load()
        data["scoring_model"]["weights"]["functionality_fit"] = 20
        self.assertTrue(any("weights differ" in e for e in errors_for(data)))

    def test_partial_evaluation_must_not_have_weighted_total(self) -> None:
        data = load()
        data["records"][0]["evaluation"]["weighted_total"] = 82.0
        self.assertTrue(any("must not have weighted_total" in e for e in errors_for(data)))

    def test_complete_evaluation_requires_every_dimension(self) -> None:
        data = load()
        data["records"][0]["evaluation"]["status"] = "COMPLETE"
        data["records"][0]["evaluation"]["dimensions"]["functionality_fit"]["score"] = None
        self.assertTrue(any("COMPLETE evaluation requires" in e for e in errors_for(data)))

    def test_weighted_total_is_recomputed(self) -> None:
        data = load()
        evaluation = data["records"][0]["evaluation"]
        evaluation["status"] = "COMPLETE"
        for dimension in evaluation["dimensions"].values():
            dimension["score"] = 90
        evaluation["weighted_total"] = 99
        evaluation["band"] = "excellent"
        self.assertTrue(any("weighted_total does not match" in e for e in errors_for(data)))


class DecisionGateTests(unittest.TestCase):
    def test_approved_requires_complete_evaluation_and_adr(self) -> None:
        data = load()
        data["records"][0]["decision"]["status"] = "APPROVED"
        errors = errors_for(data)
        self.assertTrue(any("APPROVED requires a COMPLETE evaluation" in e for e in errors))
        self.assertTrue(any("APPROVED requires an ADR reference" in e for e in errors))

    def test_unknown_license_cannot_be_adopted(self) -> None:
        data = load()
        record = data["records"][0]
        record["decision"]["decision"] = "ADOPT"
        record["legal"]["license"] = "UNKNOWN"
        self.assertTrue(any("adoption requires a known license" in e for e in errors_for(data)))

    def test_incompatible_license_cannot_be_adopted(self) -> None:
        data = load()
        record = data["records"][0]
        record["decision"]["decision"] = "INTEGRATE"
        record["legal"]["license_compatibility"] = "INCOMPATIBLE"
        self.assertTrue(any("incompatible license" in e for e in errors_for(data)))

    def test_critical_security_blocks_adoption(self) -> None:
        data = load()
        record = data["records"][0]
        record["decision"]["decision"] = "ADAPT"
        record["security"]["security_review_status"] = "BLOCKED"
        self.assertTrue(any("critical security finding" in e for e in errors_for(data)))

    def test_no_record_is_approved(self) -> None:
        data = load()
        self.assertTrue(all(record["decision"]["status"] != "APPROVED" for record in data["records"]))


class ExportAndHistoryTests(unittest.TestCase):
    def test_export_roundtrip_is_stable(self) -> None:
        data = load()
        payload = glosi_registry.canonical_json(data)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "registry.json"
            out.write_text(payload, encoding="utf-8")
            self.assertEqual(out.read_text(encoding="utf-8"), payload)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), data)

    def test_export_validates_before_writing(self) -> None:
        data = load()
        data["records"][0]["identity"]["official_url"] = "not-a-url"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "bad.json"
            target = Path(tmp) / "out.json"
            source.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(glosi_registry.RegistryError):
                glosi_registry.export_registry(source, target)
            self.assertFalse(target.exists())

    def test_update_appends_history_without_losing_prior_entries(self) -> None:
        data = load()
        record = data["records"][0]
        before = copy.deepcopy(record["evaluation_history"])
        glosi_registry.update_record(
            data,
            record["identity"]["registry_id"],
            {"evaluation": {"notes": "evidence update"}},
            update_date="2026-11-15",
            summary="Added source verification note",
            evidence_refs=["/tmp/opencode/glosi/evidence/repo_automerge.json"],
        )
        self.assertEqual(record["evaluation_history"][:-1], before)
        self.assertEqual(record["evaluation_history"][-1]["summary"], "Added source verification note")
        self.assertEqual(data["updated"], "2026-11-15")
        self.assertEqual(errors_for(data), [])

    def test_update_rejects_unknown_record(self) -> None:
        with self.assertRaises(glosi_registry.RegistryError):
            glosi_registry.update_record(
                load(),
                "GLOSI-9999",
                {"evaluation": {"notes": "x"}},
                update_date="2026-11-15",
                summary="x",
                evidence_refs=["https://example.org"],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
