"""Phase 3 — Dependency Governance.

Analyze the backend's package-level dependency graph using AST import
parsing. Detect circular dependencies, skip-layer violations (routes
reaching into models directly), and cross-context coupling. Findings are
deterministic and persist under state/dependencies/.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from functools import cache
from pathlib import Path

from scripts.architect.core import (
    DEPENDENCY_DIR,
    DependencyEdge,
    DependencyFinding,
    make_id,
    write_json,
)
from scripts.kernel.core import REPO_ROOT, utcnow

# Layer order for skip-layer detection (routes -> services -> models/domain).
LAYER_RANK: dict[str, int] = {
    "routes": 0,
    "services": 1,
    "models": 2,
    "domain": 2,
    "core": 2,
    "security": 1,
    "tasks": 1,
}

# Vendor SDKs that signal technology lock-in when declared as dependencies.
# The constitution mandates Free/Open-Source/Self-Hosted-first, so any
# presence of these is reported as drift to be justified or replaced.
VENDOR_SDKS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("aws", ("boto3", "aws-sdk", "aws_cdk")),
    ("azure", ("azure-storage", "azure-identity", "azure.cosmos")),
    ("google-cloud", ("google-cloud", "google-cloud-storage")),
    ("twilio", ("twilio",)),
    ("sendgrid", ("sendgrid",)),
    ("firebase", ("firebase",)),
    ("algolia", ("algoliasearch",)),
)

BACKEND_APP = "backend" / Path("app")


def _package_of(path: Path) -> str:
    """Return the top-level package name of a backend module path."""
    parts = path.parts
    try:
        index = parts.index("app")
    except ValueError:
        return ""
    return parts[index + 1] if index + 1 < len(parts) else ""


@cache
def module_imports(root: Path) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Map module file -> top-level packages it imports (cached, immutable)."""
    app_dir = root / "backend" / "app"
    imports: dict[str, set[str]] = {}
    if not app_dir.exists():
        return ()
    for path in sorted(app_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        package = _package_of(path)
        if not package:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        targets: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                parts = node.module.split(".")
                if len(parts) >= 2 and parts[0] == "app":
                    targets.add(parts[1])
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    parts = alias.name.split(".")
                    if len(parts) >= 2 and parts[0] == "app":
                        targets.add(parts[1])
        imports[path.relative_to(root).as_posix()] = targets
    return tuple(sorted((module, tuple(sorted(targets)))
                        for module, targets in imports.items()))


def build_edges(root: Path | None = None) -> list[DependencyEdge]:
    """Build package-level dependency edges from backend imports."""
    root = root or REPO_ROOT
    imports = dict(module_imports(root))
    edges: list[DependencyEdge] = []
    for module, targets in sorted(imports.items()):
        source = _package_of(Path(module))
        if not source:
            continue
        for target in sorted(targets):
            if target == source:
                continue
            edges.append(DependencyEdge(
                source=source,
                target=target,
                kind="calls",
                evidence=f"{module} -> app.{target}",
            ))
    return edges


def _adjacency(edges: list[DependencyEdge]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        graph[edge.source].add(edge.target)
    return graph


def _find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Return canonical directed cycles present (deterministic, deduplicated)."""
    cycles: dict[tuple[str, ...], bool] = {}
    nodes = sorted(graph)
    for start in nodes:
        path: list[str] = []
        visited: set[str] = set()

        def dfs(
            node: str,
            path: list[str] = path,
            visited: set[str] = visited,
        ) -> None:
            if node in path:
                raw = [*path[path.index(node):], node]
                unique = raw[:-1]
                start = unique.index(min(unique))
                key = (*unique[start:], *unique[:start])
                cycles.setdefault(key, True)
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for neighbor in sorted(graph.get(node, ())):
                dfs(neighbor)
            path.pop()

        dfs(start)
    return [list(cycle) for cycle in sorted(cycles)]


def _find_skip_layer(edges: list[DependencyEdge]) -> list[DependencyFinding]:
    """Detect routes reaching models/domain directly (bypassing services)."""
    findings: list[DependencyFinding] = []
    for edge in sorted(edges, key=lambda e: (e.source, e.target)):
        source_rank = LAYER_RANK.get(edge.source)
        target_rank = LAYER_RANK.get(edge.target)
        if (
            source_rank is not None
            and target_rank is not None
            and target_rank - source_rank >= 2
        ):
            findings.append(DependencyFinding(
                    finding_id=make_id("DEP"),
                    kind="skip-layer",
                    source=edge.source,
                    target=edge.target,
                    severity="medium",
                    evidence=edge.evidence,
                    recommendation=(
                        f"Route layer ({edge.source}) must call services, not "
                        f"reach {edge.target} directly."
                    ),
                ))
    return findings


def _find_cross_context(edges: list[DependencyEdge]) -> list[DependencyFinding]:
    """Detect service-to-service coupling outside the event bus."""
    findings: list[DependencyFinding] = []
    for edge in sorted(edges, key=lambda e: (e.source, e.target)):
        if edge.source == "services" and edge.target == "services":
            findings.append(DependencyFinding(
                finding_id=make_id("DEP"),
                kind="cross-context",
                source=edge.source,
                target=edge.target,
                severity="low",
                evidence=edge.evidence,
                recommendation="Prefer domain events over direct service imports.",
            ))
    return findings


def _find_technology_lockin(root: Path) -> list[DependencyFinding]:
    """Detect vendor-SDK dependencies that violate self-hosted-first policy."""
    findings: list[DependencyFinding] = []
    manifests = [
        root / "backend" / "requirements.txt",
        root / "backend" / "requirements-base.txt",
        root / "backend" / "pyproject.toml",
        root / "frontend-v3" / "package.json",
    ]
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in manifests
        if path.exists()
    ).lower()
    for vendor, sdk_names in VENDOR_SDKS:
        hits = [name for name in sdk_names if name in text]
        if hits:
            findings.append(DependencyFinding(
                finding_id=make_id("DEP"),
                kind="technology-lock-in",
                source="dependency-manifests",
                target=vendor,
                severity="low",
                evidence=f"{vendor} SDK(s) declared: {', '.join(sorted(hits))}",
                recommendation=(
                    f"Replace the {vendor} dependency with a self-hosted or "
                    "vendor-neutral alternative, or document an approved "
                    "exception with cost analysis."
                ),
            ))
    return findings


def detect_dependencies(root: Path | None = None) -> list[DependencyFinding]:
    """Run the full dependency-governance scan deterministically."""
    root = root or REPO_ROOT
    edges = build_edges(root)
    graph = _adjacency(edges)
    findings: list[DependencyFinding] = []
    for cycle in _find_cycles(graph):
        findings.append(DependencyFinding(
            finding_id=make_id("DEP"),
            kind="circular",
            source=cycle[0],
            target=cycle[-2] if len(cycle) > 2 else cycle[0],
            severity="high" if len(cycle) > 2 else "medium",
            evidence=" -> ".join(cycle),
            recommendation=(
                "Break the dependency cycle by extracting a shared module "
                "or introducing domain events."
            ),
        ))
    findings.extend(_find_skip_layer(edges))
    findings.extend(_find_cross_context(edges))
    findings.extend(_find_technology_lockin(root))
    return sorted(findings, key=lambda f: (f.kind, f.source, f.target))


def persist_dependencies(root: Path | None = None) -> Path:
    """Persist dependency findings and the edge graph."""
    root = root or REPO_ROOT
    edges = build_edges(root)
    findings = detect_dependencies(root)
    path = DEPENDENCY_DIR / "findings.json"
    write_json(path, {
        "discovered_at": utcnow(),
        "edges": [e.to_dict() for e in edges],
        "findings": [f.to_dict() for f in findings],
    })
    return path


def render_markdown(findings: list[DependencyFinding]) -> str:
    lines = [
        "# GULA-ARCHITECT-001 — Dependency Governance",
        "",
        f"Generated: **{utcnow()}**",
        "",
        f"**{len(findings)} dependency findings**.",
        "",
        "| Kind | Severity | Cycle / Edge |",
        "|---|---|---|",
    ]
    for finding in findings:
        edge = (
            finding.evidence
            if finding.kind == "circular"
            else f"{finding.source} -> {finding.target}"
        )
        lines.append(
            f"| {finding.kind} | {finding.severity} | `{edge}` |"
        )
    lines.append("")
    if findings:
        lines.append("## Recommendations")
        lines.append("")
        for finding in findings[:10]:
            lines.append(f"- `{finding.finding_id}` {finding.recommendation}")
    else:
        lines.append("**No dependency-governance findings. The backend layer "
                     "discipline is clean.**")
    lines.append("")
    return "\n".join(lines)
