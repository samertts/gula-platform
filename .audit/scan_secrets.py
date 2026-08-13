import re
import subprocess
from pathlib import Path

patterns = {
    "telegram_bot_token": re.compile(r"\b\d{8,12}:AA[A-Za-z0-9_-]{20,}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "generic_secret_assignment": re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*[\"'][^\"']{12,}[\"']"),
}

tracked = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard"], text=True).splitlines()
ignored_parts = {".git", "node_modules", "dist", "venv", "__pycache__", ".audit"}
findings = []
for item in tracked:
    path = Path(item)
    if any(part in ignored_parts for part in path.parts) or not path.is_file():
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for line_no, line in enumerate(text.splitlines(), 1):
        for name, pattern in patterns.items():
            if pattern.search(line):
                findings.append({"type": name, "path": str(path), "line": line_no})

print({"finding_count": len(findings), "findings": findings})
