#!/usr/bin/env python3
"""Safe repository secret scan with explicit reference/fixture classification."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

PATTERNS = {
    "telegram_bot_token": re.compile(r"\b\d{8,12}:AA[A-Za-z0-9_-]{20,}\b"),
    "private_key_header": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "generic_secret_assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*[\"']([^\"']{12,})[\"']"
    ),
}
PEM_BLOCK = re.compile(
    r"-----BEGIN (?P<kind>(?:RSA |EC |OPENSSH )?PRIVATE KEY)-----"
    r"\s*(?P<body>[A-Za-z0-9+/=\r\n]{40,})\s*"
    r"-----END (?P=kind)-----"
)

SKIP_DIRS = {".git", "node_modules", "dist", "venv", "__pycache__", ".audit", "security-audit"}
PLACEHOLDER_WORDS = (
    "example",
    "dummy",
    "test",
    "changeme",
    "replace",
    "your_",
    "your-",
    "secure-password",
    "xxxxx",
    "localhost",
    "placeholder",
)
COMMENT_PREFIXES = ("#", "//", "<!--", "*", "<!--")


def _tracked_files() -> list[Path]:
    return [Path(item) for item in subprocess.check_output(
        ["git", "ls-files", "-co", "--exclude-standard"], text=True
    ).splitlines()]


def _is_fixture_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")


def _is_env_reference(raw: str) -> bool:
    stripped = raw.strip()
    return (
        stripped.startswith("$")
        or stripped.startswith("{{")
        or stripped.startswith("${")
        or stripped.startswith("<")
    )


def _is_comment(line: str) -> bool:
    return line.lstrip().startswith(COMMENT_PREFIXES)


def _finding(
    *,
    kind: str,
    path: Path,
    line: int,
    raw: str,
) -> dict[str, object]:
    lowered = raw.lower()
    return {
        "type": kind,
        "path": str(path),
        "line": line,
        "length": len(raw),
        "placeholder_like": any(word in lowered for word in PLACEHOLDER_WORDS),
        "test_fixture_like": _is_fixture_path(path),
        "sha256_prefix": hashlib.sha256(raw.encode()).hexdigest()[:12],
    }


def scan_file(path: Path) -> list[dict[str, object]]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    findings: list[dict[str, object]] = []
    lines = text.splitlines()
    for line_no, line in enumerate(lines, 1):
        for kind, pattern in PATTERNS.items():
            match = pattern.search(line)
            if not match:
                continue
            if kind == "generic_secret_assignment":
                if _is_comment(line):
                    continue
                raw = match.group(1)
                if _is_env_reference(raw):
                    continue
            elif kind == "private_key_header":
                # A documentation header or a detector pattern is not a key.
                # Complete PEM blocks are scanned below using the full file text.
                continue
            else:
                raw = match.group(0)
            findings.append(_finding(kind=kind, path=path, line=line_no, raw=raw))
            break

    for match in PEM_BLOCK.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        findings.append(_finding(
            kind="private_key",
            path=path,
            line=line_no,
            raw=match.group(0),
        ))
    return findings


def main() -> int:
    findings: list[dict[str, object]] = []
    for path in _tracked_files():
        if any(part in SKIP_DIRS for part in path.parts) or not path.is_file():
            continue
        findings.extend(scan_file(path))

    summary = {
        "finding_count": len(findings),
        "by_type": {
            kind: sum(item["type"] == kind for item in findings)
            for kind in (*PATTERNS.keys(), "private_key")
        },
        "non_placeholder": [
            item for item in findings
            if not item["placeholder_like"] and not item["test_fixture_like"]
        ],
        "test_fixture_like": [item for item in findings if item["test_fixture_like"]],
        "placeholder_like": [item for item in findings if item["placeholder_like"]],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
