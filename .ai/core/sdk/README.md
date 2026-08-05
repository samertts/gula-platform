---
id: SDK-000000
type: sdk
title: "Plugin SDK — Overview"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [sdk, plugin, gula-kernel-ext-001]
---

# Plugin SDK — Overview

> Mission: GULA-KERNEL-EXT-001 — Phase 1
> Implementation: `scripts/kernel/ext/plugin.py`

The official SDK for the GULA AI Kernel. Every AI Engine becomes a plugin.
Plugins are discovered, validated, registered, installed, sandboxed,
certified, versioned, and hot-reloaded through one canonical interface. No
engine may bypass the SDK.

## Documents

| Document | Purpose |
|---|---|
| `PLUGIN_SPEC.md` | Specification, manifest, validation rules |
| `PLUGIN_API.md` | API reference |
| `PLUGIN_LIFECYCLE.md` | Lifecycle states & transitions |
| `PLUGIN_SECURITY.md` | Permissions, isolation, sandbox |
| `PLUGIN_TESTING.md` | Testing & certification |

## Quick Start

```bash
# List registered engine plugins + validate all engines as plugins
python scripts/kernel.py ext-plugin

# Certify all engines as plugins
python scripts/kernel.py ext-plugin-certify

# Extension self-check (CI gate)
python scripts/kernel.py ext-check
```

## Key Concepts

- **Manifest** — superset of the Kernel 16-field contract + plugin metadata.
- **Registry** — canonical in-process plugin store with version conflict
  detection.
- **Sandbox** — default-deny permission model + 5 isolation levels.
- **Lifecycle** — draft → registered → validated → installed → active
  (with disabled / deprecated / uninstalled), plus hot reload.
- **Certification** — validation + sandbox + license gate; empty findings =
  certified.

## Reuse

The SDK composes the Kernel contract (`scripts/kernel/core.py`), the
Governor authority (`scripts/governor/authority.py`), and Governor safety
(`scripts/governor/safety.py`). It never duplicates governance logic.

## Related

- `docs/constitution/17_PLUGIN_CONSTITUTION.md`
- `KERNEL_EXTENSION_AUDIT.md`
- Kernel: `scripts/kernel/core.py`, `scripts/kernel/contract.py`
