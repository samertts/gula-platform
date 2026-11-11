from pathlib import Path

from importlib.util import module_from_spec, spec_from_file_location


_spec = spec_from_file_location(
    "gula_secret_scanner",
    Path(__file__).parents[1] / ".audit" / "scan_secrets_safe.py",
)
assert _spec and _spec.loader
scanner = module_from_spec(_spec)
_spec.loader.exec_module(scanner)


def _scan(tmp_path: Path, content: str):
    path = tmp_path / "fixture.conf"
    path.write_text(content, encoding="utf-8")
    return scanner.scan_file(path)


def test_scanner_ignores_environment_references_and_documentation_headers(tmp_path):
    findings = _scan(
        tmp_path,
        """
password: \"{{ POSTGRES_PASSWORD }}\"
token=\"$VERCEL_TOKEN\"
SERVER_SSH_KEY starts with -----BEGIN OPENSSH PRIVATE KEY-----
""",
    )
    assert findings == []


def test_scanner_reports_literal_secret_assignments(tmp_path):
    findings = _scan(tmp_path, 'api_key = "literal-secret-value-123"\n')
    assert len(findings) == 1
    assert findings[0]["type"] == "generic_secret_assignment"
    assert findings[0]["placeholder_like"] is False


def test_scanner_reports_complete_private_key_block(tmp_path):
    body = "A" * 64
    findings = _scan(
        tmp_path,
        "-----BEGIN RSA PRIVATE KEY-----\n"
        f"{body}\n"
        "-----END RSA PRIVATE KEY-----\n",
    )
    assert len(findings) == 1
    assert findings[0]["type"] == "private_key"
