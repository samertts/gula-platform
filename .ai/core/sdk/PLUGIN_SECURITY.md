---
id: SDK-000004
type: sdk
title: "Plugin SDK — Security"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [sdk, plugin, security, sandbox, gula-kernel-ext-001]
---

# Plugin Security

> Mission: GULA-KERNEL-EXT-001 — Phase 1
> Authority: `docs/constitution/17_PLUGIN_CONSTITUTION.md`, OWASP ASVS,
> Least Privilege, Defense in Depth, Zero Trust

## Permissions Model

Plugins declare permissions at installation time. Users (or the Reviewer
engine) approve the permission grant — never assumed.

| Permission | Grants | Risk |
|---|---|---|
| `read` | Read knowledge/config | Low |
| `write` | Write workspace/knowledge | Medium |
| `execute` | Execute commands/scripts | Medium |
| `network` | Network access | High |
| `filesystem` | File system access | Medium |
| `database` | Database access | High |
| `secrets` | Access credentials | Critical |
| `deployment` | Deploy/rollback | Critical |

`secrets` and `deployment` permissions always trigger a HIGH finding in
`PluginSandbox.evaluate()` and require explicit Reviewer approval.

## Isolation Levels

| Level | Isolation | Default permissions |
|---|---|---|
| `sandbox` | Fully sandboxed | read only; network/db/secrets/deploy always denied |
| `restricted` | Sandboxed with explicit grants | approved categories only |
| `process` | Isolated plugin process | per-manifest grants |
| `thread` | Isolated worker | per-manifest grants |
| `embedded` | Inline (first-party) | read only by default |

`PluginSandbox.deny_list()` returns the denied categories for the active
posture — the sandbox always denies what is not explicitly granted (Zero
Trust default-deny).

## Security Findings

`PluginSandbox.evaluate()` reports:

- `PLUGIN-SECRETS` (HIGH) — plugin requests secrets access
- `PLUGIN-DEPLOY` (HIGH) — plugin requests deployment permission
- `PLUGIN-ISO-PERM` (MEDIUM) — embedded isolation with privileged
  permissions (should use process isolation)

## Certification Gates

A plugin is certified only when `certify()` returns no HIGH/CRITICAL
findings. Certification covers: manifest validity, sandbox posture, and
license policy (approved list: MIT, Apache-2.0, BSD-3-Clause, MPL-2.0).

## Rules

1. Plugins use published Kernel APIs only — no internal services.
2. Plugins never modify core database schema (they add prefixed tables only).
3. A misbehaving plugin must not affect Kernel stability (sandbox first).
4. Permissions are declared at install and approved explicitly.
5. Secrets/deployment require Reviewer approval and are audited.
6. Version upgrades follow the same review as fresh installs
   (`17_PLUGIN_CONSTITUTION.md`).
