from __future__ import annotations

from pathlib import Path

from scripts.security_scan_config import scan


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_scanner_detects_high_risk_configuration(tmp_path):
    path = tmp_path / "docker-compose.yml"
    _write(
        path,
        """services:\n  app:\n    image: example/app:latest\n    privileged: true\n    environment:\n      API_KEY: real-secret-value\n      URL: http://remote.invalid\n""",
    )
    findings = scan(tmp_path, set())
    rules = {finding.rule for finding in findings}
    assert {"UNPINNED_IMAGE", "PRIVILEGED_CONTAINER", "SECRET_EXPOSED", "PLAINTEXT_ENDPOINT"} <= rules


def test_scanner_allows_placeholders_and_local_http(tmp_path):
    path = tmp_path / "config.yaml"
    _write(path, "secret: ${SECRET}\nurl: http://localhost:8000\n")
    assert scan(tmp_path, set()) == []


def test_scanner_parses_json_and_reports_invalid_config(tmp_path):
    path = tmp_path / "settings.json"
    _write(path, '{"enabled": true,')
    findings = scan(tmp_path, set())
    assert any(finding.rule == "PARSE_ERROR" for finding in findings)


def test_scanner_excludes_node_modules(tmp_path):
    path = tmp_path / "node_modules" / "third-party.json"
    path.parent.mkdir()
    _write(path, '{"secret": "real-secret"}')
    assert scan(tmp_path, {"node_modules"}) == []
