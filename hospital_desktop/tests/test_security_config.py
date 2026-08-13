from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import DEFAULT_API_BASE_URL, AppConfig, validate_api_base_url  # noqa: E402


class ApiUrlValidationTests(unittest.TestCase):
    def test_default_is_production_https(self):
        self.assertEqual(AppConfig().api_base_url, DEFAULT_API_BASE_URL)

    def test_production_and_local_development_endpoints_are_allowed(self):
        self.assertEqual(
            validate_api_base_url("https://api.gula-platform.org/api/v1/"),
            DEFAULT_API_BASE_URL,
        )
        self.assertEqual(validate_api_base_url("http://localhost:8000"), "http://localhost:8000")

    def test_external_plaintext_and_unapproved_hosts_are_rejected(self):
        invalid_urls = (
            "http://api.gula-platform.org/api/v1",
            "https://evil.example/api/v1",
            "https://user:pass@api.gula-platform.org/api/v1",
            "https://api.gula-platform.org/other",
        )
        for value in invalid_urls:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_api_base_url(value)


if __name__ == "__main__":
    unittest.main()
