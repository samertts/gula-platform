#!/usr/bin/env python3
"""PROGRAM-AUTOMATION-001: Periodic Health Reports

Generates:
- Daily Health Report
- Weekly Governance Report
- Monthly Knowledge Report
- Monthly Technical Debt Report
- Enterprise Readiness Trend

Usage:
    python scripts/health_reports.py                  # Generate daily report
    python scripts/health_reports.py --period daily
    python scripts/health_reports.py --period weekly
    python scripts/health_reports.py --period monthly
    python scripts/health_reports.py --all
"""
import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CORE = REPO_ROOT / ".ai" / "core"
REPORTS_DIR = REPO_ROOT / "reports" / "health"
SCRIPTS = REPO_ROOT / "scripts"

def ensure_dirs():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def run_validator(script):
    try:
        r = subprocess.run(["python3", str(SCRIPTS / script)], capture_output=True, text=True, timeout=120, cwd=REPO_ROOT)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)

def get_git_stats():
    try:
        commits = subprocess.run(["git", "log", "--oneline", "-10"], capture_output=True, text=True, cwd=REPO_ROOT, timeout=10)
        return len(commits.stdout.strip().split("\n"))
    except: return 0

def collect_metrics():
    """Collect system metrics."""
    metrics = {"timestamp": datetime.now().isoformat()}

    # Health doctor
    rc, out, err = run_validator("gula_ai_doctor.py")
    try:
        if "--json" in out or True:
            pass
    except: pass
    # Parse health from stdout
    for line in out.split("\n"):
        if "Health Score" in line:
            m = re.search(r"([\d.]+)", line)
            if m: metrics["health_score"] = float(m.group(1))
        if "Checks:" in line:
            m = re.search(r"PASS: (\d+) \| WARN: (\d+) \| FAIL: (\d+)", line)
            if m:
                metrics["pass"] = int(m.group(1))
                metrics["warn"] = int(m.group(2))
                metrics["fail"] = int(m.group(3))

    # Registry
    reg = AI_CORE / "registry" / "REGISTRY.md"
    if reg.exists():
        content = reg.read_text("utf-8")
        t = re.search(r"\*\*Total Artifacts\*\*.*?\|\s*(\d+)", content)
        if t: metrics["artifacts"] = int(t.group(1))

    # Debt
    debt = AI_CORE / "quality" / "TECHNICAL_DEBT.md"
    if debt.exists():
        content = debt.read_text("utf-8")
        metrics["open_debt"] = content.count("| Open |")

    # Git activity
    metrics["recent_commits"] = get_git_stats()

    return metrics

def generate_daily():
    m = collect_metrics()
    out = []
    out.append("# Daily Health Report")
    out.append("")
    out.append(f"**Date:** {datetime.now().isoformat()}")
    out.append("**Type:** Daily")
    out.append("")
    out.append("## Health Metrics")
    out.append("")
    out.append(f"- Health Score: {m.get('health_score', 'N/A')}")
    out.append(f"- Checks: PASS {m.get('pass', 0)} / WARN {m.get('warn', 0)} / FAIL {m.get('fail', 0)}")
    out.append(f"- Artifacts: {m.get('artifacts', 0)}")
    out.append(f"- Open Debt: {m.get('open_debt', 0)}")
    out.append(f"- Recent Commits: {m.get('recent_commits', 0)}")
    out.append("")
    f = REPORTS_DIR / f"daily_{datetime.now().strftime('%Y%m%d')}.md"
    f.write_text("\n".join(out), encoding="utf-8")
    return f

def generate_weekly():
    m = collect_metrics()
    out = []
    out.append("# Weekly Governance Report")
    out.append("")
    out.append(f"**Week ending:** {datetime.now().isoformat()}")
    out.append("**Type:** Weekly")
    out.append("")
    out.append("## Governance Summary")
    out.append("")
    out.append(f"- Constitution status: {'PASS' if m.get('health_score', 0) >= 90 else 'REVIEW'}")
    out.append(f"- Health Score: {m.get('health_score', 'N/A')}")
    out.append(f"- Open Debt Items: {m.get('open_debt', 0)}")
    out.append(f"- Commits this week: {m.get('recent_commits', 0)}")
    out.append("")
    f = REPORTS_DIR / f"weekly_{datetime.now().strftime('%Y%m%d')}.md"
    f.write_text("\n".join(out), encoding="utf-8")
    return f

def generate_monthly():
    m = collect_metrics()
    out = []
    out.append("# Monthly Knowledge Report")
    out.append("")
    out.append(f"**Month:** {datetime.now().strftime('%Y-%m')}")
    out.append("")
    out.append("## Knowledge System Summary")
    out.append("")
    out.append(f"- Total Artifacts: {m.get('artifacts', 0)}")
    out.append(f"- Health Score: {m.get('health_score', 'N/A')}")
    out.append(f"- Open Debt: {m.get('open_debt', 0)}")
    out.append("")
    out.append("## Enterprise Readiness Trend")
    out.append("")
    out.append("| Date | Health Score | Artifacts | Open Debt |")
    out.append("|---|---|---|---|")
    out.append(f"| {datetime.now().strftime('%Y-%m-%d')} | {m.get('health_score', 'N/A')} | {m.get('artifacts', 0)} | {m.get('open_debt', 0)} |")
    out.append("")
    f = REPORTS_DIR / f"monthly_{datetime.now().strftime('%Y%m')}.md"
    f.write_text("\n".join(out), encoding="utf-8")
    return f

def main():
    parser = argparse.ArgumentParser(description="Periodic Health Reports")
    parser.add_argument("--period", choices=["daily", "weekly", "monthly"], default="daily")
    parser.add_argument("--all", action="store_true", help="Generate all reports")
    args = parser.parse_args()

    ensure_dirs()

    if args.all:
        for period in ["daily", "weekly", "monthly"]:
            if period == "daily": f = generate_daily()
            elif period == "weekly": f = generate_weekly()
            else: f = generate_monthly()
            print(f"[OK] {period}: {f}")
    else:
        if args.period == "daily": f = generate_daily()
        elif args.period == "weekly": f = generate_weekly()
        else: f = generate_monthly()
        print(f"[OK] {args.period}: {f}")

if __name__ == "__main__":
    main()
