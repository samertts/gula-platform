---
id: SDK-000005
type: sdk
title: "Plugin SDK — Testing & Certification"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [sdk, plugin, testing, certification, gula-kernel-ext-001]
---

# Plugin Testing & Certification

> Mission: GULA-KERNEL-EXT-001 — Phase 1

## Testing Strategy

The Plugin SDK is covered by unit tests in
`backend/tests/unit/test_kernel_ext_plugin.py` (43 tests). Every bug fix
requires a regression test (constitution §5.5).

## Test Coverage Areas

| Area | Tests | Covers |
|---|---|---|
| Manifest validation | 10 | name, semver, entrypoint, isolation, permissions, contract, deps, `is_valid` |
| Version | 2 | valid/invalid semvers |
| Registry | 11 | register/get, duplicates, install/activate/deactivate, uninstall, hot reload, list, snapshot, lifecycle order |
| Dependencies | 3 | topological order, missing dep, cycle detection |
| Sandbox | 5 | deny/allow, deny list, secrets, deployment, embedded-privileged |
| Certification | 4 | clean certify, license policy, hard findings |
| Engine→Plugin | 2 | all 7 engines become valid plugins, contract preserved |
| Discovery | 4 | empty dir, plugin.json, bad json, missing fields |
| Rendering | 1 | registry markdown |

## Certification Process

```
manifest created
   ↓
validate_manifest()           [no HIGH/CRITICAL]
   ↓
PluginSandbox.evaluate()      [no secrets/deploy/iso-perm HIGH]
   ↓
license policy                [approved OSI license]
   ↓
certify() == []               → CERTIFIED
```

## Certification CLI

```bash
python scripts/kernel.py ext-plugin-certify   # certifies all 7 engines
python scripts/kernel.py ext-check            # CI gate: registration + certification
```

Both commands exit non-zero on any failure, so they are safe CI gates.

## Regression Policy

- New plugin capability → new test.
- Bug fix → regression test added before the fix is accepted.
- SDK API change → tests updated in the same commit.

## Run

```bash
ENV=test PYTHONPATH=.. backend/.venv/bin/python -m pytest \
  backend/tests/unit/test_kernel_ext_plugin.py -q --no-header
```
