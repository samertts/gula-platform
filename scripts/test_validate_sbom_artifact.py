from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validate_sbom_artifact import main


class ValidateSbomArtifactTests(unittest.TestCase):
    def write_payload(self, payload: object) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "sbom.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_accepts_non_empty_cyclonedx_components(self) -> None:
        path = self.write_payload(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "components": [{"name": "example-package", "version": "1.0.0"}],
            }
        )

        self.assertEqual(main(["validator", str(path)]), 0)

    def test_rejects_non_cyclonedx_payload(self) -> None:
        path = self.write_payload(
            {"bomFormat": "SPDX", "specVersion": "1.6", "components": [{"name": "x"}]}
        )

        self.assertEqual(main(["validator", str(path)]), 1)

    def test_rejects_empty_components(self) -> None:
        path = self.write_payload(
            {"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []}
        )

        self.assertEqual(main(["validator", str(path)]), 1)

    def test_rejects_invalid_json(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "sbom.json"
        path.write_text("not-json", encoding="utf-8")

        self.assertEqual(main(["validator", str(path)]), 1)


if __name__ == "__main__":
    unittest.main()
