---
id: SDK-000001
type: sdk
title: "Plugin SDK — Specification"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [sdk, plugin, gula-kernel-ext-001]
---

# Plugin SDK Specification

> Mission: GULA-KERNEL-EXT-001 — Phase 1
> Authority: `AI_OPERATING_CONSTITUTION.md`, `docs/constitution/17_PLUGIN_CONSTITUTION.md`

## Purpose

Every AI Engine becomes a plugin. The Plugin SDK is the official, versioned,
stable interface for building, installing, and managing engine plugins
without modifying the Kernel. No engine may bypass the SDK.

## Plugin Model

A plugin is a self-describing artifact identified by a **manifest** — a
superset of the Kernel 16-field engine contract (inputs, outputs, events,
errors, artifacts, ownership, dependencies, health, progress, checkpoint,
capabilities, resources, timeout, retry, version, status) plus plugin fields
(name, version, description, author, license, entrypoint, lifecycle,
permissions, isolation, marketplace metadata).

Existing engines in `ENGINE_REGISTRY` become plugins by construction via
`manifest_from_engine()` — no registry rewrite.

## Manifest Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Unique plugin id (lowercase, `-`/`.` separated) |
| `version` | semver | yes | Semantic version `X.Y.Z` |
| `description` | string | yes | One-line summary |
| `author` | string | yes | Plugin owner |
| `license` | string | yes | Approved OSI license (MIT, Apache-2.0, BSD-3-Clause, MPL-2.0) |
| `entrypoint` | string | yes | Dotted module path |
| `lifecycle` | enum | no | draft/registered/validated/installed/active/disabled/deprecated/uninstalled |
| `permissions` | list | yes | read/write/execute/network/filesystem/database/secrets/deployment |
| `isolation` | enum | no | sandbox/restricted/process/thread/embedded |
| `marketplace` | object | no | Marketplace metadata (type, categories, tags, rating) |
| `contract` | object | yes | The 16-field Kernel contract |

## Validation Rules

- `version` MUST be semantic (`X.Y.Z`). Non-semver → HIGH.
- `entrypoint` MUST be a dotted module path. Otherwise → HIGH.
- `isolation` MUST be one of the five levels. Otherwise → HIGH.
- Every permission MUST be in the approved categories. Otherwise → HIGH.
- All 16 Kernel contract fields MUST be present. Otherwise → HIGH.
- `name` MUST be non-empty. Otherwise → CRITICAL.
- Dependencies MUST be dotted references. Otherwise → MEDIUM.

## Dependency Resolution

`resolve_dependencies()` returns the topological order of a plugin's
dependencies (leaf-first). Missing dependencies and dependency cycles raise
`PluginError`. Install order is always dependency-first.

## Lifecycle

```
draft → registered → validated → installed → active
                                  ↕           ↕ (hot reload)
                                 disabled  uninstalled
```

See `PLUGIN_LIFECYCLE.md`.

## Isolation & Permissions

See `PLUGIN_SECURITY.md`.

## Certification

`certify()` runs manifest validation + sandbox evaluation + license policy.
Empty findings list = certified. See `PLUGIN_TESTING.md`.

## Registry

`PluginRegistry` is the canonical in-process registry. Registration rejects
re-registration at a different version. Hot reload is supported via
`unload()` / `reload()`.

## Reuse

The SDK reuses the Kernel contract (`scripts/kernel/core.py`), authority
(`scripts/governor/authority.py`), and safety (`scripts/governor/safety.py`).
It does not duplicate governance logic.

## Related

- `PLUGIN_API.md` — API reference
- `PLUGIN_LIFECYCLE.md` — lifecycle details
- `PLUGIN_SECURITY.md` — isolation, permissions, sandbox
- `PLUGIN_TESTING.md` — testing and certification
- `docs/constitution/17_PLUGIN_CONSTITUTION.md` — platform plugin constitution
