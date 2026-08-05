---
id: SDK-000003
type: sdk
title: "Plugin SDK — Lifecycle"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [sdk, plugin, lifecycle, gula-kernel-ext-001]
---

# Plugin Lifecycle

> Mission: GULA-KERNEL-EXT-001 — Phase 1

## Lifecycle States

```
draft ──→ registered ──→ validated ──→ installed ──→ active
             ↑                              │            │
             │                              ↓            │
          (re-register)                  disabled        │
                                              ↑          │
                                              └──(hot reload / reactivate)
                                                        │
                                                     uninstalled
```

| State | Meaning | Allowed transitions |
|---|---|---|
| `draft` | Manifest created, not registered | → registered |
| `registered` | In `PluginRegistry` | → validated, → uninstalled |
| `validated` | Passed validation + sandbox checks | → installed |
| `installed` | Available, not serving | → active, → uninstalled |
| `active` | Loaded and serving | → disabled, → installed (unload) |
| `disabled` | Installed but inactive | → active, → uninstalled |
| `deprecated` | Superseded / EOL | → disabled, → uninstalled |
| `uninstalled` | Removed from registry | terminal |

## Transitions (registry operations)

| Operation | From → To |
|---|---|
| `register(manifest)` | draft → registered |
| `install(name)` | registered/validated → installed |
| `activate(name)` | installed → active |
| `deactivate(name)` | active → disabled |
| `unload(name)` | active → installed |
| `reload(name)` | installed → active (hot reload) |
| `uninstall(name)` | any → uninstalled (removed) |

## Hot Reload

Hot reload (`unload()` then `activate()`) re-activates a plugin in place.
Used after an approved version upgrade. Lifecycle safety: a plugin is only
re-loaded when it was previously installed, so a failed reload leaves the
plugin in `installed` state — never in a broken `active` state.

## Health & Monitoring

Each `PluginRecord` carries `health` and `loaded_at`. The Health Engine
(Phase 10) reads plugin health from the registry; degraded plugins are
candidates for disable (never automatic uninstall).

## Lifecycle Governance

- State transitions are recorded and auditable (Observability, Phase 13 of
  the Kernel).
- Uninstall never deletes plugin data — consistent with
  `17_PLUGIN_CONSTITUTION.md` ("Disabling a plugin does not delete its data").
- Deprecation precedes removal: a plugin MUST be deprecated before
  uninstall when it has been active.
