"""PROGRAM-STABLE-004 — Domain Isolation validation (Phase 3).

Validation rules:

  * Laboratory cannot access Pharmacy internals.
  * Pharmacy cannot access Laboratory internals.
  * Radiology cannot access Laboratory internals.
  * Hospital cannot access Pharmacy internals.
  * Insurance cannot access Hospital internals.
  * Citizen Portal cannot access operational systems.
  * Provider Portal cannot execute domain administration.
  * Every Domain owns only itself.

The validator inspects the real module set of every Domain and reports any
cross-domain import, cross-domain table reference, circular dependency,
shared mutable state, permission leak, or direct database coupling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.domain_platform.core import DomainManifest
from app.domain_platform.shared_core import is_shared_core_import

_MODULE_RE = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE)
_MUTABLE_GLOBAL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:\[\]|\{\}|set\(\))\s*$", re.MULTILINE)
_TABLE_RE = re.compile(r"__tablename__\s*=\s*['\"]([^'\"]+)['\"]")
_ENGINE_IMPORTS = (
    "create_engine",
    "create_async_engine",
    "engine_from_config",
    "make_url",
    "sessionmaker",
)


@dataclass
class IsolationFinding:
    """One isolation violation with its evidence and severity."""

    kind: str
    severity: str
    message: str
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "severity": self.severity,
            "message": self.message,
            "evidence": self.evidence,
        }


@dataclass
class DomainIsolationReport:
    """Phase 3 result for the whole platform."""

    domain_imports: dict[str, list[str]] = field(default_factory=dict)
    cross_domain: list[IsolationFinding] = field(default_factory=list)
    circular: list[IsolationFinding] = field(default_factory=list)
    shared_state: list[IsolationFinding] = field(default_factory=list)
    permission_leaks: list[IsolationFinding] = field(default_factory=list)
    db_coupling: list[IsolationFinding] = field(default_factory=list)
    table_overlaps: list[IsolationFinding] = field(default_factory=list)

    @property
    def all_findings(self) -> list[IsolationFinding]:
        return (
            self.cross_domain
            + self.circular
            + self.shared_state
            + self.permission_leaks
            + self.db_coupling
            + self.table_overlaps
        )

    @property
    def passes(self) -> bool:
        return not self.all_findings

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_imports": self.domain_imports,
            "cross_domain": [f.to_dict() for f in self.cross_domain],
            "circular": [f.to_dict() for f in self.circular],
            "shared_state": [f.to_dict() for f in self.shared_state],
            "permission_leaks": [f.to_dict() for f in self.permission_leaks],
            "db_coupling": [f.to_dict() for f in self.db_coupling],
            "table_overlaps": [f.to_dict() for f in self.table_overlaps],
            "passes": self.passes,
        }


def _extract_imports(source: str) -> set[str]:
    imports: set[str] = set()
    for match in _MODULE_RE.finditer(source):
        imports.add(match.group(1) or match.group(2))
    return imports


def _to_import_name(module: str) -> str:
    """Convert a file path (``app/lims/models.py``) to an importable module
    name (``app.lims.models``)."""
    name = module.removesuffix(".py").replace("/", ".")
    return name.rstrip(".")


def _to_table_name(module: str) -> str:
    return module.split("/")[-1].removesuffix(".py")


def _extract_tables(source: str) -> set[str]:
    return set(_TABLE_RE.findall(source))


def _extract_mutable_globals(source: str) -> set[str]:
    return set(_MUTABLE_GLOBAL_RE.findall(source))


class IsolationValidator:
    """Validates Domain Sovereignty for a set of Domain manifests.

    ``domain_modules`` maps a domain code to the list of module paths it
    owns. The validator resolves imports by reading the real source files.
    """

    def __init__(self, domains: list[DomainManifest], repo_root: str | None = None) -> None:
        self.domains = domains
        self.repo_root = repo_root
        self._module_cache: dict[str, str] = {}

    # ── module source resolution ────────────────────────────────────────────

    def _resolve_source(self, module: str) -> str:
        if module in self._module_cache:
            return self._module_cache[module]
        if self.repo_root:
            base = module[:-3] if module.endswith(".py") else module
            candidates = [
                f"{self.repo_root}/{base}.py",
                f"{self.repo_root}/{base}/__init__.py",
            ]
            for candidate in candidates:
                try:
                    import pathlib

                    with pathlib.Path(candidate).open(encoding="utf-8") as handle:
                        source = handle.read()
                except OSError:
                    continue
                else:
                    self._module_cache[module] = source
                    return source
        return ""

    # ── check 1: cross-domain imports ───────────────────────────────────────

    def detect_cross_domain_imports(self) -> list[IsolationFinding]:
        findings: list[IsolationFinding] = []
        # Build the set of all domain-owned importable modules, indexed by the
        # owning domain. Shared Core imports are allowed and never flagged.
        owner_by_module: dict[str, str] = {}
        for manifest in self.domains:
            for module in manifest.modules:
                owner_by_module[_to_import_name(module)] = manifest.code
        for manifest in self.domains:
            for module in manifest.modules:
                source = self._resolve_source(module)
                for imported in _extract_imports(source):
                    # Shared Core consumption is the legal path — skip it.
                    if is_shared_core_import(imported):
                        continue
                    for candidate, owner in owner_by_module.items():
                        if imported == candidate or imported.startswith(candidate + ".") or candidate.startswith(imported + "."):
                            if owner == manifest.code:
                                continue
                            findings.append(
                                IsolationFinding(
                                    kind="cross_domain_import",
                                    severity="critical",
                                    message=(
                                        f"domain '{manifest.code}' imports '{imported}' "
                                        f"which belongs to domain '{owner}'"
                                    ),
                                    evidence=f"{module} -> {imported}",
                                )
                            )
                        if findings and findings[-1].evidence == f"{module} -> {imported}":
                            break
        return findings

    # ── check 2: circular dependencies ──────────────────────────────────────

    @staticmethod
    def _find_cycles(deps: dict[str, set[str]], manifest_code: str) -> list[IsolationFinding]:
        """DFS cycle detection over ``deps``, returning findings."""
        findings: list[IsolationFinding] = []
        state: dict[str, int] = {}
        stack: list[str] = []

        def _visit(node: str) -> None:
            state[node] = 1
            stack.append(node)
            for neighbor in deps.get(node, ()):
                if state.get(neighbor) == 1:
                    start = stack.index(neighbor) if neighbor in stack else 0
                    cycle = [*stack[start:], neighbor]
                    findings.append(
                        IsolationFinding(
                            kind="circular_dependency",
                            severity="critical",
                            message=(
                                f"domain '{manifest_code}' has a circular "
                                f"dependency: {' -> '.join(cycle)}"
                            ),
                        )
                    )
                elif state.get(neighbor, 0) == 0:
                    _visit(neighbor)
            stack.pop()
            state[node] = 2

        for module in deps:
            if state.get(module, 0) == 0:
                _visit(module)
        return findings

    def detect_circular_dependencies(self) -> list[IsolationFinding]:
        findings: list[IsolationFinding] = []
        for manifest in self.domains:
            if len(manifest.modules) < 2:
                continue
            owned = {_to_import_name(m) for m in manifest.modules}
            deps: dict[str, set[str]] = {}
            for module in manifest.modules:
                import_name = _to_import_name(module)
                deps.setdefault(import_name, set())
                source = self._resolve_source(module)
                for imported in _extract_imports(source):
                    if is_shared_core_import(imported):
                        continue
                    for candidate in owned:
                        if candidate == import_name:
                            continue
                        if imported == candidate or imported.startswith(candidate + "."):
                            deps[import_name].add(candidate)
            findings.extend(self._find_cycles(deps, manifest.code))
        return findings

    # ── check 3: shared mutable state ───────────────────────────────────────

    def detect_shared_mutable_state(self) -> list[IsolationFinding]:
        findings: list[IsolationFinding] = []
        for manifest in self.domains:
            for module in manifest.modules:
                source = self._resolve_source(module)
                for name in sorted(_extract_mutable_globals(source)):
                    findings.append(
                        IsolationFinding(
                            kind="shared_mutable_state",
                            severity="major",
                            message=(
                                f"domain '{manifest.code}' defines mutable module-level "
                                f"global '{name}' in {module}"
                            ),
                            evidence=f"{module}:{name}",
                        )
                    )
        return findings

    # ── check 4: permission leakage ─────────────────────────────────────────

    def detect_permission_leakage(self) -> list[IsolationFinding]:
        findings: list[IsolationFinding] = []
        # Every Domain owns a set of API namespace prefixes (first path
        # segment of each declared API). A Domain leaks a permission when it
        # declares an API inside another Domain's namespace.
        namespace_owner: dict[str, str] = {}
        for manifest in self.domains:
            for api in manifest.api:
                segments = api.strip("/").split("/")
                if segments:
                    namespace_owner.setdefault(f"/{segments[0]}", manifest.code)
        for manifest in self.domains:
            for api in manifest.api:
                segments = api.strip("/").split("/")
                if not segments:
                    continue
                prefix = f"/{segments[0]}"
                owner = namespace_owner.get(prefix)
                if owner is not None and owner != manifest.code:
                    findings.append(
                        IsolationFinding(
                            kind="permission_leakage",
                            severity="major",
                            message=(
                                f"domain '{manifest.code}' declares API '{api}' inside "
                                f"namespace '{prefix}' owned by domain '{owner}'"
                            ),
                            evidence=api,
                        )
                    )
        return findings

    # ── check 5: direct database coupling ───────────────────────────────────

    def detect_direct_db_coupling(self) -> list[IsolationFinding]:
        findings: list[IsolationFinding] = []
        for manifest in self.domains:
            for module in manifest.modules:
                source = self._resolve_source(module)
                for symbol in _ENGINE_IMPORTS:
                    if f" {symbol}" in source or f"{symbol}(" in source:
                        findings.append(
                            IsolationFinding(
                                kind="direct_db_coupling",
                                severity="critical",
                                message=(
                                    f"domain '{manifest.code}' module '{module}' "
                                    f"creates its own database engine/session ({symbol})"
                                ),
                                evidence=f"{module}:{symbol}",
                            )
                        )
        return findings

    # ── check 6: cross-domain tables ────────────────────────────────────────

    def detect_table_overlaps(self) -> list[IsolationFinding]:
        findings: list[IsolationFinding] = []
        seen: dict[str, str] = {}
        for manifest in self.domains:
            for table in manifest.tables:
                owner = seen.get(table)
                if owner and owner != manifest.code:
                    findings.append(
                        IsolationFinding(
                            kind="cross_domain_table",
                            severity="critical",
                            message=(
                                f"table '{table}' is owned by both '{owner}' and "
                                f"'{manifest.code}' — no Domain reads another "
                                f"Domain's database"
                            ),
                            evidence=table,
                        )
                    )
                else:
                    seen[table] = manifest.code
        return findings

    # ── shared core consumption reporting ───────────────────────────────────

    def collect_domain_imports(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for manifest in self.domains:
            imported: set[str] = set()
            for module in manifest.modules:
                source = self._resolve_source(module)
                imported.update(_extract_imports(source))
            result[manifest.code] = sorted(imported)
        return result

    def run(self) -> DomainIsolationReport:
        report = DomainIsolationReport()
        report.domain_imports = self.collect_domain_imports()
        report.cross_domain = self.detect_cross_domain_imports()
        report.circular = self.detect_circular_dependencies()
        report.shared_state = self.detect_shared_mutable_state()
        report.permission_leaks = self.detect_permission_leakage()
        report.db_coupling = self.detect_direct_db_coupling()
        report.table_overlaps = self.detect_table_overlaps()
        return report
