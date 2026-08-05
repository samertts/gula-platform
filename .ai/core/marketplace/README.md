---
id: CAT-INDEX
type: marketplace
title: "AI Marketplace"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [marketplace, catalog, plugins, skills, policies, gula-kernel-ext-001]
---

# AI Marketplace

> Mission: GULA-KERNEL-EXT-001 — Phase 7
> Implementation: `scripts/kernel/ext/marketplace.py`
> Catalog: `marketplace_catalog.json`

Catalog and installation of reusable AI assets: plugins, skills,
policies, templates, and prompts.

## Model

| Concept | Definition |
|---|---|
| CatalogItem | id (CAT-XXXXXX), kind, name, semver, description, source, approved license |
| Marketplace | add, get, search(kind/query), install, uninstall, installed, snapshot, save |
| License gate | MIT, Apache-2.0, BSD-3-Clause, MPL-2.0 (Open-Source First §2.2) |

## Properties

1. **Immutability** — ids never change; versions are semantic.
2. **Idempotent install** — installing twice is rejected; state is audited.
3. **Searchable** — by kind and free-text query.
4. **Replaceable** — items are versioned; new versions are new catalog
   entries (Phase 4 migrations move between versions).
5. **Licensed** — only permissive open-source licenses are catalogued.

## CLI

```bash
python scripts/kernel.py ext-marketplace   # catalog + install demo
python scripts/kernel.py ext-check         # includes marketplace install gate
```

## Reuse

Shares the semver parser with Phase 3 Compatibility, the SDK manifest
fields with Phase 1, and extends the auto-registry ID pattern catalogue
(scripts/auto_registry.py) with POLICY/PLUGIN/CAT/MEM/EVT/WF — resolving
EXT-0011.

## Related

- `marketplace_catalog.json` — machine-readable catalog
- Phase 1 Plugin SDK — plugin manifests and lifecycle
- `scripts/auto_registry.py` — ID pattern catalogue (EXT-0011 resolved)
