from __future__ import annotations

import re
from datetime import UTC
from pathlib import Path
from typing import Any


class AutonomousReviewEngine:
    REVIEW_DIRS = [
        "backend/app/routes/",
        "backend/app/models/",
        "backend/app/services/",
        "backend/app/security/",
        "backend/app/ai/",
        "backend/app/fhir/",
        "backend/app/database.py",
        "backend/app/main.py",
    ]

    VENDOR_SDK_PATTERNS = [
        r"import\s+boto3",
        r"from\s+azure",
        r"from\s+google\.cloud",
        r"import\s+firebase",
        r"from\s+supabase",
        r"import\s+auth0",
        r"import\s+okta",
        r"import\s+stripe",
        r"import\s+twilio",
        r"import\s+sendgrid",
    ]

    SECURITY_PATTERNS = {
        "sql_injection": [r"execute\(.*f[\"']", r"\.format\(.*request\.", r"raw_sql"],
        "secret_leak": [r"(api_key|password|secret|token)\s*=\s*[\"'][^\"']+[\"']"],
        "weak_auth": [r"@router\.(get|post|put|delete).*\n(?!.*Depends)", r"no_auth"],
        "hardcoded_url": [r"https?://[a-z]+\.(com|io|net)"],
    }

    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.findings: list[dict[str, Any]] = []

    def review_all(self) -> list[dict[str, Any]]:
        self.findings = []
        self._review_architecture()
        self._review_dependencies()
        self._review_security()
        self._review_vendor_lock_in()
        self._review_documentation()
        self._review_database()
        self._review_api()
        self._review_ai()
        return self.findings

    def review_pull_request(self, changed_files: list[str]) -> list[dict[str, Any]]:
        self.findings = []
        for f in changed_files:
            full_path = self.repo_root / f
            if not full_path.exists():
                continue
            content = full_path.read_text(encoding="utf-8", errors="replace")
            self._scan_file(f, content)
        return self.findings

    def _scan_file(self, path: str, content: str) -> None:
        for cat, patterns in self.SECURITY_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, content, re.IGNORECASE):
                    self.findings.append({
                        "type": cat,
                        "severity": "HIGH",
                        "file": path,
                        "message": f"Potential {cat.replace('_', ' ')} detected",
                    })
        for pat in self.VENDOR_SDK_PATTERNS:
            if re.search(pat, content):
                self.findings.append({
                    "type": "vendor_lock_in",
                    "severity": "BLOCKER",
                    "file": path,
                    "message": f"Direct vendor SDK import: {pat}",
                })

    def _review_architecture(self) -> None:
        for d in self.REVIEW_DIRS:
            full_path = self.repo_root / d
            if not full_path.exists():
                continue
            if full_path.is_dir():
                for f in full_path.rglob("*.py"):
                    if "__pycache__" not in str(f):
                        content = f.read_text(encoding="utf-8", errors="replace")
                        rel = str(f.relative_to(self.repo_root))
                        self._scan_file(rel, content)
            elif full_path.is_file():
                content = full_path.read_text(encoding="utf-8", errors="replace")
                self._scan_file(d, content)

    def _review_dependencies(self) -> None:
        req_files = [
            self.repo_root / "backend" / "requirements.txt",
            self.repo_root / "package.json",
        ]
        for rf in req_files:
            if rf.exists():
                self.findings.append({
                    "type": "dependency_check",
                    "severity": "INFO",
                    "file": str(rf.relative_to(self.repo_root)),
                    "message": "Dependency file reviewed — run `make constitution-check` for full audit",
                })

    def _review_security(self) -> None:
        sec_dir = self.repo_root / "backend" / "app" / "security"
        if sec_dir.exists():
            self.findings.append({
                "type": "security_review",
                "severity": "INFO",
                "file": "backend/app/security/",
                "message": "Security module present — verify threat models for new changes",
            })

    def _review_vendor_lock_in(self) -> None:
        gateways_dir = self.repo_root / "backend" / "app" / "gateways"
        if gateways_dir.exists():
            for f in gateways_dir.rglob("*.py"):
                if "__pycache__" not in str(f):
                    content = f.read_text(encoding="utf-8", errors="replace")
                    for pat in self.VENDOR_SDK_PATTERNS:
                        if re.search(pat, content):
                            self.findings.append({
                                "type": "vendor_lock_in",
                                "severity": "BLOCKER",
                                "file": str(f.relative_to(self.repo_root)),
                                "message": f"Vendor SDK in gateways: {pat}",
                            })

    def _review_documentation(self) -> None:
        docs_dir = self.repo_root / "docs"
        if docs_dir.exists():
            md_files = list(docs_dir.rglob("*.md"))
            self.findings.append({
                "type": "documentation",
                "severity": "INFO",
                "file": "docs/",
                "message": f"{len(md_files)} documentation files found",
            })

    def _review_database(self) -> None:
        models_dir = self.repo_root / "backend" / "app" / "models"
        if models_dir.exists():
            count = len(list(models_dir.rglob("*.py")))
            self.findings.append({
                "type": "database_review",
                "severity": "INFO",
                "file": "backend/app/models/",
                "message": f"{count} model files found — verify migrations for changes",
            })

    def _review_api(self) -> None:
        routes_dir = self.repo_root / "backend" / "app" / "routes"
        if routes_dir.exists():
            count = len(list(routes_dir.rglob("*.py")))
            self.findings.append({
                "type": "api_review",
                "severity": "INFO",
                "file": "backend/app/routes/",
                "message": f"{count} route files found — verify OpenAPI compliance",
            })

    def _review_ai(self) -> None:
        ai_dirs = [
            self.repo_root / "backend" / "app" / "ai",
            self.repo_root / "backend" / "app" / "ai_fabric",
        ]
        for ai_dir in ai_dirs:
            if ai_dir.exists():
                self.findings.append({
                    "type": "ai_review",
                    "severity": "INFO",
                    "file": str(ai_dir.relative_to(self.repo_root)),
                    "message": "AI module present — verify guardrails and human approval gates",
                })

    def get_report(self) -> dict[str, Any]:
        from datetime import datetime

        blocker = sum(1 for f in self.findings if f["severity"] == "BLOCKER")
        high = sum(1 for f in self.findings if f["severity"] == "HIGH")
        medium = sum(1 for f in self.findings if f["severity"] == "MEDIUM")
        low = sum(1 for f in self.findings if f["severity"] == "LOW")
        info = sum(1 for f in self.findings if f["severity"] == "INFO")

        types = {}
        for f in self.findings:
            t = f["type"]
            if t not in types:
                types[t] = {"count": 0, "severities": []}
            types[t]["count"] += 1
            types[t]["severities"].append(f["severity"])

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "total_findings": len(self.findings),
            "severity_summary": {
                "blocker": blocker,
                "high": high,
                "medium": medium,
                "low": low,
                "info": info,
            },
            "by_type": types,
            "findings": self.findings,
        }
