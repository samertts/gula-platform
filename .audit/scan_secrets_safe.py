import hashlib
import json
import re
import subprocess
from pathlib import Path

patterns = {
    "telegram_bot_token": re.compile(r"\b\d{8,12}:AA[A-Za-z0-9_-]{20,}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "generic_secret_assignment": re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*[\"']([^\"']{12,})[\"']"),
}

skip_dirs = {".git", "node_modules", "dist", "venv", "__pycache__", ".audit", "security-audit"}
placeholder_words = ("example", "dummy", "test", "changeme", "replace", "your_", "xxxxx", "localhost", "secret")
tracked = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard"], text=True).splitlines()
findings = []
for item in tracked:
    path = Path(item)
    if any(part in skip_dirs for part in path.parts) or not path.is_file():
        continue
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        continue
    for line_no, line in enumerate(lines, 1):
        for kind, pattern in patterns.items():
            match = pattern.search(line)
            if not match:
                continue
            raw = match.group(1) if kind == "generic_secret_assignment" else match.group(0)
            lowered = raw.lower()
            is_placeholder = any(word in lowered for word in placeholder_words)
            findings.append({
                "type": kind,
                "path": str(path),
                "line": line_no,
                "length": len(raw),
                "placeholder_like": is_placeholder,
                "sha256_prefix": hashlib.sha256(raw.encode()).hexdigest()[:12],
            })
            break

summary = {
    "finding_count": len(findings),
    "by_type": {kind: sum(x["type"] == kind for x in findings) for kind in patterns},
    "non_placeholder": [x for x in findings if not x["placeholder_like"]],
    "placeholder_like": [x for x in findings if x["placeholder_like"]],
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
