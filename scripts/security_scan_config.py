#!/usr/bin/env python3
"""Fail-closed security lint for configuration and infrastructure files.

The scanner is intentionally local-only and deterministic. It does not execute
configuration, contact external services, or print secret values.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

MAX_FILE_BYTES = 2 * 1024 * 1024
DEFAULT_EXCLUDES = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    "readiness-evidence",
    "security-audit",
}
CONFIG_SUFFIXES = {".yml", ".yaml", ".json", ".toml", ".tf", ".tfvars"}
CONFIG_NAMES = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}
PLACEHOLDER_RE = re.compile(r"^(?:$|changeme|change-me|example|placeholder|dummy|test|<[^>]+>|\$\{[^}]+\})$", re.I)

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("jwt-like-token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("generic-secret-assignment", re.compile(r"(?i)\b(?:password|passwd|secret|token|api[_-]?key|private[_-]?key)\b\s*[:=]\s*[\"']?([^\"'\s,}]+)")),
)

@dataclass(frozen=True)
class Finding:
    severity: str
    rule: str
    path: str
    line: int
    message: str

    def render(self) -> str:
        return f"{self.severity:<8} {self.rule:<28} {self.path}:{self.line} {self.message}"


def _is_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_RE.fullmatch(value.strip())) or value.strip().lower() in {"false", "null", "none"}


def _iter_files(root: Path, excludes: set[str]) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in excludes for part in path.parts):
            continue
        if path.name in CONFIG_NAMES or path.suffix.lower() in CONFIG_SUFFIXES:
            yield path


def _safe_line(path: Path, line: int) -> str:
    try:
        value = path.read_text(encoding="utf-8", errors="replace").splitlines()[line - 1].strip()
    except (OSError, IndexError):
        return "configuration line"
    return re.sub(r"(?i)(password|passwd|secret|token|api[_-]?key|private[_-]?key)(\s*[:=]\s*)[^\s,}]+", r"\1\2[REDACTED]", value)


def _add(findings: list[Finding], severity: str, rule: str, path: Path, line: int, message: str) -> None:
    findings.append(Finding(severity, rule, str(path), line, message))


def _scan_secret_patterns(path: Path, lines: list[str], findings: list[Finding]) -> None:
    for number, text in enumerate(lines, start=1):
        for rule, pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            if rule == "generic-secret-assignment":
                value = match.group(1).strip().strip("\"'")
                if _is_placeholder(value) or value.startswith(("${", "os.environ", "env(", "var.")):
                    continue
            _add(findings, "CRITICAL", "SECRET_EXPOSED", path, number, f"possible {rule}; value redacted")
            break


def _scan_common_rules(path: Path, lines: list[str], findings: list[Finding]) -> None:
    path_text = str(path).replace("\\\\", "/")
    infra_file = path.suffix.lower() in {".yml", ".yaml", ".tf", ".tfvars"} or path.name.startswith("Dockerfile")
    workflow_file = ".github/workflows/" in path_text
    for number, text in enumerate(lines, start=1):
        lower = text.lower()
        if infra_file and "http://" in lower and not any(host in lower for host in ("localhost", "127.0.0.1", "example.com")):
            _add(findings, "HIGH", "PLAINTEXT_ENDPOINT", path, number, "non-local HTTP endpoint; use HTTPS or an approved isolated test endpoint")
        if infra_file and re.search(r"(^|[\s:=])0\.0\.0\.0([\s,}\]]|$)", text):
            _add(findings, "MEDIUM", "WILDCARD_BIND", path, number, "wildcard bind address requires explicit staging/production justification")
        if infra_file and re.search(r"\bimage\s*:\s*[^\s:@]+:latest\b", lower):
            _add(findings, "HIGH", "UNPINNED_IMAGE", path, number, "container image uses latest; pin an immutable digest or version")
        if infra_file and ("privileged: true" in lower or "privileged=true" in lower):
            _add(findings, "CRITICAL", "PRIVILEGED_CONTAINER", path, number, "privileged container is not allowed")
        if infra_file and ("hostpath:" in lower or "host_path:" in lower):
            _add(findings, "HIGH", "HOST_PATH_MOUNT", path, number, "host filesystem mount requires security review")
        if infra_file and "automountserviceaccounttoken: true" in lower:
            _add(findings, "HIGH", "SERVICE_ACCOUNT_TOKEN", path, number, "disable automatic service-account token mounting unless required")
        if workflow_file and re.search(r"uses:\s*[^@\s]+\s*$", lower):
            _add(findings, "HIGH", "UNPINNED_ACTION", path, number, "GitHub Action must be pinned to a full commit SHA")
        if infra_file and re.search(r"\b(terraform|docker|kubectl)\s+(apply|run|exec)\b", lower):
            _add(findings, "HIGH", "MUTATING_COMMAND", path, number, "configuration contains a mutating command; review and gate it")


def _scan_structured(path: Path, findings: list[Finding]) -> None:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        _add(findings, "HIGH", "FILE_READ", path, 1, f"cannot read file: {exc}")
        return
    if len(raw) > MAX_FILE_BYTES:
        _add(findings, "HIGH", "FILE_TOO_LARGE", path, 1, f"file exceeds {MAX_FILE_BYTES} bytes")
        return
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _add(findings, "HIGH", "NON_UTF8_CONFIG", path, 1, "configuration must be UTF-8")
        return
    lines = text.splitlines()
    _scan_secret_patterns(path, lines, findings)
    _scan_common_rules(path, lines, findings)
    try:
        if path.suffix.lower() == ".json":
            json.loads(text)
        elif path.suffix.lower() == ".toml":
            tomllib.loads(text)
    except (json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        _add(findings, "HIGH", "PARSE_ERROR", path, getattr(exc, "lineno", 1) or 1, "configuration does not parse")


def scan(root: Path, excludes: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(root, excludes):
        _scan_structured(path, findings)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument("--json", dest="json_output", type=Path, help="write redacted JSON findings")
    parser.add_argument("--exclude", action="append", default=[], help="additional directory name to exclude")
    parser.add_argument("--fail-on", choices=("CRITICAL", "HIGH", "MEDIUM", "LOW"), default="HIGH")
    args = parser.parse_args(argv)

    severity_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    findings = scan(args.root.resolve(), DEFAULT_EXCLUDES | set(args.exclude))
    findings.sort(key=lambda item: (-severity_rank[item.severity], item.path, item.line, item.rule))
    for finding in findings:
        sys.stdout.write(finding.render() + "\n")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps([asdict(item) for item in findings], indent=2) + "\n", encoding="utf-8")
    blocking = [item for item in findings if severity_rank[item.severity] >= severity_rank[args.fail_on]]
    sys.stdout.write(f"\nScanned {args.root}; findings={len(findings)}; blocking={len(blocking)}; fail_on={args.fail_on}\n")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
