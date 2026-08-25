from __future__ import annotations

import unittest
from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"


class CiSbomWorkflowTests(unittest.TestCase):
    def test_sbom_job_is_pinned_and_artifact_only(self) -> None:
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        job = workflow["jobs"]["sbom"]
        steps = job["steps"]
        generation_step = next(step for step in steps if step.get("name") == "Generate CycloneDX SBOM")
        upload_step = next(step for step in steps if step.get("name") == "Upload SBOM artifact")

        self.assertEqual(job["needs"], ["syntax-gate"])
        self.assertEqual(job["permissions"], {"contents": "read"})
        self.assertEqual(generation_step["uses"], "anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610")
        self.assertEqual(generation_step["with"]["format"], "cyclonedx-json")
        self.assertFalse(generation_step["with"]["upload-artifact"])
        self.assertFalse(generation_step["with"]["upload-release-assets"])
        self.assertEqual(upload_step["uses"], "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02")
        self.assertEqual(upload_step["with"]["if-no-files-found"], "error")


if __name__ == "__main__":
    unittest.main()
