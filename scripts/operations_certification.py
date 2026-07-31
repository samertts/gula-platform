#!/usr/bin/env python3
"""
GULA Platform — Operations Readiness Certification (PROGRAM-011)
================================================================

Evaluates the enterprise operations layer across the nine PROGRAM-011
phases with evidence-based static checks and produces:

  reports/ops/OPERATIONS_READINESS_REPORT.md   (master report + health score)
  reports/ops/observability_report.md          (Phase 1)
  reports/ops/monitoring_report.md             (Phase 2)
  reports/ops/recovery_report.md               (Phases 5 + 3 diagnostics)
  reports/ops/automation_report.md             (Phase 8)
  reports/ops/security_operations_report.md    (Phase 7)
  reports/ops/overall_health.json              (machine-readable score)

Usage:
  python scripts/operations_certification.py
  python scripts/operations_certification.py --output-dir ./reports/ops
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import subprocess
import sys
import time
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT_DIR = pathlib.Path(os.getenv("OPS_CERT_OUTPUT", "reports/ops"))

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
SKIP = "SKIP"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("ops-cert")

PHASES: list[tuple[str, str]] = [
    ("1. Observability", "observability_report.md"),
    ("2. Monitoring", "monitoring_report.md"),
    ("3. Self-Diagnostics", "recovery_report.md"),
    ("4. Self-Healing", "recovery_report.md"),
    ("5. Backup & Recovery", "recovery_report.md"),
    ("6. Operations Dashboard", "operations_dashboard_report.md"),
    ("7. Security Operations", "security_operations_report.md"),
    ("8. Automation", "automation_report.md"),
    ("9. Documentation", "operations_manual_report.md"),
]


class OpsCertification:
    def __init__(self, output_dir: str | os.PathLike[str]) -> None:
        self.output_dir = pathlib.Path(output_dir)
        self.results: list[dict[str, Any]] = []
        self.start_time = time.time()

    # ── helpers ────────────────────────────────────────────────────────────────

    def _check(self, name: str, fn: Any) -> None:
        try:
            fn()
        except Exception as exc:  # pragma: no cover - defensive
            self._result(name, FAIL, str(exc))

    def _result(self, check: str, status: str, detail: str = "") -> None:
        self.results.append({"check": check, "status": status, "detail": detail})

    @staticmethod
    def _exists(rel: str) -> bool:
        return (REPO_ROOT / rel).exists()

    def _has_text(self, rel: str, *needles: str) -> bool:
        p = REPO_ROOT / rel
        if not p.exists():
            return False
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return False
        return all(n in text for n in needles)

    def _run(self, cmd: list[str], timeout: int = 120) -> tuple[int, str]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=REPO_ROOT)
            return r.returncode, (r.stdout + r.stderr).strip()
        except (OSError, subprocess.TimeoutExpired) as exc:
            return 1, f"failed: {exc}"

    # ── Phase 1: Observability ─────────────────────────────────────────────────

    def _phase_observability(self) -> None:
        checks: list[tuple[str, bool]] = [
            ("Structured logging: JSONFormatter in shared/logging", self._has_text(
                "shared/logging/config.py", "class JSONFormatter", "request_id", "trace_id")),
            ("Logging configured at app entry (main.py)", self._has_text(
                "backend/app/main.py", "configure_logging(", "LOG_LEVEL")),
            ("Request ID middleware (X-Request-ID)", self._has_text(
                "backend/app/middleware.py", "class RequestIDMiddleware", "X-Request-ID")),
            ("Access-log + latency middleware", self._has_text(
                "backend/app/middleware.py", "class RequestTimingMiddleware", "X-Response-Time")),
            ("Liveness endpoint /health/live", self._has_text(
                "backend/app/main.py", "/health/live")),
            ("Readiness endpoint /health/ready", self._has_text(
                "backend/app/main.py", "/health/ready", "startup_guard")),
            ("Deep diagnostics /health/deep", self._has_text(
                "backend/app/main.py", "/health/deep", "GREEN")),
            ("Prometheus exposition /metrics/prom", self._has_text(
                "backend/app/routes/metrics.py", "/metrics/prom")),
            ("Request SLO metrics (histogram + counters)", self._has_text(
                "backend/app/services/metrics_service.py",
                "gula_request_duration_seconds", "gula_requests_total")),
            ("DB error metrics", self._has_text(
                "backend/app/services/metrics_service.py", "gula_db_refused_total")),
            ("Redis latency metric", self._has_text(
                "backend/app/services/metrics_service.py", "gula_redis_latency_ms")),
            ("Runtime log-level control", self._has_text(
                "backend/app/routes/admin_log_level.py", "log-level")),
            ("Audit frontend page", self._has_text(
                "frontend-v3/src/pages/admin/AdminPages.tsx", "audit")),
        ]
        for name, ok in checks:
            self._result(f"P1 · {name}", PASS if ok else FAIL)
        self._result("P1 · Distributed tracing export (OTel)", WARN,
                     "tracer.py debug-logs spans; Jaeger/Tempo provisioned but no SDK export")

    # ── Phase 2: Monitoring ────────────────────────────────────────────────────

    def _phase_monitoring(self) -> None:
        checks: list[tuple[str, bool]] = [
            ("Prometheus config present", self._exists("config/prometheus/prometheus.yml")),
            ("Prometheus scrapes app metrics with auth", self._has_text(
                "config/prometheus/prometheus.yml", "metrics/prom", "authorization")),
            ("Grafana provisioning (datasources)", self._has_text(
                "config/grafana/provisioning/datasources/datasources.yml", "prometheus")),
            ("Grafana dashboards (>=8)", (REPO_ROOT / "config/grafana/dashboards").exists()
             and len(list((REPO_ROOT / "config/grafana/dashboards").glob("*.json"))) >= 8),
            ("Alert rules (gula.yml)", self._has_text(
                "config/prometheus/rules/gula.yml", "alert:")),
            ("SLO rules (slo.yml) grounded in exported metrics", self._has_text(
                "config/prometheus/rules/slo.yml", "gula_request_duration_seconds")),
            ("Alertmanager config", self._has_text(
                "config/alertmanager/alertmanager.yml", "webhook")),
            ("Backend health-alert loop (webhook)", self._has_text(
                "backend/app/core/startup.py", "ALERT_WEBHOOK_URL")),
            ("Cron uptime monitor w/ Telegram", self._has_text(
                "scripts/monitor.sh", "TELEGRAM", "health/ready")),
            ("Container/node metrics (node-exporter)", self._has_text(
                "docker-compose.full.yml", "node-exporter")),
            ("Makefile monitoring profile", self._has_text(
                "Makefile", "monitoring", "grafana")),
        ]
        for name, ok in checks:
            self._result(f"P2 · {name}", PASS if ok else FAIL)
        self._result("P2 · Grafana alerting provisioning", WARN,
                     "Alerting via Prometheus rules + Alertmanager webhook; no Grafana alert provisioning files")

    # ── Phase 3: Self-Diagnostics ──────────────────────────────────────────────

    def _phase_diagnostics(self) -> None:
        checks: list[tuple[str, bool]] = [
            ("diagnose.sh", self._exists("scripts/diagnose.sh")),
            ("diagnose-droplet.sh (read-only snapshot)", self._exists("scripts/diagnose-droplet.sh")),
            ("health-probes/check-all.sh (parallel probes)", self._exists("scripts/health-probes/check-all.sh")),
            ("verify_environment.sh", self._exists("scripts/verify_environment.sh")),
            ("preflight.sh (deploy gate)", self._exists("scripts/preflight.sh")),
            ("integration_test.sh (10 E2E checks)", self._exists("scripts/integration_test.sh")),
            ("DB circuit breaker", self._has_text(
                "backend/app/core/self_healing.py", "db_circuit")),
            ("Redis circuit breaker", self._has_text(
                "backend/app/core/self_healing.py", "redis_circuit")),
            ("Auth-failure logging (login_failed)", self._has_text(
                "backend/app/routes/login.py", "login_failed")),
            ("Cert expiry detection", self._has_text(
                "scripts/cert-renew.sh", "get_cert_expiry_days", "CRITICAL")),
            ("Migration failure detection", self._has_text(
                "scripts/diagnose-droplet.sh", "alembic")),
            ("Memory pressure detection", self._has_text(
                "backend/app/core/auto_repair.py", "VmRSS")),
        ]
        for name, ok in checks:
            self._result(f"P3 · {name}", PASS if ok else FAIL)
        self._result("P3 · Outbox-backlog auto-repair", WARN,
                     "detected + logged in auto_repair.py; repair action not implemented (docstring promise)")
        self._result("P3 · ASHS restart cooldown", WARN,
                     "self_heal.py has no per-signal cooldown — restart-loop risk if system stays stuck")

    # ── Phase 4: Self-Healing ──────────────────────────────────────────────────

    def _phase_self_healing(self) -> None:
        checks: list[tuple[str, bool]] = [
            ("DegradedModeMiddleware (L1/L2/L3)", self._has_text(
                "backend/app/core/self_healing.py", "DegradedModeMiddleware")),
            ("Monotonic escalation + hysteresis", self._has_text(
                "backend/app/core/self_healing.py", "update_degraded_state")),
            ("Kill switch (always reachable)", self._exists("backend/app/core/kill_switch.py")),
            ("RecoveryWorker probe loop", self._has_text(
                "backend/app/core/self_healing.py", "RecoveryWorker")),
            ("Auto-repair actions (gc/pool/redis)", self._has_text(
                "backend/app/core/auto_repair.py", "memory_gc", "redis_reconnect")),
            ("Policy-gated repairs", self._has_text(
                "backend/app/core/auto_repair.py", "guard_repair")),
            ("ASHS external agent (container restarts)", self._exists("scripts/self_heal.py")),
            ("auto_heal.sh watchdog w/ restart cap", self._has_text(
                "scripts/auto_heal.sh", "MAX_RESTARTS_PER_HOUR")),
            ("gula_autofix.py (DB error log scan)", self._exists("scripts/gula_autofix.py")),
            ("Healer tests (resilience suites)", self._exists("backend/tests/test_resilience_smoke.py")),
        ]
        for name, ok in checks:
            self._result(f"P4 · {name}", PASS if ok else FAIL)

    # ── Phase 5: Backup & Recovery ─────────────────────────────────────────────

    def _phase_backup(self) -> None:
        checks: list[tuple[str, bool]] = [
            ("backup.sh (PG dump + checksum)", self._has_text("scripts/backup.sh", "sha256sum")),
            ("Optional AES-256 encryption", self._has_text("scripts/backup.sh", "aes-256-cbc")),
            ("backup-verification.sh (PostgreSQL restore test)", self._has_text(
                "scripts/backup-verification.sh", "psql", "TEST_DB_NAME")),
            ("restore-test.sh (temp container restore)", self._exists("scripts/restore-test.sh")),
            ("validate-restore.sh (audit chain check)", self._has_text(
                "scripts/validate-restore.sh", "chain")),
            ("pitr-recover.sh (WAL archive recovery)", self._exists("scripts/pitr-recover.sh")),
            ("PITR runbook", self._exists("docs/dr/PITR_RUNBOOK.md")),
            ("DR failover/failback scripts", self._has_text(
                "scripts/dr-failover.sh", "failover") and self._exists("scripts/dr-failback.sh")),
            ("DR drill script", self._exists("scripts/dr-test.sh")),
            ("Snapshot management", self._exists("scripts/manage-snapshots.sh")),
            ("Committed scheduling (crons in server-setup)", self._has_text(
                "scripts/server-setup.sh", "backup-verification", "cert-renew")),
            ("CI backup drill", self._has_text(
                ".github/workflows/nightly.yml", "backup-drill")),
        ]
        for name, ok in checks:
            self._result(f"P5 · {name}", PASS if ok else FAIL)
        self._result("P5 · Cloud snapshot restore", WARN,
                     "manage-snapshots.sh: 'cloud restore not implemented' (documented)")

    # ── Phase 6: Operations Dashboard ──────────────────────────────────────────

    def _phase_dashboard(self) -> None:
        checks: list[tuple[str, bool]] = [
            ("System status endpoint (/compliance/system-status)", self._has_text(
                "backend/app/routes/compliance.py", "system-status")),
            ("Audit integrity endpoint", self._has_text(
                "backend/app/routes/compliance.py", "audit-integrity")),
            ("JSON metrics endpoint", self._has_text(
                "backend/app/routes/metrics.py", "/metrics")),
            ("Admin audit page (frontend)", self._has_text(
                "frontend-v3/src/pages/admin/AdminPages.tsx", "audit")),
            ("Stats page (frontend)", self._exists("frontend-v3/src/pages/stats/StatsPage.tsx")),
            ("Critical alerts page (frontend)", self._exists(
                "frontend-v3/src/pages/alerts/CriticalAlertsPage.tsx")),
            ("Kernel page (frontend)", self._exists("frontend-v3/src/pages/kernel/KernelPage.tsx")),
            ("Grafana ops dashboards (>=5)", (REPO_ROOT / "config/grafana/dashboards").exists()
             and len(list((REPO_ROOT / "config/grafana/dashboards").glob("gula-*.json"))) >= 5),
        ]
        for name, ok in checks:
            self._result(f"P6 · {name}", PASS if ok else FAIL)
        self._result("P6 · Dedicated frontend metrics dashboard", WARN,
                     "no page consumes /metrics; observability page is an API explorer")

    # ── Phase 7: Security Operations ───────────────────────────────────────────

    def _phase_security_ops(self) -> None:
        checks: list[tuple[str, bool]] = [
            ("Audit service with chain hash", self._has_text(
                "backend/app/services/audit_service.py", "chain_hash", "verify_audit_chain")),
            ("Audit integrity endpoint", self._has_text(
                "backend/app/routes/compliance.py", "audit-integrity")),
            ("Failed-login audit events", self._has_text(
                "backend/app/routes/login.py", "login_failed")),
            ("Permission violation events", self._has_text(
                "backend/app/middleware.py", "SecurityEventMiddleware", "permission_denied")),
            ("Secret scanning pre-commit", self._has_text(
                "scripts/pre-commit-check-secrets.py", "detect_secrets")),
            ("Secret scanning CI", self._exists(".github/workflows/secret-scanning.yml")),
            ("Secrets rotation automation", self._has_text(
                "scripts/rotate-secrets.sh", "rotate", "rolling back")),
            ("Cert renewal + expiry alert", self._has_text(
                "scripts/cert-renew.sh", "get_cert_expiry_days", "ALERT_WEBHOOK_URL")),
            ("Cert check scheduled", self._has_text(
                "scripts/server-setup.sh", "cert-renew")),
            ("SBOM generation", self._exists("scripts/generate-sbom.sh")),
            ("SBOM validation (license policy)", self._exists("scripts/validate-sbom.sh")),
            ("Dependency review CI", self._exists(".github/workflows/dependency-review.yml")),
            ("CodeQL CI", self._exists(".github/workflows/codeql-analysis.yml")),
            ("OpenSSF scorecard CI", self._exists(".github/workflows/scorecard.yml")),
        ]
        for name, ok in checks:
            self._result(f"P7 · {name}", PASS if ok else FAIL)
        self._result("P7 · Encryption key rotation re-encryption", WARN,
                     "rotate-secrets.sh bumps encryption_key_version; re-encryption deferred on read")

    # ── Phase 8: Automation ────────────────────────────────────────────────────

    def _phase_automation(self) -> None:
        workflows = (REPO_ROOT / ".github/workflows").glob("*.yml")
        wf_count = len(list(workflows))
        checks: list[tuple[str, bool]] = [
            ("verify_environment.sh", self._exists("scripts/verify_environment.sh")),
            ("preflight.sh", self._exists("scripts/preflight.sh")),
            ("integration_test.sh", self._exists("scripts/integration_test.sh")),
            ("smoke-bootstrap.sh (post-deploy)", self._exists("scripts/smoke-bootstrap.sh")),
            ("deploy.sh (backup + health wait)", self._has_text("scripts/deploy.sh", "180")),
            ("Rollback CI workflow", self._exists(".github/workflows/rollback.yml")),
            ("Auto-rollback CI workflow", self._exists(".github/workflows/auto-rollback.yml")),
            ("Blue-green deploy CI", self._exists(".github/workflows/blue-green-deploy.yml")),
            ("Release tagging with gates", self._exists("scripts/tag-release.sh")),
            ("CI workflow count >= 20", wf_count >= 20),
            ("Nightly CI (cron)", self._has_text(".github/workflows/nightly.yml", "schedule")),
        ]
        for name, ok in checks:
            self._result(f"P8 · {name}", PASS if ok else FAIL)

    # ── Phase 9: Documentation ─────────────────────────────────────────────────

    def _phase_documentation(self) -> None:
        runbooks = list((REPO_ROOT / "docs/runbooks").glob("*.md")) if (REPO_ROOT / "docs/runbooks").exists() else []
        checks: list[tuple[str, bool]] = [
            ("Operations manual", self._exists("docs/ops/OPERATIONS_MANUAL.md")),
            ("Runbook count >= 7", len(runbooks) >= 7),
            ("PITR runbook", self._exists("docs/dr/PITR_RUNBOOK.md")),
            ("Deployment guide", self._exists("docs/DEPLOYMENT.md")),
            ("Launch runbook", self._exists("docs/LAUNCH_RUNBOOK.md")),
            ("Zero-downtime upgrades doc", self._exists("docs/operations/zero-downtime-upgrades.md")),
            ("Secrets management docs", self._exists("docs/security/SECRET_MANAGEMENT.md")),
            ("Secret rotation plan", self._exists("docs/security/SECRET_ROTATION_PLAN.md")),
        ]
        for name, ok in checks:
            self._result(f"P9 · {name}", PASS if ok else FAIL)

    # ── run / report ───────────────────────────────────────────────────────────

    def run(self) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("=" * 60)
        logger.info("OPERATIONS READINESS CERTIFICATION — PROGRAM-011")
        logger.info("=" * 60)

        self._check("Phase 1", self._phase_observability)
        self._check("Phase 2", self._phase_monitoring)
        self._check("Phase 3", self._phase_diagnostics)
        self._check("Phase 4", self._phase_self_healing)
        self._check("Phase 5", self._phase_backup)
        self._check("Phase 6", self._phase_dashboard)
        self._check("Phase 7", self._phase_security_ops)
        self._check("Phase 8", self._phase_automation)
        self._check("Phase 9", self._phase_documentation)

        per_phase: dict[str, tuple[int, int, int]] = {}
        for phase_name, _ in PHASES:
            prefix = "P" + phase_name.split(".")[0] + " ·"
            phase_results = [r for r in self.results if r["check"].startswith(prefix)]
            p = sum(1 for r in phase_results if r["status"] == PASS)
            w = sum(1 for r in phase_results if r["status"] == WARN)
            f = sum(1 for r in phase_results if r["status"] == FAIL)
            per_phase[phase_name] = (p, w, f)

        passed = sum(1 for r in self.results if r["status"] == PASS)
        warned = sum(1 for r in self.results if r["status"] == WARN)
        failed = sum(1 for r in self.results if r["status"] == FAIL)
        total = passed + warned + failed
        score = round((passed + 0.5 * warned) / total * 100) if total else 0
        level = "PRODUCTION READY" if failed == 0 and score >= 85 else (
            "CONDITIONAL" if failed <= 3 else "NOT READY")

        self._generate_reports(per_phase, score, passed, warned, failed, level)
        elapsed = time.time() - self.start_time
        logger.info(f"COMPLETE — {elapsed:.1f}s — score {score}% — {level}")
        logger.info(f"{passed} PASS / {warned} WARN / {failed} FAIL")

    def _generate_reports(self, per_phase: dict[str, tuple[int, int, int]],
                          score: int, passed: int, warned: int, failed: int, level: str) -> None:
        phase_map: dict[str, str] = {}
        for phase_name, report_file in PHASES:
            phase_map.setdefault(report_file, []).append(phase_name)

        for report_file, phase_names in phase_map.items():
            lines = [f"# {report_file.replace('.md', '').replace('_', ' ').title()}", ""]
            for phase_name in phase_names:
                p, w, f = per_phase[phase_name]
                lines += [f"## {phase_name} — {p} PASS / {w} WARN / {f} FAIL", ""]
                for r in self.results:
                    if not r["check"].startswith(phase_name.split(".")[0] + " ·"):
                        continue
                    lines.append(f"- **{r['status']}** {r['check'].split('·', 1)[1].strip()}")
                    if r["detail"]:
                        lines.append(f"  - {r['detail']}")
                lines.append("")
            (self.output_dir / report_file).write_text("\n".join(lines), encoding="utf-8")

        health = {"score": score, "passed": passed, "warned": warned, "failed": failed,
                  "level": level, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        (self.output_dir / "overall_health.json").write_text(json.dumps(health, indent=2) + "\n", encoding="utf-8")

        lines = [
            "# Operations Readiness Report — PROGRAM-011", "",
            f"**Generated:** {health['generated_at']}",
            f"**Overall Platform Health Score: {score}%** ({passed} PASS / {warned} WARN / {failed} FAIL)",
            f"**Status: {level}**", "",
            "## Phase Summary", "",
            "| Phase | PASS | WARN | FAIL |", "|---|---|---|---|",
        ]
        for phase_name, (p, w, f) in per_phase.items():
            lines.append(f"| {phase_name} | {p} | {w} | {f} |")
        lines += [
            "",
            "## Findings", "",
        ]
        for r in self.results:
            if r["status"] != PASS:
                lines.append(f"- **{r['status']}** {r['check']} — {r['detail'] or 'no detail'}")
        lines += ["", "## Sub-Reports", ""]
        for report_file in sorted({report for _, report in PHASES}):
            lines.append(f"- `{report_file}`")
        lines += ["", "## Baseline / Regression", "",
                  "The Program-012 validation engine (`make validate`) is the regression gate; "
                  "operations certification is evidence-based static evaluation.",
                  "Regressions vs `reports/validation/baseline.json` block commits."]
        (self.output_dir / "OPERATIONS_READINESS_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="PROGRAM-011 operations readiness certification")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()
    cert = OpsCertification(args.output_dir)
    cert.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
