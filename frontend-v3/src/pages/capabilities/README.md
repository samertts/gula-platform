# Capability pages — NR-054 disposition

These pages were produced by `scripts/zero_drift_engine.py` from
`docs/api/backend_inventory.json`. That inventory catalogues backend **route
files**, not **registered routes**, so the generator emitted a page, a route and
a navigation entry for every router under `backend/app/capabilities/` —
including the nine whose routers `factory.py` never includes. Each of those
pages issued `GET /<capability>` and received a 404, while the navigation
offered it as a working feature.

## Routed (1)

| Page | Endpoint | Owner |
| --- | --- | --- |
| `encounter-management` | `GET /national-data/encounters` | `app/routes/national_data.py::list_canonical_encounters` |

Bound to the canonical owner rather than to the capability stub: the endpoint is
registered, filters on `current_user.lab_id`, and is gated server-side on
`patients:read`.

## Not routed (8)

`clinical-foundation`, `document-management`, `healthcare-consent`,
`provider-management`, `reporting-service`, `search-service`,
`storage-service`, `workflow-engine`.

The components are kept — they are the starting point for whichever of these
capabilities is eventually built — but they are **deliberately absent from
`src/routes/index.tsx` and from `NAV_ITEMS`**, and must stay absent until a real
backend contract exists. `backend/tests/test_frontend_backend_contract.py`
fails if any of them is routed again.

Why not simply register the existing capability routers? Because they are
stubs: every `list_*` returns `{"items": [], "total": 0}` and every `create_*`
returns `{"success": true, "id": ""}` without writing anything. Registering them
would replace a visible 404 with an invisible lie — a page that looks like it
works and reports that your data is empty.

Why not bind them to another existing API, as `encounter-management` was? No
unambiguous canonical owner exists for any of the eight:

- **document**, **workflow**, **consent** — each has 2–4 competing
  implementations and no canonical owner (NR-051). Choosing one here would be
  making that decision by side effect.
- **reporting** — twelve domain-specific report endpoints (`/lims/reports`,
  `/public-health/reports`, `/nhdw/shift-reports`, …), no platform-wide one.
- **search** — 43 endpoints, all of which need a query; none is a listing.
- **storage** — only `/lims/storage`, which is physical sample storage, a
  different concept from a blob/file service.
- **provider** — the registered `…/providers` paths are AI, federation and
  payment *service* providers, not healthcare practitioners.
- **clinical-foundation** — the concept has no definition anywhere in the
  repository to bind to.

Re-enabling one means: implement or identify its canonical backend contract,
point the page at it, restore the route and the nav entry with the permission
the backend really enforces, and let the contract test above prove it.
