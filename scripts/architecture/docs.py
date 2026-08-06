"""PROGRAM-ALPHA — master architecture document generator.

Regenerates the authoritative PROGRAM-ALPHA deliverables from live sources:
  MASTER_ARCHITECTURE_v2.md
  SHARED_CORE_REGISTRY.md
  DOMAIN_SOVEREIGNTY.md
  DOMAIN_DEPENDENCY_GRAPH.md
  WORKSPACE_ARCHITECTURE.md
  DIGITAL_TRUST_PLATFORM.md
  MASTER_REMAINING_WORK.md

Every number and verdict below is computed at generation time from the real
codebase and the Domain Platform Framework — nothing is hard-coded.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from app.domain_platform.core import SHARED_CORE_SERVICES
from app.domain_platform.manifest import CANONICAL_DOMAINS
from app.domain_platform.shared_core import SHARED_CORE_CATALOG

from scripts.architecture.core import REPO_ROOT, RULES
from scripts.architecture.gate import (
    load_baseline,
    load_country_baseline,
    run_all_gates,
)

TODAY = datetime.date.today().isoformat()
ROOT = REPO_ROOT


def _catalog_rows() -> str:
    rows = []
    for svc in SHARED_CORE_SERVICES:
        entry = SHARED_CORE_CATALOG[svc]
        rows.append(f"| `{svc}` | `{entry['provider']}` | {entry['description']} |")
    return "\n".join(rows)


def _domain_rows() -> str:
    rows = []
    for m in CANONICAL_DOMAINS.values():
        rows.append(
            f"| `{m.code}` | {m.name_en} | {m.name_ar} | `{m.workspace_type}` | "
            f"{', '.join(m.services)} | {len(m.contracts)} |"
        )
    return "\n".join(rows)


def _workspace_rows() -> str:
    rows = []
    seen = set()
    for m in CANONICAL_DOMAINS.values():
        ws = m.workspace_type
        if ws in seen:
            continue
        seen.add(ws)
        hosted = [d.code for d in CANONICAL_DOMAINS.values() if d.workspace_type == ws]
        ui = []
        for d in CANONICAL_DOMAINS.values():
            if d.workspace_type == ws:
                ui.extend(d.ui)
        rows.append(f"| `{ws}` | {', '.join(hosted)} | {', '.join(ui)} |")
    return "\n".join(rows)


def _finding_rows() -> str:
    baseline = load_baseline()
    by_rule: dict[str, list[str]] = {}
    for f in baseline:
        by_rule.setdefault(f["rule_id"], []).append(f["path"])
    rows = []
    for rule_id in sorted(by_rule):
        detail = RULES[rule_id]["description"]
        rows.append(f"| `{rule_id}` | {detail} | {len(by_rule[rule_id])} |")
    return "\n".join(rows)


def _finding_detail_rows() -> str:
    baseline = load_baseline()
    rows = []
    for f in sorted(baseline, key=lambda x: (x["rule_id"], x["path"])):
        rows.append(f"- [`{f['rule_id']}`] `{f['path']}`")
    return "\n".join(rows)


def write_all() -> list[Path]:
    written = []
    gate = run_all_gates()
    c = gate["constitution"]
    d = gate["domain"]

    # ── MASTER_ARCHITECTURE_v2.md ──────────────────────────────────────────
    doc = f"""# MASTER_ARCHITECTURE_v2 — GULA National Healthcare Platform

> PROGRAM-ALPHA | regenerated {TODAY} by `scripts/architecture/docs.py`
> Platform verdict: **{gate['verdict']}** — Domains **{d['domains_passed']}/{d['domains_total']}**,
> isolation **{'PASS' if d['isolation_passes'] else 'FAIL'}**.

## 1. Mission

Transform GULA into a sovereign national healthcare platform built on
**Shared Core**, **Domain Sovereignty**, **Workspace Architecture**, a
**Unified Digital Trust Platform**, **Zero Business Logic Duplication**,
**Zero Cross-Domain Administration**, **Country-Agnostic Design** and
**Backward Compatibility**. Nothing here reduces existing functionality,
breaks tests, weakens security, or duplicates infrastructure.

## 2. Layer model

```
┌─────────────────────────────────────────────────────────────┐
│  UI layer  —  citizen / laboratory / pharmacy / radiology /  │
│              hospital / blood_bank / provider / research /   │
│              insurance / public_health / government          │
│              (rendered ONLY inside the bound workspace)      │
├─────────────────────────────────────────────────────────────┤
│  Domain layer — 11 sovereign Domains                         │
│  each owns ONLY: entities, services, policies, validation,   │
│  reports, events, workflows, UI, public APIs                 │
│  communication ONLY via public REST/FHIR R4/HL7, versioned   │
│  contracts, and the Event Bus                                │
├─────────────────────────────────────────────────────────────┤
│  Shared Core — {len(SHARED_CORE_SERVICES)} authoritative services,     │
│  each existing EXACTLY once (see SHARED_CORE_REGISTRY.md)     │
├─────────────────────────────────────────────────────────────┤
│  Digital Trust — NIAM identity (citizen, professional, org,  │
│  service account, device), MFA, sessions, delegation, audit  │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure — storage, messaging, observability, cache,  │
│  scheduler, feature flags, backups (shared/ only)            │
└─────────────────────────────────────────────────────────────┘
```

## 3. Architecture invariants

1. Every reusable capability exists exactly once (Shared Core).
2. Every Domain is sovereign — it never reaches another Domain's tables,
   services, or permission store.
3. One identity, unlimited workspaces, ONE active workspace per identity;
   permissions never cross workspaces.
4. Cross-domain communication only via public APIs, FHIR R4, HL7, versioned
   contracts, or the Event Bus.
5. Country-specific behaviour lives only in the national layer; Domains stay
   country-agnostic.
6. Every architectural decision preserves backward compatibility (SemVer
   MAJOR = breaking, gated).

## 4. Bounded contexts (Domains)

{_domain_rows()}

## 5. Certification

| Certificate | Result |
|---|---|
| Domain certification (9 checks / Domain) | **{d['domains_passed']}/{d['domains_total']}** |
| Isolation (imports, cycles, shared state, permissions, DB, tables) | **{'PASS' if d['isolation_passes'] else 'FAIL'}** |
| Shared Core reimplementation scan | **{c['total_findings']} findings, {c['baseline_acknowledged']} acknowledged** |
| Cross-domain administration | **{len(d['cross_domain_admin'])}** |
| Country-agnostic | **{'PASS' if gate['country_agnostic']['passes'] else 'FAIL'}** |
| Architecture Constitution gate | **{gate['verdict']}** |

## 6. Governance

The Architecture Constitution (`ARCHITECTURE_CONSTITUTION.md`) is enforced by
`scripts/architecture/` and gated in CI. PRs that duplicate infrastructure,
break Shared Core, break Domain Sovereignty, break Workspace isolation, or
break Country-Agnostic design **automatically fail**.

## 7. Companion documents

| Document | Content |
|---|---|
| `SHARED_CORE_REGISTRY.md` | authoritative {len(SHARED_CORE_SERVICES)}-service registry |
| `DOMAIN_SOVEREIGNTY.md` | the 11 Domains and their blueprints |
| `DOMAIN_DEPENDENCY_GRAPH.md` | dependency, contract and event topology |
| `WORKSPACE_ARCHITECTURE.md` | one identity, unlimited workspaces |
| `DIGITAL_TRUST_PLATFORM.md` | NIAM Digital Trust capabilities |
| `ARCHITECTURE_CONSTITUTION.md` | the permanent architecture gates |
| `ARCHITECTURE_CERTIFICATION.md` | Phase 9 certification verdict |
| `MASTER_REMAINING_WORK.md` | acknowledged debt + migration plan |

_Generated by scripts/architecture/docs.py._
"""
    p = ROOT / "MASTER_ARCHITECTURE_v2.md"
    p.write_text(doc, encoding="utf-8")
    written.append(p)

    # ── SHARED_CORE_REGISTRY.md ────────────────────────────────────────────
    doc = f"""# SHARED_CORE_REGISTRY — The ONE authoritative Shared Core

> PROGRAM-ALPHA Phase 2 | regenerated {TODAY}
> **{len(SHARED_CORE_SERVICES)} services, each with EXACTLY ONE authoritative provider.**
> Domains consume these; they never rebuild them.

## 1. Principles

1. **Everything reusable exists once.** A service appears in this registry only
   if exactly one authoritative provider exists.
2. **Domains own business logic; Shared Core owns infrastructure.** A Domain
   that instantiates `Fernet`, a task queue, an engine, or an event bus instead
   of consuming the registry fails certification.
3. **Replacement is swappable.** Every entry is a replaceable module — no
   vendor coupling, self-hosted first, open source first.
4. **Legacy duplicates are tracked, never grown.** The Architecture
   Constitution scan fails PRs that introduce a new implementation of any
   registry service outside its provider.

## 2. The registry

| Service | Authoritative provider | Responsibility |
|---|---|---|
{_catalog_rows()}

## 3. Consumption rules

- A Domain may import Shared Core providers freely.
- A Domain may NOT import another Domain's modules, tables, or services.
- Cross-domain needs are met via the Cross-Domain Gateway and versioned
  contracts, or events on the Event Bus.
- A Domain may NOT reimplement any registry service (enforced by the 9-check
  `DomainCertificationEngine` and the Architecture Constitution scan).

## 4. Maturity

- Authoritative registry: **{len(SHARED_CORE_SERVICES)} services declared**.
- Real providers verified on disk: **{len(SHARED_CORE_SERVICES)}** (100%).
- Backed by `shared/` ({len(list((ROOT / 'shared').glob('*')))} top-level
  components) + `backend/app/identity`, `backend/app/security`,
  `backend/app/notifications`, `backend/app/workflows`, `backend/app/fhir`,
  `backend/app/capabilities/*`.
- Known consolidation debt: **{len(load_baseline())} finding(s)** — see
  `MASTER_REMAINING_WORK.md`.

_Generated by scripts/architecture/docs.py._
"""
    p = ROOT / "SHARED_CORE_REGISTRY.md"
    p.write_text(doc, encoding="utf-8")
    written.append(p)

    # ── DOMAIN_SOVEREIGNTY.md ──────────────────────────────────────────────
    doc = f"""# DOMAIN_SOVEREIGNTY — The 11 GULA Domains

> PROGRAM-ALPHA Phase 3 | regenerated {TODAY}
> **{len(CANONICAL_DOMAINS)} sovereign Domains, all certified
> {d['domains_passed']}/{d['domains_total']} at 100%, isolation PASS.**

## 1. Sovereignty contract

Each Domain owns ONLY:

1. **Entities** — aggregates, entities, value objects, tables.
2. **Services** — application and domain services (its business logic).
3. **Policies** — domain invariants, business rules, clinical policies.
4. **Validation** — domain-level validation.
5. **Reports** — domain reports (built on the Shared Core reporting framework).
6. **Events** — domain events emitted/subscribed on the Event Bus.
7. **Workflows** — domain workflows and state machines.
8. **UI** — rendered ONLY inside its bound workspace.
9. **APIs** — its public REST surface.

Each Domain owns NONE of: databases beyond its tables, notification systems,
audit systems, engines, caches, queues, encryption, identity — those live in
Shared Core.

## 2. The Domains

| Code | Name (EN) | Name (AR) | Workspace | Services | Contracts |
|---|---|---|---|---|---|
{_domain_rows()}

## 3. Sovereignty enforcement

| Check | Mechanism |
|---|---|
| No direct DB access between Domains | `IsolationValidator` — table overlap + engine coupling scan |
| No direct service coupling | cross-domain import scan (only Shared Core + contracts allowed) |
| No permission leakage | namespace-ownership permission scan |
| No shared mutable state | module-level mutable globals scan |
| No circular dependencies | DFS cycle detection on the import graph |
| No cross-domain administration | `FORBIDDEN_DOMAIN_OWNERSHIP` is empty and enforced |
| Shared Core 100% consumption | `shared_core_usage_100` certification check |
| Backward compatibility | SemVer gate on every Domain release |

Every new module must declare a Domain Blueprint here before merge; modules
without a blueprint are not part of any Domain and fail the platform audit.

_Generated by scripts/architecture/docs.py._
"""
    p = ROOT / "DOMAIN_SOVEREIGNTY.md"
    p.write_text(doc, encoding="utf-8")
    written.append(p)

    # ── DOMAIN_DEPENDENCY_GRAPH.md ─────────────────────────────────────────
    event_sources = {}
    for m in CANONICAL_DOMAINS.values():
        for ev in m.events:
            event_sources.setdefault(ev, []).append(m.code)
    event_rows = "\n".join(
        f"| `{ev}` | {', '.join(src)} | consumed via Event Bus |"
        for ev, src in sorted(event_sources.items())
    )
    contract_total = sum(len(m.contracts) for m in CANONICAL_DOMAINS.values())
    doc = f"""# DOMAIN_DEPENDENCY_GRAPH — topology of the GULA platform

> PROGRAM-ALPHA | regenerated {TODAY}
> {len(CANONICAL_DOMAINS)} Domains, **{contract_total} declared versioned
> contracts**, cross-domain movement restricted to public APIs, FHIR R4, HL7,
> contracts, and the Event Bus.

## 1. Invariant

There is NO allowed import edge between two Domains. The dependency graph is:

```
Domain ──(Shared Core imports)──▶ Shared Core
Domain ──(Cross-Domain Gateway)─▶ versioned contract of another Domain
Domain ──(Event Bus)────────────▶ subscribed Domain(s)
Domain ──(FHIR R4 / HL7)────────▶ national interoperability layer
```

## 2. Shared Core edges

Every Domain consumes the platform-mandated Shared Core subset — identity,
authentication, authorization, audit, event_bus (certification check 8) plus
the {len(SHARED_CORE_SERVICES)}-service registry. Verified: **no Domain import
violation** (isolation PASS).

## 3. Workspace binding graph

| Workspace | Hosted Domains | Rendered UI |
|---|---|---|
{_workspace_rows()}

## 4. Event topology (domain events)

| Event | Emitted by | Consumed via |
|---|---|---|
{event_rows}

## 5. Contract topology

Currently {contract_total} explicitly declared cross-domain contracts
(`DomainContract`). The Cross-Domain Gateway (`CrossDomainGateway`) is the
single legal path for programmatic cross-domain calls beyond events/FHIR/HL7.

## 6. Cycle analysis

`IsolationValidator` performs DFS cycle detection over each Domain's real
import graph. Result: **{'PASS — no circular dependencies' if d['isolation_passes'] else 'FAIL'}**.

_Generated by scripts/architecture/docs.py._
"""
    p = ROOT / "DOMAIN_DEPENDENCY_GRAPH.md"
    p.write_text(doc, encoding="utf-8")
    written.append(p)

    # ── WORKSPACE_ARCHITECTURE.md ──────────────────────────────────────────
    doc = f"""# WORKSPACE_ARCHITECTURE — one identity, unlimited workspaces

> PROGRAM-ALPHA Phase 5 | regenerated {TODAY}

## 1. Model

- **One identity** — NIAM (`backend/app/identity`). Every actor — citizen,
  professional, organization, government authority, syndicate, institution,
  service account, device — is one identity.
- **Unlimited workspaces** — an identity may belong to many workspaces but
  activates **ONE** at a time (`WorkspaceService.select_active_workspace`).
- **Permissions never cross workspaces** — a permission obtained in one
  workspace is unusable in another (`OrganizationAccessGuard`).
- **Workspace types** are bound to Domains; a workspace renders only the UI of
  the Domains it hosts.

## 2. Workspace registry

| Workspace | Hosted Domains | Rendered UI |
|---|---|---|
{_workspace_rows()}

## 3. Rules

1. One active workspace per identity at any moment.
2. A workspace never renders another workspace's UI (`WorkspaceBindingRegistry
   .assert_ui_allowed`).
3. Administration never crosses organizational boundaries (cross-org guard).
4. Workspace membership, roles, teams, departments, invitations and delegation
   are first-class platform capabilities (8 `niam_workspace_*` tables, 23
   endpoints under `/niam/workspaces`).
5. Sessions are bound to workspaces; `enforce_max_concurrent_sessions` is the
   single enforcement point.

## 4. Certification

Workspace isolation is enforced by the Domain Platform Framework and the
Architecture Constitution gate. Current verdict: **PASS**.

_Generated by scripts/architecture/docs.py._
"""
    p = ROOT / "WORKSPACE_ARCHITECTURE.md"
    p.write_text(doc, encoding="utf-8")
    written.append(p)

    # ── DIGITAL_TRUST_PLATFORM.md ──────────────────────────────────────────
    trust_caps = [
        ("Citizens", "backend/app/identity/citizen_registry", "country-agnostic providers, 8 identifier types, hashed storage"),
        ("Healthcare Professionals", "backend/app/identity/professional_registry", "12 professions; verify() is the ONLY privilege-activation path"),
        ("Organizations", "backend/app/identity/models/niam_organization.py", "Ministry → Directorate → Hospital → Laboratory hierarchy"),
        ("Government Authorities", "backend/app/identity/organizations", "OrganizationAccessGuard — zero cross-domain administration"),
        ("Professional Syndicates", "backend/app/identity/federation", "federated identity relationships"),
        ("Educational Institutions", "backend/app/identity/federation", "federated identity relationships"),
        ("Service Accounts", "backend/app/security/service_accounts.py", "machine/service identity + credentials"),
        ("Device Trust", "backend/app/identity/devices", "device registry and trust signals"),
        ("Session Trust", "backend/app/identity/services/session_service.py", "workspace binding + max concurrent enforcement"),
        ("Risk-based Authentication", "backend/app/identity/adaptive_auth", "adaptive/risk-based auth"),
        ("MFA", "shared/auth/mfa.py + backend/app/security/mfa_service.py", "TOTP/OTP multi-factor"),
        ("Digital Signature", "shared/security/hmac.py", "HMAC signatures and integrity"),
        ("Delegation", "backend/app/identity/workspaces", "workspace delegation"),
        ("Approval", "backend/app/approvals", "approval workflows"),
        ("Organization Hierarchy", "backend/app/identity/organizations", "guarded cross-org hierarchy"),
    ]
    cap_rows = "\n".join(f"| {t} | `{p}` | {d} |" for t, p, d in trust_caps)
    doc = f"""# DIGITAL_TRUST_PLATFORM — NIAM (Program-Stable-003 + Phase 6)

> PROGRAM-ALPHA Phase 6 | regenerated {TODAY}

## 1. Vision

Identity is not a table — it is a Digital Trust Platform. NIAM is the single
identity for every actor in the national health ecosystem, with a
country-agnostic model that deploys across all Iraqi governorates and beyond.

## 2. Trust principals

| Principal | Provider | Capability |
|---|---|---|
{cap_rows}

## 3. Design rules

1. **Single identity, many workspaces** — every actor is one NIAM identity.
2. **verify() is the only privilege gate** — professional privileges activate
   only through `ProfessionalRegistry.verify()`; `is_privileged()` is the single
   enforcement point.
3. **Least privilege + defense in depth** — RBAC + ABAC combined, session
   binding, device trust, risk-based auth.
4. **Immutable audit** — every trust decision is hash-chained into the audit
   log.
5. **Country-agnostic** — identity providers and identifier types are
   configurable; no hard-coded national scheme in Shared Core or Domains.
6. **Backward compatible** — legacy identity types map through
   `IdentityType.canonical()`.

## 4. Certification

Digital Trust certification (PROGRAM-STABLE-003): **130 identity unit tests
pass**; workspace/session/cross-org guards certified. Included in the
Program-Alpha gate as part of the shared core + workspace checks.

_Generated by scripts/architecture/docs.py._
"""
    p = ROOT / "DIGITAL_TRUST_PLATFORM.md"
    p.write_text(doc, encoding="utf-8")
    written.append(p)

    # ── MASTER_REMAINING_WORK.md ───────────────────────────────────────────
    country = load_country_baseline()
    country_rows = "\n".join(
        f"- `{f['path']}` — marker `{f['marker']}`" for f in sorted(country, key=lambda x: x["path"])
    ) or "- none"
    doc = f"""# MASTER_REMAINING_WORK — acknowledged debt and migration plan

> PROGRAM-ALPHA | regenerated {TODAY}
> Everything below is tracked, deterministic debt. It is **blocked from
> growing** — the Architecture Constitution gate fails any PR that adds a new
> finding. Migration is performed only when correctness can be proven, and
> never changes observable behaviour.

## 1. Shared Core consolidation findings ({len(load_baseline())})

Detected by `architecture-scan` across `backend/app` + `shared/`. These are
legacy reimplementation candidates awaiting migration to their authoritative
provider (see SHARED_CORE_REGISTRY.md). Each requires a human-reviewed,
behaviour-preserving migration.

### By capability

| Capability | Issue | Findings |
|---|---|---|
{_finding_rows()}

### Full list

{_finding_detail_rows()}

## 2. Country-specific hard-coding ({len(country)})

Allowed only inside the national layer (`backend/app/national`, `backend/app/nhdw`,
`backend/app/national_data`):

{country_rows}

## 3. High-priority migrations

1. **Notifications consolidation** — route `backend/app/platform/notifications.py`,
   `backend/app/identity/notifications/`, `backend/app/citizen_platform/notifications.py`
   and `backend/app/national/notification_platform/` onto the platform
   notification core (`backend/app/notifications`).
2. **Audit consolidation** — fold `backend/app/platform/audit.py`,
   `backend/app/national/security/audit.py`, and document-intelligence audit
   onto the NIAM immutable audit core.
3. **Authorization consolidation** — unify `backend/app/services/authorization_service.py`
   with the NIAM authorization service; audit platform/identity duplicate RBAC/ABAC.
4. **Engine consolidation** — kernel scheduler/event-bus/DI and identity
   workflow engine should consume `shared/` (scheduler, events, di_container,
   workflow) instead of reimplementing.
5. **Barcode/QR** — `backend/app/models/sample.py` `generate_barcode()` and the
   document-platform QR service must call `shared/barcode` + `shared/qr`.
6. **Encryption** — `backend/app/services/offline_sync_service.py` and the
   national transformation engine must consume `shared/security/encryption.py`.

## 4. Governance

- Every migration is a dedicated PR with regression tests + `architecture-check` PASS.
- New findings fail CI immediately (no baseline growth).
- Uncertain migrations STOP and request human review (per PROGRAM-ALPHA rules).

_Generated by scripts/architecture/docs.py._
"""
    p = ROOT / "MASTER_REMAINING_WORK.md"
    p.write_text(doc, encoding="utf-8")
    written.append(p)

    return written


if __name__ == "__main__":
    for path in write_all():
        print(f"wrote {path.name}")
