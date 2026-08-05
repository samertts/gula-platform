# MARKETPLACE REPORT

**Mission:** GULA-KERNEL-EXT-001 — Phase 11 (Final Certification)
**Certifier:** Kernel Extension Certification (deterministic engine checks)
**Date:** 2026-08-05
**Verdict:** **CERTIFIED**

---

## Scope

AI Marketplace (Phase 7): catalog and audited installation of reusable AI
assets (plugins, skills, policies, templates, prompts).

## Catalog

| ID | Kind | Name | Version | License | Status |
|---|---|---|---|---|---|
| CAT-000001 | plugin | governor-plugin | 1.0.0 | MIT | installed |
| CAT-000002 | policy | security-policy-set | 1.0.0 | MIT | available |
| CAT-000003 | skill | refactor-skill | 1.0.0 | MIT | available |

## License Gate (Open-Source First §2.2)

Approved licenses: MIT, Apache-2.0, BSD-3-Clause, MPL-2.0.
Proprietary licenses are rejected by `CatalogItem.__post_init__`.

## Properties Verified

1. **Immutable ids** — `CAT-XXXXXX`; semantic versions.
2. **Idempotent install** — double install rejected; state audited.
3. **Searchable** — by kind and free-text query.
4. **Replaceable** — versioned; new versions are new catalog entries.
5. **Audited** — indexed/installed/uninstalled events recorded.

## EXT-0011 Resolution

`scripts/auto_registry.py` ID patterns extended with
`POLICY`, `PLUGIN`, `CAT`, `MEM`, `EVT`, `WF` (18 patterns total).

## Evidence

- `backend/tests/unit/test_kernel_ext_marketplace.py` — 20 tests passing
- `.ai/core/marketplace/README.md`, `marketplace_catalog.json`

---

**Verdict: PASS** — marketplace is licensed, audited, and certified.
