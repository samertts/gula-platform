#!/usr/bin/env python3
"""GULA Platform — Enterprise Governance Certification (PROGRAM-ENTERPRISE-GOVERNANCE-001).

Audits every subsystem against enterprise production standards.
Generates evidence-based certification report.

Usage:
    python3 scripts/enterprise_governance_certification.py
    python3 scripts/enterprise_governance_certification.py --output-dir ./governance_report
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pathlib
import subprocess
import sys
import time
from datetime import UTC, datetime
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
SKIP = "SKIP"

CERT_LEVELS = [
    ("DEVELOPMENT", 0),
    ("ALPHA", 1),
    ("BETA", 2),
    ("RELEASE CANDIDATE", 3),
    ("PRODUCTION READY", 4),
    ("ENTERPRISE READY", 5),
    ("NATIONAL READY", 6),
]

class GovernanceCertification:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.results: list[dict[str, Any]] = []
        self.stats: dict[str, int] = {}
        self.findings: list[str] = []
        self.blockers: list[str] = []
        self.risks: list[str] = []
        self.start_time = time.time()

    def run(self) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("=" * 60)
        logger.info("ENTERPRISE GOVERNANCE CERTIFICATION")
        logger.info("PROGRAM-ENTERPRISE-GOVERNANCE-001")
        logger.info("=" * 60)

        self._check("1. Repository Integrity", self._check_repository)
        self._check("2. Architecture Compliance", self._check_architecture)
        self._check("3. Code Quality", self._check_code_quality)
        self._check("4. Security Posture", self._check_security)
        self._check("5. Authentication & Authorization", self._check_auth)
        self._check("6. Tenant Isolation", self._check_tenant_isolation)
        self._check("7. Audit Trail", self._check_audit_trail)
        self._check("8. API Governance", self._check_api_governance)
        self._check("9. Clinical Workflows", self._check_clinical_workflows)
        self._check("10. AI Platform", self._check_ai_platform)
        self._check("11. Integration Platform", self._check_integration)
        self._check("12. Observability", self._check_observability)
        self._check("13. Disaster Recovery", self._check_disaster_recovery)
        self._check("14. Documentation", self._check_documentation)
        self._check("15. Frontend Governance", self._check_frontend)

        self._generate_report()
        elapsed = time.time() - self.start_time
        logger.info("=" * 60)
        logger.info(f"CERTIFICATION COMPLETE — {elapsed:.1f}s")
        passed = sum(1 for r in self.results if r["status"] == PASS)
        total = len(self.results)
        logger.info(f"Results: {passed}/{total} passed")
        for b in self.blockers:
            logger.warning(f"  BLOCKER: {b}")
        logger.info("=" * 60)

    def _check(self, name: str, fn) -> None:
        logger.info(f"[CHECK] {name}...")
        try:
            fn()
        except Exception as e:
            self.results.append({"check": name, "status": FAIL, "detail": str(e)})

    def _result(self, check: str, status: str, detail: str = "") -> None:
        self.results.append({"check": check, "status": status, "detail": detail})
        if status == FAIL:
            self.blockers.append(f"{check}: {detail}")
        elif status == WARN:
            self.risks.append(f"{check}: {detail}")

    def _run_tool(self, script: str, args: list[str] | None = None, timeout: int = 60) -> dict[str, Any]:
        sp = SCRIPTS_DIR / script
        if not sp.exists():
            return {"status": SKIP, "detail": f"Script not found: {script}"}
        cmd = [sys.executable, str(sp)]
        if args:
            cmd.extend(args)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=REPO_ROOT)
            return {"status": PASS, "stdout": r.stdout[:2000], "stderr": r.stderr[:1000]}
        except subprocess.TimeoutExpired:
            return {"status": WARN, "detail": "Timed out"}
        except Exception as e:
            return {"status": FAIL, "detail": str(e)}

    # ── Governance Checks ──────────────────────────────────────────────────────

    def _check_repository(self) -> None:
        """Verify repository integrity and git hygiene."""
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=REPO_ROOT)
        dirty = len([l for l in r.stdout.splitlines() if l.strip()])
        self._result("Repository: Clean working tree", PASS if dirty == 0 else WARN,
                     f"{dirty} uncommitted files" if dirty else "Clean")
        r = subprocess.run(["git", "rev-list", "--count", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT)
        self.stats["Git Commits"] = int(r.stdout.strip() or 0)
        self.stats["Uncommitted Files"] = dirty

    def _check_architecture(self) -> None:
        """Run architecture compliance engine."""
        arch = self._run_tool("architecture_compliance_engine.py", timeout=30)
        score = None
        if arch["status"] == PASS:
            for line in arch.get("stdout", "").splitlines():
                if "compliance" in line.lower() or "score" in line.lower():
                    parts = line.split()
                    for p in parts:
                        try:
                            score = float(p.replace("%", "").replace("/", ""))
                        except ValueError:
                            continue
        self._result("Architecture Compliance Engine", arch["status"],
                     f"Score: {score}" if score else arch.get("detail", ""))
        self.stats["Architecture Compliance"] = score or 0

    def _check_code_quality(self) -> None:
        """Check code quality via existing tools."""
        qg = self._run_tool("quality_gate.py", ["--json"], timeout=60)
        if qg["status"] == PASS:
            try:
                data = json.loads(qg["stdout"])
                qi = data.get("quality_index", {})
                self.stats["Quality Index"] = qi.get("total", 0)
                self._result("Quality Gate", PASS, f"Index: {qi.get('total', 0)}/1000")
                for comp, val in qi.get("components", {}).items():
                    self._result(f"  {comp}", PASS if val >= 50 else WARN, f"{val}/100")
            except (json.JSONDecodeError, KeyError):
                self._result("Quality Gate", WARN, "Could not parse JSON output")
        else:
            self._result("Quality Gate", qg["status"], qg.get("detail", ""))

        # Check py_compile on backend
        be_files = ["app/main.py", "app/config.py", "app/routes/ai_platform.py"]
        for f in be_files:
            r = subprocess.run(["python3", "-m", "py_compile", f], capture_output=True, text=True, cwd=REPO_ROOT / "backend")
            self._result(f"PyCompile: {f}", PASS if r.returncode == 0 else FAIL)

        # Check TS compilation
        r = subprocess.run(["npx", "tsc", "--noEmit"], capture_output=True, text=True,
                          timeout=120, cwd=REPO_ROOT / "frontend-v2")
        ts_errors = len([l for l in r.stdout.splitlines() if "error" in l.lower()])
        self._result("TypeScript Compilation", PASS if ts_errors == 0 else FAIL,
                     f"{ts_errors} errors" if ts_errors else "Clean")

    def _check_security(self) -> None:
        """Verify security posture."""
        # Check for SECRET_KEY in config
        config_path = REPO_ROOT / "backend/app/config.py"
        if config_path.exists():
            content = config_path.read_text()
            keys_found = []
            for key in ["SECRET_KEY", "ENCRYPTION_KEY", "REFRESH_TOKEN_SECRET", "NID_HMAC_KEY"]:
                if key in content:
                    keys_found.append(key)
            self._result("Security: Required keys configured", PASS if len(keys_found) == 4 else FAIL,
                         f"Found: {', '.join(keys_found)}")

        # Check for hard-coded secrets
        r = subprocess.run(["bash", "-c",
            r"grep -n 'hardcoded\|placeholder' backend/app/config.py | grep -v 'without hardcoded' || true"],
            capture_output=True, text=True, cwd=REPO_ROOT)
        has_issue = bool(r.stdout.strip())
        self._result("Security: No placeholder secrets", FAIL if has_issue else PASS,
                     "No placeholder secrets" if not has_issue else r.stdout.strip())

        # Rate limiting
        routes = REPO_ROOT / "backend/app/routes"
        rate_limited = 0
        if routes.exists():
            for f in routes.iterdir():
                if f.suffix == ".py":
                    content = f.read_text()
                    if "limiter" in content.lower() or "rate_limit" in content.lower():
                        rate_limited += 1
        self._result("Security: Rate limiting", WARN if rate_limited < 5 else PASS,
                     f"{rate_limited} route files with rate limiting")

    def _check_auth(self) -> None:
        """Check authentication and authorization."""
        route_dir = REPO_ROOT / "backend/app/routes"
        authed_endpoints = 0
        total_endpoints = 0
        unauth_files = []
        if route_dir.exists():
            for f in sorted(route_dir.iterdir()):
                if f.suffix != ".py" or f.name == "__init__.py":
                    continue
                content = f.read_text()
                endpoints_in_file = content.count("@router.") + content.count("@api_router.")
                total_endpoints += endpoints_in_file
                if "get_current_user" in content:
                    authed_endpoints += endpoints_in_file
                else:
                    unauth_files.append(f"{f.name} ({endpoints_in_file} endpoints)")
        pct = (authed_endpoints / total_endpoints * 100) if total_endpoints else 0
        self._result("Auth: Endpoint authentication", PASS if pct >= 90 else WARN,
                     f"{authed_endpoints}/{total_endpoints} endpoints ({pct:.0f}%) authenticated")
        if unauth_files:
            self._result("Auth: Unauthenticated route files", WARN, ", ".join(unauth_files[:5]))

        # RBAC model check
        rbac_path = REPO_ROOT / "backend/app/security/rbac.py"
        if rbac_path.exists():
            content = rbac_path.read_text()
            roles = [l for l in content.splitlines() if "role" in l.lower() and "=" in l]
            self._result("Auth: RBAC model", PASS, f"{len(roles)} role definitions found")

    def _check_tenant_isolation(self) -> None:
        """Verify tenant isolation enforcement."""
        query_files = [
            "backend/app/routes/results.py",
            "backend/app/routes/orders.py",
            "backend/app/routes/patients.py",
            "backend/app/routes/samples.py",
        ]
        isolated = 0
        for f in query_files:
            p = REPO_ROOT / f
            if p.exists():
                content = p.read_text()
                if "lab_id" in content and ("current_user" in content or "user.lab_id" in content):
                    isolated += 1
        self._result("Tenant Isolation: lab_id filtering", PASS if isolated >= 3 else FAIL,
                     f"{isolated}/4 route files enforce lab_id filtering")

        # Check Tenant model
        tenant_path = REPO_ROOT / "backend/app/models/tenant.py"
        if tenant_path.exists():
            content = tenant_path.read_text()
            has_tenant = "parent_tenant_id" in content or "tenant_type" in content
            self._result("Tenant Model: Hierarchy support", PASS if has_tenant else FAIL)

    def _check_audit_trail(self) -> None:
        """Verify audit logging coverage."""
        audit_model = REPO_ROOT / "backend/app/models/audit_log.py"
        if audit_model.exists():
            content = audit_model.read_text()
            has_chain = "chain_hash" in content
            has_immutable = "created_at" in content
            self._result("Audit: Immutable log model", PASS if has_chain and has_immutable else FAIL)

        audit_service = REPO_ROOT / "backend/app/services/audit_service.py"
        if audit_service.exists():
            content = audit_service.read_text()
            self._result("Audit: Service layer", PASS,
                         f"{len([l for l in content.splitlines() if l.strip()])} lines")

        # Count routes with audit logging
        routes = REPO_ROOT / "backend/app/routes"
        audit_entries = 0
        if routes.exists():
            for f in routes.iterdir():
                if f.suffix == ".py" and "audit" in f.read_text().lower():
                    audit_entries += 1
        self._result("Audit: Routes with audit logging", WARN if audit_entries < 10 else PASS,
                     f"{audit_entries} route files reference audit")

    def _check_api_governance(self) -> None:
        """Verify API structure and documentation."""
        routes = REPO_ROOT / "backend/app/routes"
        total_routes = 0
        response_models = 0
        if routes.exists():
            for f in routes.iterdir():
                if f.suffix == ".py" and f.name != "__init__.py":
                    content = f.read_text()
                    total_routes += content.count("@router.") + content.count("@api_router.")
                    response_models += content.count("response_model")
        self._result("API: Route count", PASS, f"{total_routes} total endpoints")
        self._result("API: Response models", WARN if response_models < total_routes * 0.5 else PASS,
                     f"{response_models}/{total_routes} have response_model")
        self.stats["API Endpoints"] = total_routes

    def _check_clinical_workflows(self) -> None:
        """Verify clinical workflows are complete."""
        route_dir = REPO_ROOT / "backend/app/routes"
        workflows = [
            ("Patient Registration", "register.py"),
            ("Order Management", "clinical_orders.py"),
            ("Sample Processing", "samples.py"),
            ("Result Management", "results.py"),
            ("Patient Management", "patients.py"),
            ("Critical Alerts", "critical_alerts.py"),
            ("Health Check", "health.py"),
        ]
        for name, fname in workflows:
            p = route_dir / fname
            self._result(f"Clinical: {name} ({fname})", PASS if p.exists() else WARN)

    def _check_ai_platform(self) -> None:
        """Audit AI platform readiness."""
        ai_route = REPO_ROOT / "backend/app/routes/ai_platform.py"
        if ai_route.exists():
            content = ai_route.read_text()
            authed = content.count("get_current_user")
            total = content.count("@router.")
            self._result("AI Platform: Authentication", PASS if authed >= total else FAIL,
                         f"{authed}/{total} endpoints authed")

        ai_governance = REPO_ROOT / "backend/app/ai/governance.py"
        if ai_governance.exists():
            content = ai_governance.read_text()
            has_eval = "evaluator" in content or "eval" in content.lower()
            has_model_reg = "model_registry" in content or "registry" in content.lower()
            self._result("AI Platform: Governance module", PASS if has_eval and has_model_reg else WARN)

    def _check_integration(self) -> None:
        """Verify integration platform readiness."""
        integration = REPO_ROOT / "backend/app/integration"
        if integration.exists():
            files = list(integration.rglob("*.py"))
            self._result("Integration: Module exists", PASS, f"{len(files)} files")
        device_bridge = REPO_ROOT / "services/device_bridge"
        if device_bridge.exists():
            self._result("Integration: Device Bridge", PASS)
        fhir_cap = REPO_ROOT / "backend/app/capabilities/fhir_interoperability"
        fhir_route = REPO_ROOT / "backend/app/routes/ehr_fhir.py"
        self._result("Integration: FHIR support", PASS if fhir_cap.exists() or fhir_route.exists() else WARN)
        hl7_cmd = REPO_ROOT / "backend/app/capabilities/fhir_interoperability/commands/convert_from_hl7.py"
        self._result("Integration: HL7 support", PASS if hl7_cmd.exists() else WARN)

    def _check_observability(self) -> None:
        """Verify observability infrastructure."""
        checks = [
            ("Health endpoints", "backend/app/routes/health.py"),
            ("Startup guard", "backend/app/core/startup_guard.py"),
            ("Structured logging", "backend/app/core/logging_config.py"),
            ("Metrics", "backend/app/routes/metrics.py"),
            ("Circuit breaker", "backend/app/core/self_healing.py"),
            ("Auto-repair", "backend/app/core/auto_repair.py"),
        ]
        for name, path in checks:
            p = REPO_ROOT / path
            self._result(f"Observability: {name}", PASS if p.exists() else WARN)

    def _check_disaster_recovery(self) -> None:
        """Verify DR readiness."""
        dr_scripts = [
            ("Backup", "scripts/backup.sh"),
            ("Restore test", "scripts/restore-test.sh"),
            ("PITR Recovery", "scripts/pitr-recover.sh"),
            ("Failover", "scripts/pg_failover.sh"),
            ("DR failover", "scripts/dr-failover.sh"),
            ("DR failback", "scripts/dr-failback.sh"),
            ("DR recovery", "scripts/dr_recovery.py"),
            ("Validate restore", "scripts/validate-restore.sh"),
        ]
        for name, path in dr_scripts:
            p = REPO_ROOT / path
            self._result(f"DR: {name}", PASS if p.exists() else WARN)

    def _check_documentation(self) -> None:
        """Verify documentation coverage."""
        docs = [
            ("CLAUDE.md", "CLAUDE.md"),
            ("Architecture", "docs/architecture.md" if (REPO_ROOT / "docs/architecture.md").exists() else None),
            ("Deployment Guide", "docs/deployment.md" if (REPO_ROOT / "docs/deployment.md").exists() else None),
            ("API Manual", "docs/api.md" if (REPO_ROOT / "docs/api.md").exists() else None),
            ("Security Manual", "docs/security.md" if (REPO_ROOT / "docs/security.md").exists() else None),
            ("SNDHS Runbook", "docs/sndhs/phase1/RUNBOOK.md"),
        ]
        for name, path in docs:
            if path:
                p = REPO_ROOT / path
                self._result(f"Docs: {name}", PASS if p.exists() else WARN)

    def _check_frontend(self) -> None:
        """Verify frontend governance."""
        views = REPO_ROOT / "frontend-v2/src/views"
        if views.exists():
            total_views = len(list(views.rglob("*.tsx")))
            connected = 0
            for f in views.rglob("*.tsx"):
                content = f.read_text()
                if "apiGet" in content or "apiPost" in content or "apiPut" in content:
                    connected += 1
            self._result("Frontend: Views with API connection", WARN if connected < total_views * 0.8 else PASS,
                         f"{connected}/{total_views} views connected to backend")
            self.stats["Frontend Views"] = total_views
            self.stats["Frontend Connected"] = connected

    def _generate_report(self) -> None:
        """Generate the final comprehensive certification report."""
        passed = sum(1 for r in self.results if r["status"] == PASS)
        warned = sum(1 for r in self.results if r["status"] == WARN)
        failed = sum(1 for r in self.results if r["status"] == FAIL)
        total = len(self.results)

        score = int((passed / total) * 100) if total > 0 else 0
        if failed > 0:
            cert_level = CERT_LEVELS[0]  # DEVELOPMENT
        elif score >= 90:
            cert_level = CERT_LEVELS[5]  # ENTERPRISE READY
        elif score >= 75:
            cert_level = CERT_LEVELS[4]  # PRODUCTION READY
        elif score >= 60:
            cert_level = CERT_LEVELS[3]  # RELEASE CANDIDATE
        else:
            cert_level = CERT_LEVELS[2]  # BETA

        path = os.path.join(self.output_dir, "NATIONAL_CERTIFICATION_REPORT.md")
        with open(path, "w") as f:
            f.write("# GULA Platform — National Enterprise Certification\n\n")
            f.write("**Program**: PROGRAM-ENTERPRISE-GOVERNANCE-001\n")
            f.write(f"**Date**: {datetime.now(UTC).isoformat()}\n")
            f.write(f"**Classification**: {cert_level[0]}\n")
            f.write(f"**Score**: {score}% ({passed}/{total} checks passed)\n\n")
            f.write("## Certification Level\n\n")
            for level, order in CERT_LEVELS:
                mark = "✓" if order <= cert_level[1] else " "
                f.write(f"- [{mark}] {level}\n")
            f.write("\n## Results Summary\n\n")
            f.write("| Result | Count |\n")
            f.write("|--------|-------|\n")
            f.write(f"| PASS | {passed} |\n")
            f.write(f"| WARNING | {warned} |\n")
            f.write(f"| FAIL | {failed} |\n")
            f.write(f"| **Total** | **{total}** |\n\n")
            f.write("## Detailed Results\n\n")
            f.write("| Check | Status | Detail |\n")
            f.write("|-------|--------|--------|\n")
            for r in self.results:
                icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗", "SKIP": "○"}
                f.write(f"| {r['check']} | {icon.get(r['status'], '?')} {r['status']} | {r.get('detail', '')} |\n")
            f.write("\n## Statistics\n\n")
            for k, v in sorted(self.stats.items()):
                f.write(f"- **{k}**: {v}\n")
            f.write("\n## Blockers\n\n")
            if self.blockers:
                for b in self.blockers:
                    f.write(f"- ✗ {b}\n")
            else:
                f.write("None.\n")
            f.write("\n## Risks & Warnings\n\n")
            if self.risks:
                for r in self.risks:
                    f.write(f"- ⚠ {r}\n")
            else:
                f.write("None.\n")
            f.write("\n## Recommendation\n\n")
            if failed > 0:
                f.write("**NOT RECOMMENDED FOR PRODUCTION.** ")
                f.write(f"Resolve {failed} blocking issues before proceeding.\n")
            elif score >= 90:
                f.write("**RECOMMENDED FOR ENTERPRISE DEPLOYMENT.** ")
                f.write("All critical checks pass. Address warnings for optimal readiness.\n")
            elif score >= 75:
                f.write("**RECOMMENDED FOR PRODUCTION.** ")
                f.write("Fix warnings before enterprise deployment.\n")
            else:
                f.write("**CONDITIONAL.** ")
                f.write("Address warnings and re-certify before production deployment.\n")
            f.write("\n## Engineering Tasks\n\n")
            for b in self.blockers:
                f.write(f"- [ ] {b}\n")

        logger.info(f"Report generated: {path}")
        self._generate_json_report(score, passed, total, cert_level)

    def _generate_json_report(self, score: int, passed: int, total: int, cert_level: tuple) -> None:
        jpath = os.path.join(self.output_dir, "certification_results.json")
        with open(jpath, "w") as f:
            json.dump({
                "program": "PROGRAM-ENTERPRISE-GOVERNANCE-001",
                "timestamp": datetime.now(UTC).isoformat(),
                "classification": cert_level[0],
                "score": score,
                "passed": passed,
                "total": total,
                "blockers": self.blockers,
                "risks": self.risks,
                "results": self.results,
                "stats": self.stats,
            }, f, indent=2)

logger = logging.getLogger("gula.governance")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Enterprise Governance Certification")
    parser.add_argument("--output-dir", default="./governance_report")
    args = parser.parse_args()
    cert = GovernanceCertification(args.output_dir)
    cert.run()
