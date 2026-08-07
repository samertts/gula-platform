# ADR-032: Notifications Queue Completion (identity queue → backend/app/notifications)

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Engineering Lead, Platform Architect, CTO
**Supersedes:** (none — applies ADR-029 to the notifications capability)
**Related:** ADR-028, ADR-029, ADR-024, ADR-011

---

## Context

The structural migration phase (ADR-028) reduces the acknowledged Shared Core
reimplementation findings in
`.ai/core/architecture/constitution_baseline.json` to canonical providers
(`SHARED_CORE_CATALOG` in `backend/app/domain_platform/shared_core.py`).

Wave 3 order 13 targets the `notifications` capability (classification §2.7):

- **Finding #24:**
  `backend/app/identity/notifications/services.py` — `NotificationService`
  (queue-only: `send_notification`, `send_template`, `mark_sent`/`mark_delivered`/
  `mark_read`, `get_pending`, preferences, templates).
- **Finding #49:**
  `backend/app/identity/notifications/routes.py` — `send_notification` +
  9 more handlers (queue-only), 10 endpoints under `/niam/notifications/*`.
- **Canonical provider:** `backend/app/notifications` — delivers (sync
  `service.NotificationService`, Telegram channels) but has **no persistence,
  queue, templates, or preferences**.

**Behavioral equivalence:** the two layers are **complementary halves** —
the canonical provider delivers, the finding queues. The finding is the
**ONLY DB-backed notification queue/template/preference layer in the
platform**: it owns the `niam_notif_templates`, `niam_notif_queue`, and
`niam_notif_preferences` tables (migration
`20260723_0002_niam_completion_tables.py`) and backs the live
`/niam/notifications/*` API. Archiving it would delete working, data-bearing
behavior; no canonical queue exists to re-point to.

**Consumer inventory (complete):** the only in-repo importers of
`app.identity.notifications` are `backend/app/identity/api/router.py`
(line 11 import, line 32 include under `/niam`) and
`backend/tests/test_niam_v2.py` (lines 454, 470 — model imports). The package
`__init__.py` is empty (0 bytes) — not a public API.

This is therefore **not a removal** (nothing is dead) and **not an archive**
(no canonical queue exists). It is a **Canonical Provider Completion**
(ADR-029): the canonical provider gains its missing persistence half by
promotion, and the NIAM surface is re-pointed to it.

The canonical ownership of the Notifications Queue is being changed, so this
decision is recorded as an ADR (Documentation Policy).

## Decision

Complete the canonical `backend/app/notifications` provider with the queue/
template/preference layer, per ADR-029:

1. **Live code is promoted, not archived.** `git mv` (history preserved):
   - `backend/app/identity/notifications/models.py` →
     `backend/app/notifications/models.py`
   - `backend/app/identity/notifications/services.py` →
     `backend/app/notifications/services.py`
   - `backend/app/identity/notifications/routes.py` →
     `backend/app/notifications/routes.py`
   The vacated `backend/app/identity/notifications/` package (empty
   `__init__.py`, not a public API) is removed.
2. **The queue service class is renamed `NotificationService` →
   `NotificationQueueService`.** This is required because the canonical
   package already defines a **different** `NotificationService` (the sync
   delivery service in `service.py`, exported by `__init__.py`). Two same-named
   classes in one canonical package would be an ambiguity and a latent bug.
   No consumer references the class name directly (only the moved routes
   instantiate it); the public surface is the routes, so behavior is preserved.
3. **The route/API layer moves with the service.** The router keeps
   `prefix="/notifications"`, its tags, its 10 handlers, and its JSON shapes
   (`to_dict()`), and is re-mounted unchanged at `/niam/notifications/*` via
   the existing NIAM router — API paths, parameters, and responses are
   byte-identical.
4. **ORM models move with the layer** (ADR-029 Rule 2: the canonical provider
   is self-contained). The models **retain their `IdentityBaseEntity` base**
   (`app.identity.base`): this is REQUIRED for behavior preservation —
   `IdentityBaseEntity` registers the `before_insert` listener that resolves
   the `id=...` Ellipsis placeholder used by every call site, and provides
   `to_dict()`, `created_at`, and `updated_at` matching the `niam_notif_*`
   tables. `app.identity` is platform infrastructure (NIAM), not one of the 11
   healthcare domains; the retained base dependency does not invert the
   domain graph and is documented as a deliberate exception.
5. **All in-repo consumers are re-pointed atomically** in the same commit
   (`identity/api/router.py`, `test_niam_v2.py`); **no compatibility facade**
   is created under the vacated namespace (ADR-029 Rule 4).
6. **No schema change.** The `niam_notif_*` tables (migration
   `20260723_0002`) and all routes/mounts are untouched.
7. **ADR-028 Rules 1–7 and ADR-029 Rules 1–6 apply verbatim.** The promotion
   commit preserves behavior, carries evidence, keeps the backend
   authoritative, produces a Migration Impact Report, stays reversible via
   single `git revert`, and executes one commit at a time with a stop for
   approval.

The first application is Commit 3.1, resolving the `notifications` findings
#24 and #49 (37 → 35) by canonical completion + ownership correction.

## Alternatives Considered

### A. Archive-and-repoint

Rejected: the canonical provider has no queue to re-point to. Archiving the
only DB-backed notification queue would delete working, data-bearing behavior
(queued notifications, templates, preferences) and leave
`backend/app/notifications` delivery-only forever — the finding would not be
resolved, only renamed.

### B. Reimplement the queue inside canonical, then archive

Rejected: this duplicates a complete, working layer (write a new queue to
replace one that already works) with no behavior gain, and it recreates the
finding in new code before deleting the old. Promotion carries the proven
implementation instead of re-inventing it.

### C. Register the identity module as canonical by exception

Rejected: whitelisting `app.identity.notifications.*` as canonical without
moving it would keep Shared Core implementation inside a domain (inverted
dependency, domain-sovereignty violation) and require a constitution
exception. Moving the code to the already-designated canonical path achieves
the same finding reduction with no exception.

### D. Move only services + routes, keep models in identity

Rejected: the canonical provider would then depend on `app.identity.notifications`
for its own models (Shared Core importing from a domain), recreating the
inversion the promotion exists to fix, and the layer would be split across two
packages. Models must move with the layer.

### E. Promote but keep a facade at the old module path

Rejected: ADR-029 Rule 4 forbids a re-export facade under the vacated module
path — it would re-introduce the duplicate module path. All in-repo consumers
are re-pointed in the same commit instead.

## Consequences

**Positive**

- The `notifications` Shared Core capability finally has a real, populated
  canonical provider: `backend/app/notifications` becomes delivers + queues +
  templates + preferences in one authoritative place.
- The acknowledged-findings baseline shrinks by ownership correction
  (37 → 35) and never re-opens the duplicate.
- Domain Sovereignty improves: the identity domain consumes a Shared Core
  capability instead of implementing it.
- Behavior is preserved exactly — identical tables, identical
  `/niam/notifications/*` API, identical `id=...`/`to_dict()` semantics —
  verified by the identical backend suite, identical boot route count, and an
  identical OpenAPI surface (no contract change).

**Negative**

- The old namespace `app.identity.notifications` is vacated; any out-of-repo
  consumer importing it directly would break (none exist in-repo; consumers
  were re-pointed atomically in the same commit).
- The canonical package gains ~560 LOC of live implementation (models 76 +
  services 285 + routes 198), shifting maintenance ownership from the identity
  domain to Shared Core (intended).
- A documented dependency on `app.identity.base.IdentityBaseEntity` is
  retained for the promoted models (behavior-required, see Decision 4).

**Neutral**

- The NIAM notifications surface stays mounted via the existing NIAM router;
  `factory.py` is unchanged.
- The legacy `/notify` surface (`app/routes/notifications.py`) is untouched.

## References

- ADR-029 — Canonical Provider Promotion (`docs/adr/ADR-029-canonical-provider-promotion.md`)
- ADR-028 — Structural Migration Rules (`docs/adr/ADR-028-structural-migration.md`)
- ADR-024 — Platform Constitution (`docs/adr/ADR-024-Platform-Constitution.md`)
- ADR-011 — Notification Platform (`docs/adr/ADR-011-notification-platform.md`)
- `backend/app/domain_platform/shared_core.py` — `SHARED_CORE_CATALOG` (`notifications`)
- `backend/app/notifications/` — canonical provider (delivery + promoted queue layer)
- `backend/app/identity/notifications/` — vacated namespace (models/services/routes moved)
- `backend/app/identity/base.py` — `IdentityBaseEntity` (retained ORM base)
- `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` — §2.7 (#24/#49), Wave 3 table
- `docs/baselines/COMMIT_3_1_VERIFICATION_REPORT.md` — execution evidence
