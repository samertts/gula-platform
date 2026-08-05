"""Phase 0 — Deployment Audit.

Audit the full deployment surface: Docker, Docker Compose, Traefik,
Cloudflare, Vercel, Hetzner, Terraform, Kubernetes, Helm, GitHub Actions,
environment variables, secrets, certificates, DNS, storage, backups, and
monitoring. Generate DEPLOYER_AUDIT_REPORT.md at the repository root.
Deterministic; detects what actually exists.
"""

from __future__ import annotations

from pathlib import Path

from scripts.deployer.core import (
    AUDIT_COMPONENTS,
    AUDIT_PATH,
    InfrastructureItem,
)
from scripts.kernel.core import REPO_ROOT

# Category -> candidate files/patterns that prove the component exists.
AUDIT_PATTERNS: dict[str, tuple[str, ...]] = {
    "docker": ("backend/Dockerfile", "frontend-v3/Dockerfile", "Dockerfile"),
    "docker-compose": ("docker-compose.yml", "docker-compose.full.yml", "docker-compose.scale.yml"),
    "traefik": ("config/traefik", "traefik.yml", "traefik.yaml"),
    "cloudflare": ("config/cloudflare", "cloudflare.toml", "wrangler.toml"),
    "vercel": ("vercel.json", "config/vercel"),
    "hetzner": ("config/hetzner", "terraform/hetzner", "hetzner"),
    "terraform": ("terraform", "*.tf"),
    "kubernetes": ("kubernetes", "k8s", "deploy/kubernetes", "manifests"),
    "helm": ("helm", "charts", "Chart.yaml"),
    "github-actions": (".github/workflows",),
    "environment-variables": (".env.example", ".env.sample", "config/env"),
    "secrets": ("config/vault", ".vault", "secrets"),
    "certificates": ("config/ssl", "config/cert-manager", "certs"),
    "dns": ("config/dns", "dns", "config/cloudflare"),
    "storage": ("config/minio-ha", "config/backup", "config/postgres"),
    "backups": ("config/backup", "config/dr", "backup"),
    "monitoring": ("config/prometheus", "config/grafana", "config/alertmanager"),
}


def _expand(pattern: str) -> list[Path]:
    if any(ch in pattern for ch in "*?["):
        return sorted(Path(REPO_ROOT).glob(pattern))
    path = Path(REPO_ROOT) / pattern
    return [path] if path.exists() else []


def audit_systems() -> list[InfrastructureItem]:
    """Collect evidence for every deployment component."""
    items: list[InfrastructureItem] = []
    for name in AUDIT_COMPONENTS:
        patterns = AUDIT_PATTERNS.get(name, ())
        evidence: list[str] = []
        for pattern in patterns:
            for path in _expand(pattern):
                rel = path.relative_to(REPO_ROOT).as_posix()
                if rel not in evidence:
                    evidence.append(rel)
        items.append(InfrastructureItem(
            name=name,
            category="deployment",
            present=bool(evidence),
            evidence=evidence,
            notes="configured" if evidence else "NOT FOUND",
        ))
    return items


def render_markdown(items: list[InfrastructureItem]) -> str:
    lines = [
        "# DEPLOYER_AUDIT_REPORT.md",
        "",
        "Audit of the deployment surface for GULA-DEPLOYER-001.",
        "",
        "| Component | Status | Notes | Evidence |",
        "|---|---|---|---|",
    ]
    for item in items:
        state = "present" if item.present else "absent"
        evidence = ", ".join(item.evidence[:5]) or "—"
        lines.append(f"| {item.name} | {state} | {item.notes} | `{evidence}` |")
    lines.append("")
    present = sum(1 for i in items if i.present)
    lines.append("## Verdict")
    lines.append("")
    lines.append(
        f"**AUDIT COMPLETE** — {present}/{len(items)} deployment components "
        "present. Absent components are flagged for the Deployment "
        "Architecture and Infrastructure phases. Only components with "
        "evidence are assumed present; everything else is treated as a gap."
    )
    lines.append("")
    return "\n".join(lines)


def run_audit() -> Path:
    """Run the audit and write DEPLOYER_AUDIT_REPORT.md."""
    items = audit_systems()
    AUDIT_PATH.write_text(render_markdown(items), encoding="utf-8")
    return AUDIT_PATH
