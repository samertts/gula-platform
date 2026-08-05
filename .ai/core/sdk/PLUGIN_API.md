---
id: SDK-000002
type: sdk
title: "Plugin SDK — API Reference"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [sdk, plugin, api, gula-kernel-ext-001]
---

# Plugin SDK API Reference

> Mission: GULA-KERNEL-EXT-001 — Phase 1
> Module: `scripts/kernel/ext/plugin.py`

## Constants

| Constant | Value |
|---|---|
| `LIFECYCLE_STATES` | `draft, registered, validated, installed, active, disabled, deprecated, uninstalled` |
| `PERMISSION_CATEGORIES` | `read, write, execute, network, filesystem, database, secrets, deployment` |
| `ISOLATION_LEVELS` | `sandbox, restricted, process, thread, embedded` |
| `MANIFEST_FIELDS` | Plugin fields + 16 Kernel contract fields |

## Data Types

### `PluginManifest`

A validated plugin manifest. Key attributes: `name`, `version`, `description`,
`author`, `license`, `entrypoint`, `lifecycle`, `permissions`, `isolation`,
`marketplace`, `dependencies`, `contract`, `capabilities` (property).
Methods: `to_dict()`.

### `PluginRecord`

Runtime state of a registered plugin: `manifest`, `health`, `state`,
`loaded_at`, `last_health_at`.

### `PluginFinding`

`id`, `title`, `severity` (`Severity`), `detail`.

### `PluginError(Exception)`

Raised for invalid manifests, duplicate versions, missing plugins,
missing/cyclic dependencies.

## Functions

### `validate_version(version: str) -> bool`
Semver check.

### `manifest_from_engine(name: str, meta: dict) -> PluginManifest`
Derive a plugin manifest from an `ENGINE_REGISTRY` entry.

### `validate_manifest(manifest) -> list[PluginFinding]`
Validation findings (empty = valid).

### `is_valid(manifest) -> bool`
True when no HIGH/CRITICAL findings.

### `certify(manifest) -> list[PluginFinding]`
Manifest validation + sandbox evaluation + license policy. Empty = certified.

### `discover(directory: Path) -> list[PluginManifest]`
Find `plugin.json` / `*.plugin.json` manifests under a directory.

### `resolve_dependencies(registry, name) -> list[str]`
Topological dependency order (leaf-first). Raises `PluginError` on missing
dep or cycle.

## Class: `PluginRegistry`

| Method | Behavior |
|---|---|
| `register(manifest)` | Validate + register; raises on invalid manifest or version conflict |
| `get(name)` | Record or `None` |
| `install(name)` | Set state → `installed` |
| `activate(name)` | Set state → `active` |
| `deactivate(name)` | Set state → `disabled` |
| `uninstall(name)` | Remove from registry |
| `unload(name)` | Hot-reload prep: active → installed |
| `reload(name)` | `unload` then `activate` |
| `list(state=None)` | All records, optionally filtered by state |
| `snapshot()` | `{name: {state, health, version}}` |

## Class: `PluginSandbox`

| Method | Behavior |
|---|---|
| `can(action)` | Permission check |
| `deny_list()` | Denied categories for this sandbox posture |
| `evaluate()` | Security findings (secrets/deploy/embedded-privileged) |

## CLI

Integrated into the Kernel CLI (`scripts/kernel.py`):

```bash
python scripts/kernel.py ext-plugin          # registry snapshot
python scripts/kernel.py ext-plugin-certify  # certify all engines as plugins
python scripts/kernel.py ext-check           # extension self-check (CI gate)
```

## Errors

| Error | Trigger |
|---|---|
| `PluginError("invalid manifest: ...")` | HIGH/CRITICAL validation findings |
| `PluginError("... already registered at version ...")` | version conflict |
| `PluginError("... is not registered")` | unknown plugin operation |
| `PluginError("missing dependency '...'")` | unresolved dependency |
| `PluginError("dependency cycle detected at '...'")` | cyclic deps |
