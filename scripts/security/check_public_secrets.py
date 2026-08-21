#!/usr/bin/env python3
"""Fail CI when tracked source files contain likely live secrets.

This is defense in depth; GitHub secret scanning remains authoritative. The
check focuses on concrete provider-token formats and quoted literal secret
assignments, not ordinary variable names such as ``access_token``.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

EXCLUDED_PARTS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".gradle",
    ".dart_tool",
    "Pods",
    "tests",
    "test",
    "e2e",
    "docs",
}
EXCLUDED_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements-lock.txt",
    "poetry.lock",
}
EXCLUDED_PREFIXES = (
    "security-audit/",
    "docs/security/",
)
FORBIDDEN_TRACKED_ARTIFACTS = {
    ".jks",
    "signing.properties",
}

TEXT_EXTENSIONS = {
    ".c", ".cfg", ".conf", ".dart", ".env", ".gradle", ".h", ".java",
    ".js", ".json", ".jsx", ".kts", ".kt", ".properties", ".py", ".rb",
    ".sql", ".swift", ".tf", ".toml", ".ts", ".tsx", ".txt", ".xml",
    ".yaml", ".yml",
}

PATTERNS = [
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("openai-style-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("jwt-like-value", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    (
        "private-key-block",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
            r"[\s\S]{40,}?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
        ),
    ),
    (
        "secret-literal-assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|client[_-]?secret|private[_-]?key|secret[_-]?key|"
            r"access[_-]?token|refresh[_-]?token|aws[_-]?secret[_-]?access[_-]?key)"
            r"\s*[:=]\s*['\"](?!\$\{|<|CHANGE_ME|REPLACE_ME|your[_-]|test[_-])"
            r"[A-Za-z0-9_./+=:-]{16,}['\"]"
        ),
    ),
]


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], check=True, capture_output=True, text=False
    )
    return [Path(item) for item in result.stdout.decode().split("\0") if item]


def is_candidate(path: Path) -> bool:
    value = path.as_posix()
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.name in EXCLUDED_NAMES or value.startswith(EXCLUDED_PREFIXES):
        return False
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name.startswith(".env")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-history", action="store_true", help="reserved for GitHub secret scanning")
    parser.parse_args()

    findings: list[tuple[str, int, str, str]] = []
    for path in tracked_files():
        if path.suffix.lower() in FORBIDDEN_TRACKED_ARTIFACTS or path.name in FORBIDDEN_TRACKED_ARTIFACTS:
            findings.append((path.as_posix(), 0, "tracked-signing-artifact", "[path-only check]"))
            continue
        if not is_candidate(path) or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue
        for name, pattern in PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            line_number = text.count("\n", 0, match.start()) + 1
            snippet = text.splitlines()[line_number - 1].strip()[:160]
            findings.append((path.as_posix(), line_number, name, snippet))

    if findings:
        sys.stdout.write("Potential public secrets detected:\n")
        for path, line_number, name, snippet in findings:
            sys.stdout.write(f"- {path}:{line_number} [{name}] {snippet[:80]!r}\n")
        return 1

    sys.stdout.write("OK: no likely public secrets found in tracked source files\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
