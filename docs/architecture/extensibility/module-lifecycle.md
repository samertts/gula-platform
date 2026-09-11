# Module lifecycle

**PROGRAM-EXT-001, Phase 9.** Normative.

## 1. The states

`app/kernel/types.py::CapabilityMaturity`.

| State | Means | Evidence required to enter |
| --- | --- | --- |
| `proposed` | someone wants it | a written problem statement and an owner |
| `designed` | shape agreed | a contract: API, events, data, tenancy |
| `experimental` | code exists | unit tests; **off by default**; no production data |
| `internal` | staff-facing | integration tests; audit declared; internal tenants only |
| `pilot` | one or few real sites | tests against migrated PostgreSQL; authorization and tenancy proven; rollback rehearsed |
| `validated` | proven at a pilot's scale | the pilot's own evidence, reviewed; no open P0/P1 against it |
| `production` | generally available | performance and failure-mode evidence; runbook; monitoring |
| `national` | national deployment | DR proven; scale evidence; governance sign-off; data-protection review |
| `deprecated` | on the way out | successor exists and is at least `production`; `deprecation` block populated |
| `retired` | gone | no traffic for the declared window; data migrated or lawfully destroyed |

## 2. Two things maturity is not

**It is not `CapabilityStatus`.** Status says what the platform *does* with a
capability — draft, active, deprecated, retired. Maturity says how much evidence
stands behind it. They move independently, and a capability can be `active` and
`experimental` at once. Keeping them separate is what stops "we turned it on"
from being read as "we proved it".

**It is not a feature flag.** The flag controls presence. Maturity records
evidence. `validate_descriptor` checks they are consistent — a `production`
capability behind an `experimental` flag is either mislabelled or an unfinished
rollout — but consistency is not identity.

## 3. Transitions

Forward one step at a time. `experimental → production` is not a transition; it
is three transitions and the evidence for each.

Backward is always allowed and needs no ceremony. A `pilot` capability that
fails at a site returns to `experimental` the moment someone notices — waiting
for a review to agree it failed is how a bad capability stays deployed.

Every transition changes `maturity` in the descriptor, so it appears in the
diff and gets reviewed as code.

## 4. Evidence proportional to risk

The bar is set by what the capability can damage, not by how large it is.

* Touches patient data, authorization, audit or tenancy → evidence against
  **migrated PostgreSQL**. Not SQLite, not `create_all()`, not a mocked session.
  This is the TEST-001 rule and it is not negotiable for these categories.
* Touches money → the same, plus concurrency evidence on two real connections.
* Touches neither → unit tests are enough.

A mock proves the shape of a call. It cannot prove a predicate — which is how a
missing `Account.is_locked` filter survived review until NR-044.1 ran the real
query. That is the whole argument for this section in one sentence.

## 5. Retirement

Retiring is work, not an absence of work:

1. `deprecation` block populated: `since_version`, `removal_version`,
   `replacement`, `migration_notes`.
2. Consumers notified; traffic measured until it is zero.
3. Routes removed at the declared version, not before.
4. Data migrated or lawfully destroyed — retention rules outlive the code.
5. Descriptor set to `retired`; the row **stays in the registry**. A retired
   capability that vanishes from the catalogue takes its history with it, and
   the next person proposes it again.

## 6. Feature flags (Phase 8)

### 6.1 What exists

Four flag systems, in different places, doing different jobs:

| System | Scope | Source |
| --- | --- | --- |
| `app/core/sndhs_flags.py` | deployment-wide | env vars (`SNDHS_ENABLE_VISITS`, `SNDHS_ENABLE_NATIONAL_ID`, `ENABLE_FINANCIAL_ENGINE`, `ENABLE_ADS`) |
| `app/core/feature_flags.py` | per-tenant | subscription tier, resolved from the database |
| `app/kernel/features/` | kernel | `FeatureFlagManager` + capability, experimental, regional, tenant and kill-switch managers |
| `app/platform/` | ad-hoc | module-local checks |

Four is not a defect by itself — deployment-wide and per-tenant are genuinely
different questions. What is missing is a statement of which class a given flag
belongs to, and that is what `FeatureFlagClass` adds.

### 6.2 The classes

`app/kernel/types.py::FeatureFlagClass`:
`EXPERIMENTAL`, `INTERNAL`, `PILOT`, `PRODUCTION`, `NATIONAL`, `DEPRECATED`.

A class states the **audience**, and `validate_descriptor` checks it against
maturity: a `production` capability behind an `experimental` flag is either
mislabelled or an unfinished rollout, and either way someone should look.

### 6.3 The rule that is not negotiable

**A feature flag is never an authorization decision.**

A flag answers "is this capability present in this deployment, for this
tenant?". Authorization answers "may this actor do this, to this resource, in
this scope?". They are evaluated in different places, by different code, for
different reasons.

Using a flag as authorization fails in both directions: turning a flag on grants
everyone access, and turning it off hides a control failure behind an
availability decision. Server-side authorization remains authoritative and is
evaluated per request, whatever any flag says.

This is guarded:
`tests/test_extensibility_guards.py::test_a_feature_flag_is_never_an_authorization_decision`
asserts that no flag check stands in for a permission check in the identity or
clinical-gateway authorization paths.

### 6.4 Flags and clinical safety

`SNDHS_ENABLE_VISITS` and `SNDHS_ENABLE_NATIONAL_ID` require a data backfill and
a schema verification before they are turned on against existing data — see
`docs/sndhs/phase1/RUNBOOK.md`. A flag whose activation requires a migration is
a deployment step, not a toggle, and must be documented as one in the
capability's `configuration`.
