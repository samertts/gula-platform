# PLUGIN CERTIFICATION

**Mission:** GULA-KERNEL-EXT-001 — Phase 11 (Final Certification)
**Certifier:** Kernel Extension Certification (deterministic engine checks)
**Date:** 2026-08-05
**Verdict:** **CERTIFIED**

---

## Scope

Certification of the Plugin SDK (Phase 1) over all 7 Kernel engines.

## Results

| Engine | Manifest | Certified | HIGH/CRITICAL | Advisory (MEDIUM) |
|---|---|---|---|---|
| architect | valid | ✅ | 0 | 2 |
| orchestrator | valid | ✅ | 0 | 2 |
| reviewer | valid | ✅ | 0 | 2 |
| builder | valid | ✅ | 0 | 2 |
| deployer | valid | ✅ | 0 | 2 |
| learner | valid | ✅ | 0 | 2 |
| optimizer | valid | ✅ | 0 | 2 |

- **Plugins registered:** 7
- **Certified (no HIGH/CRITICAL findings):** 7/7
- **Hard findings:** 0

## Advisory Findings (non-blocking)

Each engine manifest reports 2 MEDIUM findings:
- `invalid dependency reference constitution`
- `invalid dependency reference governor`

**Rationale:** the sandbox dependency validator currently accepts engine
names and marketplace item ids; `constitution` and `governor` are knowledge
layers, not marketplace items. Advisory until Phase 7 marketplace resolves
these as catalog entries. No sandbox or deployment risk is introduced.

## Checks Performed

- `validate_manifest` — id/version/entrypoint/contract/isolation/permissions
- `certify` — validation + sandbox + license policy (MIT/Apache-2.0/BSD-3-Clause/MPL-2.0)
- `ext-plugin` — registry snapshot
- `ext-plugin-certify` — per-engine certification
- `ext-check` — registration + certification gate

## Evidence

- `backend/tests/unit/test_kernel_ext_plugin.py` — 43 tests passing
- `python scripts/kernel.py ext-plugin` / `ext-plugin-certify` — PASS
- `python scripts/kernel.py ext-check` — ALL KERNEL EXTENSION CHECKS PASSED

---

**Verdict: PASS** — the Plugin SDK is enterprise-certified.
