"""Phase 1 — Plugin SDK.

Every AI Engine becomes a plugin. The SDK provides manifest validation,
discovery, registration, lifecycle management, capabilities, dependencies,
configuration, health, permissions, resources, versioning, isolation, hot
reload, sandboxing, certification, and marketplace metadata.

The Plugin Manifest is a superset of the Kernel 16-field engine contract
(inputs, outputs, events, errors, artifacts, ownership, dependencies, health,
progress, checkpoint, capabilities, resources, timeout, retry, version,
status) plus plugin-specific fields: name, description, author, license,
lifecycle, permissions, isolation, and marketplace metadata.

Existing engines in ENGINE_REGISTRY conform to the plugin contract by
construction: `manifest_from_engine()` derives a plugin manifest from any
registered engine without rewriting the registry.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core import KERNEL_CONTRACT_FIELDS, Severity, utcnow

# Paths.
EXT_DIR = Path(__file__).resolve().parent
SDK_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".ai" / "core" / "sdk"

# Plugin lifecycle states (constitution §8.4 knowledge lifecycle + plugin ops).
LIFECYCLE_STATES: tuple[str, ...] = (
    "draft",       # manifest created, not yet registered
    "registered",  # registered in the plugin registry
    "validated",   # passed validation + sandbox checks
    "installed",   # available to engines (but not necessarily active)
    "active",      # loaded and serving
    "disabled",    # installed but inactive
    "deprecated",  # superseded or end-of-life
    "uninstalled", # removed from the registry
)

# Permission categories aligned with the Plugin Constitution.
PERMISSION_CATEGORIES: tuple[str, ...] = (
    "read",
    "write",
    "execute",
    "network",
    "filesystem",
    "database",
    "secrets",
    "deployment",
)

# Isolation levels (strict → permissive).
ISOLATION_LEVELS: tuple[str, ...] = (
    "sandbox",  # fully sandboxed: no write, no network by default
    "restricted",  # sandboxed with explicit grants
    "process",  # isolated per plugin runtime
    "thread",  # isolated per worker
    "embedded",  # runs inline (default for first-party engines)
)

# Required manifest fields (superset of the Kernel contract).
MANIFEST_FIELDS: tuple[str, ...] = (
    *(
        "name",             # unique plugin id
        "version",          # semantic version
        "description",      # one-line summary
        "author",           # owner of the plugin
        "license",          # OSI license id
        "entrypoint",       # module path (scripts.kernel.ext.plugin)
    ),
    *KERNEL_CONTRACT_FIELDS,
)

PLUGIN_EXTRA_FIELDS: tuple[str, ...] = (
    *(
        "name",
        "version",
        "description",
        "author",
        "license",
        "entrypoint",
        "lifecycle",
        "permissions",
        "isolation",
        "marketplace",
    ),
    *KERNEL_CONTRACT_FIELDS,
)

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class PluginError(Exception):
    """Raised when a plugin operation fails."""


@dataclass
class PluginManifest:
    """A validated plugin manifest (superset of the Kernel contract)."""

    name: str
    version: str
    entrypoint: str
    contract: dict[str, Any]
    description: str = ""
    author: str = ""
    license: str = "MIT"
    lifecycle: str = LIFECYCLE_STATES[0]
    permissions: list[str] = field(default_factory=lambda: ["read"])
    isolation: str = ISOLATION_LEVELS[0]
    marketplace: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utcnow)

    @property
    def capabilities(self) -> list[str]:
        return list(self.contract.get("capabilities", []))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "entrypoint": self.entrypoint,
            "lifecycle": self.lifecycle,
            "permissions": list(self.permissions),
            "isolation": self.isolation,
            "marketplace": dict(self.marketplace),
            "dependencies": list(self.dependencies),
            "contract": dict(self.contract),
            "created_at": self.created_at,
        }


@dataclass
class PluginFinding:
    """A validation / certification finding."""

    id: str
    title: str
    severity: Severity
    detail: str = ""


@dataclass
class PluginRecord:
    """A registered plugin with runtime state."""

    manifest: PluginManifest
    health: str = "unknown"
    state: str = "registered"
    loaded_at: str = ""
    last_health_at: str = ""


def validate_version(version: str) -> bool:
    return bool(SEMVER_RE.match(version))


def manifest_from_engine(name: str, meta: dict[str, Any]) -> PluginManifest:
    """Derive a plugin manifest from an engine registry entry.

    Existing engines become plugins without rewriting the registry. The
    resulting manifest is validated against the same rules as any plugin.
    """
    contract = {field: meta.get(field) for field in KERNEL_CONTRACT_FIELDS}
    return PluginManifest(
        name=name,
        version=meta.get("version", "1.0.0"),
        entrypoint=meta.get("entrypoint", f"scripts.kernel.{name}"),
        contract=contract,
        description=meta.get("description", f"{name} engine plugin"),
        author=meta.get("author", "GULA Platform"),
        license=meta.get("license", "Apache-2.0"),
        lifecycle=meta.get("lifecycle", LIFECYCLE_STATES[1]),
        permissions=meta.get("permissions", ["read"]),
        isolation=meta.get("isolation", ISOLATION_LEVELS[4]),
        marketplace=meta.get("marketplace", {"type": "engine"}),
        dependencies=list(meta.get("dependencies", [])),
    )


def validate_manifest(manifest: PluginManifest) -> list[PluginFinding]:
    """Validate a plugin manifest; returns non-empty findings on failure."""
    findings: list[PluginFinding] = []
    if not manifest.name or not manifest.name.strip():
        findings.append(PluginFinding("PLUGIN-NAME", "missing plugin name", Severity.CRITICAL))
    if not validate_version(manifest.version):
        findings.append(PluginFinding(
            "PLUGIN-VERSION", "version must be semantic (X.Y.Z)", Severity.HIGH,
            detail=manifest.version,
        ))
    if not manifest.entrypoint or "." not in manifest.entrypoint:
        findings.append(PluginFinding(
            "PLUGIN-ENTRY", "entrypoint must be a dotted module path", Severity.HIGH,
            detail=manifest.entrypoint,
        ))
    if manifest.isolation not in ISOLATION_LEVELS:
        findings.append(PluginFinding(
            "PLUGIN-ISO", "unknown isolation level", Severity.HIGH,
            detail=manifest.isolation,
        ))
    for perm in manifest.permissions:
        if perm not in PERMISSION_CATEGORIES:
            findings.append(PluginFinding(
                "PLUGIN-PERM", "unknown permission category", Severity.HIGH,
                detail=perm,
            ))
    missing = [f for f in KERNEL_CONTRACT_FIELDS if f not in manifest.contract]
    if missing:
        findings.append(PluginFinding(
            "PLUGIN-CONTRACT", "missing Kernel contract fields", Severity.HIGH,
            detail=", ".join(missing),
        ))
    for dep in manifest.dependencies:
        if not dep or "." not in dep:
            findings.append(PluginFinding(
                "PLUGIN-DEP", "invalid dependency reference", Severity.MEDIUM,
                detail=dep,
            ))
    return findings


def is_valid(manifest: PluginManifest) -> bool:
    return not [f for f in validate_manifest(manifest) if f.severity in {Severity.HIGH, Severity.CRITICAL}]


class PluginRegistry:
    """The canonical plugin registry (Phase 1)."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginRecord] = {}

    def register(self, manifest: PluginManifest) -> PluginRecord:
        findings = validate_manifest(manifest)
        hard = [f for f in findings if f.severity in {Severity.HIGH, Severity.CRITICAL}]
        if hard:
            raise PluginError(f"invalid manifest: {', '.join(f.title for f in hard)}")
        if manifest.name in self._plugins:
            existing = self._plugins[manifest.name].manifest
            if existing.version != manifest.version:
                raise PluginError(
                    f"plugin {manifest.name} already registered at version {existing.version}"
                )
        record = PluginRecord(manifest=manifest)
        self._plugins[manifest.name] = record
        return record

    def get(self, name: str) -> PluginRecord | None:
        return self._plugins.get(name)

    def install(self, name: str) -> PluginRecord:
        record = self._plugins.get(name)
        if record is None:
            raise PluginError(f"plugin '{name}' is not registered")
        record.state = LIFECYCLE_STATES[3]  # installed
        record.loaded_at = utcnow()
        return record

    def activate(self, name: str) -> PluginRecord:
        record = self._plugins.get(name)
        if record is None:
            raise PluginError(f"plugin '{name}' is not registered")
        record.state = LIFECYCLE_STATES[4]  # active
        record.loaded_at = utcnow()
        return record

    def deactivate(self, name: str) -> PluginRecord:
        record = self._plugins.get(name)
        if record is None:
            raise PluginError(f"plugin '{name}' is not registered")
        record.state = LIFECYCLE_STATES[5]  # disabled
        return record

    def uninstall(self, name: str) -> None:
        if name not in self._plugins:
            raise PluginError(f"plugin '{name}' is not registered")
        self._plugins.pop(name)

    def unload(self, name: str) -> PluginRecord:
        """Hot-reload support: unload an active plugin back to installed."""
        record = self._plugins.get(name)
        if record is None:
            raise PluginError(f"plugin '{name}' is not registered")
        record.state = LIFECYCLE_STATES[3]
        record.loaded_at = ""
        return record

    def reload(self, name: str) -> PluginRecord:
        """Hot reload: unload then reactivate a plugin."""
        self.unload(name)
        return self.activate(name)

    def list(self, state: str | None = None) -> list[PluginRecord]:
        records = list(self._plugins.values())
        if state is not None:
            records = [r for r in records if r.state == state]
        return records

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {
            name: {"state": record.state, "health": record.health, "version": record.manifest.version}
            for name, record in sorted(self._plugins.items())
        }


def resolve_dependencies(registry: PluginRegistry, name: str) -> list[str]:
    """Topologically resolve plugin dependencies for a plugin (or raise)."""
    resolved: list[str] = []
    visited: set[str] = set()

    def visit(plugin_name: str) -> None:
        if plugin_name in resolved:
            return
        if plugin_name in visited:
            raise PluginError(f"dependency cycle detected at '{plugin_name}'")
        visited.add(plugin_name)
        record = registry.get(plugin_name)
        if record is None:
            raise PluginError(f"missing dependency '{plugin_name}'")
        for dep in record.manifest.dependencies:
            visit(dep)
        visited.discard(plugin_name)
        resolved.append(plugin_name)

    visit(name)
    return resolved


class PluginSandbox:
    """Plugin sandbox policy (Phase 1)."""

    def __init__(self, permissions: list[str], isolation: str) -> None:
        self.permissions = set(permissions)
        self.isolation = isolation

    def can(self, action: str) -> bool:
        return action in self.permissions

    def deny_list(self) -> list[str]:
        """Actions denied by this sandbox (security posture)."""
        denied = [a for a in PERMISSION_CATEGORIES if a not in self.permissions]
        if self.isolation == "sandbox":
            denied.extend(["network", "database", "secrets", "deployment"])
        return sorted(set(denied))

    def evaluate(self) -> list[PluginFinding]:
        """Return security findings for permissive configurations."""
        findings: list[PluginFinding] = []
        if "secrets" in self.permissions:
            findings.append(PluginFinding(
                "PLUGIN-SECRETS", "plugin requests secrets access", Severity.HIGH,
                "secrets access must be reviewed per plugin",
            ))
        if "deployment" in self.permissions:
            findings.append(PluginFinding(
                "PLUGIN-DEPLOY", "plugin requests deployment permission", Severity.HIGH,
                "deployment permission must be Reviewer-approved",
            ))
        if self.isolation == "embedded" and {"network", "database", "secrets"} & self.permissions:
            findings.append(PluginFinding(
                "PLUGIN-ISO-PERM", "embedded isolation with privileged permissions", Severity.MEDIUM,
                "privileged plugins should use process isolation",
            ))
        return findings


def certify(manifest: PluginManifest) -> list[PluginFinding]:
    """Certify a plugin; returns findings (empty list = certified)."""
    findings = list(validate_manifest(manifest))
    sandbox = PluginSandbox(manifest.permissions, manifest.isolation)
    findings.extend(sandbox.evaluate())
    if manifest.license not in {"MIT", "Apache-2.0", "BSD-3-Clause", "MPL-2.0"}:
        findings.append(PluginFinding(
            "PLUGIN-LICENSE", "license not on approved list", Severity.MEDIUM,
            detail=manifest.license,
        ))
    return findings


def discover(directory: Path, registry: PluginRegistry | None = None) -> list[PluginManifest]:
    """Discover plugin manifests in a directory (manifest.json or *.plugin.json)."""
    if not directory.exists():
        return []
    registry = registry or PluginRegistry()
    discovered: list[PluginManifest] = []
    for candidate in sorted(directory.glob("**/plugin.json")) + sorted(directory.glob("**/*.plugin.json")):
        try:
            data = __import__("json").loads(candidate.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        try:
            manifest = PluginManifest(
                name=data["name"],
                version=data["version"],
                entrypoint=data.get("entrypoint", ""),
                description=data.get("description", ""),
                author=data.get("author", ""),
                license=data.get("license", "MIT"),
                lifecycle=data.get("lifecycle", LIFECYCLE_STATES[1]),
                permissions=data.get("permissions", ["read"]),
                isolation=data.get("isolation", ISOLATION_LEVELS[0]),
                marketplace=data.get("marketplace", {}),
                contract=data.get("contract", {}),
                dependencies=data.get("dependencies", []),
            )
        except KeyError:
            continue
        discovered.append(manifest)
    return discovered


def render_plugin_markdown(registry: PluginRegistry | None = None) -> str:
    """Render the plugin registry section for the extension report."""
    registry = registry or PluginRegistry()
    lines = [
        "# PLUGIN REGISTRY",
        "",
        "> Mission: GULA-KERNEL-EXT-001 — Phase 1: Plugin SDK",
        "> Generated by: `scripts/kernel/ext/plugin.py`",
        "",
        "## Registered Plugins",
        "",
        "| Plugin | Version | State | Health | Isolation | Permissions |",
        "|---|---|---|---|---|---|",
    ]
    for name, record in sorted(registry.snapshot().items()):
        m = registry.get(name).manifest
        lines.append(
            f"| {name} | {record['version']} | {record['state']} | {record['health']} | "
            f"{m.isolation} | {', '.join(m.permissions)} |"
        )
    lines += ["", ""]
    return "\n".join(lines) + "\n"


__all__ = [
    "ISOLATION_LEVELS",
    "LIFECYCLE_STATES",
    "MANIFEST_FIELDS",
    "PERMISSION_CATEGORIES",
    "PluginError",
    "PluginFinding",
    "PluginManifest",
    "PluginRecord",
    "PluginRegistry",
    "PluginSandbox",
    "certify",
    "discover",
    "is_valid",
    "manifest_from_engine",
    "render_plugin_markdown",
    "resolve_dependencies",
    "validate_manifest",
    "validate_version",
]
