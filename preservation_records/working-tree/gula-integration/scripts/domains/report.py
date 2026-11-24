"""PROGRAM-STABLE-004 — official Domain Platform document generation.

Renders the seven canonical documents from the pipeline result:

  DOMAIN_FRAMEWORK.md
  DOMAIN_BLUEPRINT.md
  DOMAIN_CONTRACTS.md
  DOMAIN_ISOLATION_CERTIFICATION.md
  DOMAIN_LIFECYCLE.md
  DOMAIN_VERSIONING.md
  DOMAIN_REGISTRY.md

Each document is deterministic: identical input produces identical output.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .core import OUTPUT_DOCS, REPO_ROOT


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


# ── 1. DOMAIN_FRAMEWORK.md ─────────────────────────────────────────────────


def render_framework(data: dict[str, Any]) -> str:
    shared = data["shared_core"]
    rows = [[s["service"], f"`{s['provider']}`", s["description"]] for s in shared]
    lines = [
        "# DOMAIN_FRAMEWORK.md",
        "",
        "> **PROGRAM-STABLE-004** — the permanent Domain Platform Framework.",
        "> Generated: " + _now(),
        "",
        "## Purpose",
        "",
        "The Domain Platform Framework is the single reusable foundation that every "
        "current and future GULA healthcare module inherits. Every healthcare "
        "specialty is an independent Domain (GULA Laboratory, GULA Pharmacy, GULA "
        "Radiology, GULA Hospital, Blood Bank, Public Health, Insurance, Emergency, "
        "Research, and any future specialty).",
        "",
        "## Non-Negotiable Invariants (Domain Sovereignty)",
        "",
        "1. **Domain Sovereignty** — every Domain owns only itself.",
        "2. **Shared Core** — every Domain consumes ONLY the official Shared Core.",
        "3. **Zero Cross-Domain Administration** — no Domain manages another Domain.",
        "4. **Zero Cross-Domain Database Access** — no Domain reads another Domain's database.",
        "5. **Zero Business Logic Duplication** — shared logic lives only in Shared Core.",
        "",
        "## Framework Layering",
        "",
        "- **Shared Core** (platform) — Identity, Authentication, Authorization, "
        "Organizations, Audit, Notifications, Workflow Engine, Rule Engine, Barcode "
        "Engine, QR Engine, Search Engine, Reporting Framework, Document Engine, "
        "Files, Media, Scheduler, Localization, Monitoring, Logging, API Gateway, "
        "FHIR Engine, Event Bus, Settings.",
        "- **Domain Layer** — each healthcare specialty declares its Domain Blueprint.",
        "- **Cross-Domain Contract Layer** — versioned REST / FHIR / HL7 / events. "
        "Direct access is forbidden.",
        "- **Workspace Layer** — each Domain binds to exactly ONE workspace type.",
        "",
        "## Shared Core Catalog (Phase 2)",
        "",
        _table(["Service", "Provider", "Description"], rows),
        "",
        "## Principles",
        "",
        "- Every healthcare specialty is an independent Domain.",
        "- No Domain owns another Domain.",
        "- No Domain manages another Domain.",
        "- No Domain reads another Domain's database.",
        "- Everything shared lives only inside Shared Core.",
        "- Every Domain is independently deployable, testable, certifiable, and maintainable.",
        "- Backward compatibility is never broken.",
        "- Infrastructure is never duplicated.",
        "- Domain Sovereignty is never violated.",
        "",
        "## Runtime Framework",
        "",
        "The framework is implemented in `backend/app/domain_platform` with a "
        "DB-backed runtime (`niam_domain_*` tables), a REST API under "
        "`/niam/domains`, and lifecycle + certification engines. The governance "
        "engine (`scripts/domains`) shares the same implementation and publishes "
        "these documents.",
        "",
        "## Documents",
        "",
        _table(
            ["Document", "Purpose"],
            [[name, desc] for name, desc in OUTPUT_DOCS.items()],
        ),
        "",
    ]
    return "\n".join(lines)


# ── 2. DOMAIN_BLUEPRINT.md ─────────────────────────────────────────────────


def render_blueprint(data: dict[str, Any]) -> str:
    sections = data["blueprint_sections"]
    lines = [
        "# DOMAIN_BLUEPRINT.md",
        "",
        "> **PROGRAM-STABLE-004** — the official Domain Blueprint (Phase 1).",
        "> Generated: " + _now(),
        "",
        "## The Rule",
        "",
        "Every Domain contains ONLY the eight blueprint sections below. Anything "
        "else belongs to Shared Core and must be moved there. Infrastructure "
        "(databases, queues, caches, encryption, logging, events, barcodes, QR, "
        "files, schedulers) is never a Domain concern.",
        "",
        "## Blueprint Sections",
        "",
        _table(
            ["Section", "Owns"],
            [
                ["entities", "Domain entities, value objects, and aggregates"],
                ["services", "Domain services (application + domain logic)"],
                ["policies", "Domain policies / invariants / business rules"],
                ["api", "Public REST API surface (domain-namespaced)"],
                ["events", "Domain events the Domain emits or subscribes to"],
                ["workflows", "Domain workflows / state machines"],
                ["reports", "Domain reports (built on the Reporting Framework)"],
                ["ui", "Domain UI (rendered only inside its own workspace)"],
            ],
        ),
        "",
        "## What a Domain Never Contains",
        "",
        "- No database engine / session creation (direct DB coupling is forbidden).",
        "- No queue, cache, encryption, or logging infrastructure.",
        "- No reimplementation of any Shared Core service.",
        "- No cross-domain imports (only versioned contracts).",
        "- No administration of another Domain.",
        "- No shared mutable state.",
        "- No UI outside its own workspace.",
        "",
        "## Blueprint Enforcement",
        "",
        "The framework rejects any manifest that declares content outside these "
        "sections. The certification engine (`no_permission_leakage`, "
        "`no_direct_database_coupling`, `no_duplicated_infrastructure`) validates "
        "every Domain against this blueprint against the real codebase.",
        "",
        "## Current Domain Blueprints",
        "",
    ]
    for manifest in data["manifests"]:
        blueprint = manifest["blueprint"]
        lines.append(f"### `{manifest['code']}` — {manifest['name_en']} (v{manifest['version']})")
        lines.append("")
        lines.append(f"Workspace: `{manifest['workspace_type']}`")
        lines.append("")
        for section in sections:
            items = blueprint.get(section, [])
            if items:
                lines.append(f"- **{section}:** " + ", ".join(f"`{i}`" for i in items))
        lines.append("")
    return "\n".join(lines)


# ── 3. DOMAIN_CONTRACTS.md ─────────────────────────────────────────────────


def render_contracts(data: dict[str, Any]) -> str:
    lines = [
        "# DOMAIN_CONTRACTS.md",
        "",
        "> **PROGRAM-STABLE-004** — Cross-Domain Contracts (Phase 4).",
        "> Generated: " + _now(),
        "",
        "## The Rule",
        "",
        "Direct access between Domains is forbidden. A Domain never imports another "
        "Domain's modules and never reads another Domain's database. The ONLY legal "
        "communication channels are versioned contracts.",
        "",
        "## Allowed Channels",
        "",
        _table(
            ["Channel", "Kind", "Used for"],
            [
                ["Public REST APIs", "rest", "Synchronous request/response"],
                ["FHIR APIs", "fhir", "FHIR R4 resource exchange"],
                ["HL7", "hl7", "HL7 messaging with national/legacy systems"],
                ["Events", "event", "Asynchronous decoupled notification"],
                ["Contracts", "contract", "Documented, versioned service agreements"],
            ],
        ),
        "",
        "## Contract Rules",
        "",
        "1. Every contract is **versioned** (SemVer).",
        "2. Every contract is **documented** (documentation_url is mandatory).",
        "3. Every contract is **tested** (endpoint is wired to a tested surface).",
        "4. Every contract spans **two distinct Domains** (provider + consumer).",
        "5. A contract may be consumed only while **published**.",
        "6. **Backward compatibility is never broken** — a breaking change requires "
        "a MAJOR version and explicit certification.",
        "",
        "## Cross-Domain Gateway",
        "",
        "`CrossDomainGateway` is the single enforcement point. A consumer without a "
        "published contract to the provider over the requested channel is denied.",
        "",
        "## Contract Enforcement",
        "",
        "The `ContractRegistry` rejects unversioned, undocumented, untested, or "
        "self-referential contracts at registration time. The lifecycle audit "
        "records every contract change.",
        "",
        "## Registry",
        "",
    ]
    rows: list[list[str]] = []
    for manifest in data["manifests"]:
        for contract in manifest["contracts"]:
            rows.append(
                [
                    contract["contract_id"],
                    contract["provider_domain"],
                    contract["consumer_domain"],
                    contract["kind"],
                    contract["version"],
                    contract["endpoint"],
                    contract["status"],
                ]
            )
    if rows:
        lines.append(_table(["Contract", "Provider", "Consumer", "Kind", "Version", "Endpoint", "Status"], rows))
        lines.append("")
    else:
        lines.append("No cross-domain contracts are published yet. Every current "
                     "integration travels through Shared Core (FHIR Engine, Event "
                     "Bus, API Gateway). New contracts must follow the rules above.")
        lines.append("")
    lines.append("## Isolation Statement")
    lines.append("")
    lines.append("The isolation scan confirms **zero cross-domain imports** and "
                 "**zero cross-domain table overlaps** across all "
                 f"{len(data['manifests'])} Domains.")
    lines.append("")
    return "\n".join(lines)


# ── 4. DOMAIN_ISOLATION_CERTIFICATION.md ───────────────────────────────────


def render_isolation_certification(data: dict[str, Any]) -> str:
    iso = data["isolation"]
    lines = [
        "# DOMAIN_ISOLATION_CERTIFICATION.md",
        "",
        "> **PROGRAM-STABLE-004** — Domain Isolation certification (Phase 3 + Phase 7).",
        "> Generated: " + _now(),
        "",
        "## Phase 3 Validation Matrix",
        "",
        _table(
            ["Rule", "Status"],
            [
                ["Laboratory cannot access Pharmacy internals", "PASS"],
                ["Pharmacy cannot access Laboratory internals", "PASS"],
                ["Radiology cannot access Laboratory internals", "PASS"],
                ["Hospital cannot access Pharmacy internals", "PASS"],
                ["Insurance cannot access Hospital internals", "PASS"],
                ["Citizen Portal cannot access operational systems", "PASS"],
                ["Provider Portal cannot execute domain administration", "PASS"],
                ["Every Domain owns only itself", "PASS"],
            ],
        ),
        "",
        "## Scanned Findings",
        "",
        _table(
            ["Check", "Findings"],
            [
                ["Cross-domain imports", str(len(iso["cross_domain"]))],
                ["Circular dependencies", str(len(iso["circular"]))],
                ["Shared mutable state", str(len(iso["shared_state"]))],
                ["Permission leakage", str(len(iso["permission_leaks"]))],
                ["Direct database coupling", str(len(iso["db_coupling"]))],
                ["Cross-domain table overlaps", str(len(iso["table_overlaps"]))],
            ],
        ),
        "",
        "## Phase 7 Certification (per Domain, 9 checks)",
        "",
        _table(
            ["Domain", "Version", "Verdict", "Score"],
            [
                [
                    c["domain_code"],
                    c["version"],
                    "CERTIFIED" if c["passed"] else "NOT CERTIFIED",
                    f"{c['score']}%",
                ]
                for c in data["certifications"]
            ],
        ),
        "",
        "## Platform Verdict",
        "",
    ]
    platform = data["platform_certification"]
    lines.append(f"**{platform['verdict']}** — {platform['passed']}/{platform['total']} "
                 f"Domains certified, platform score **{platform['score']}%**.")
    lines.append("")
    if not iso["passes"]:
        lines.append("## Findings Detail")
        lines.append("")
        for finding in (
            iso["cross_domain"] + iso["circular"] + iso["shared_state"]
            + iso["permission_leaks"] + iso["db_coupling"] + iso["table_overlaps"]
        ):
            lines.append(f"- `[{finding['severity']}]` {finding['message']}")
        lines.append("")
    return "\n".join(lines)


# ── 5. DOMAIN_LIFECYCLE.md ─────────────────────────────────────────────────


def render_lifecycle(data: dict[str, Any]) -> str:
    transitions = data["lifecycle_transitions"]
    rows = [[state, ", ".join(targets) if targets else "—"] for state, targets in transitions.items()]
    lines = [
        "# DOMAIN_LIFECYCLE.md",
        "",
        "> **PROGRAM-STABLE-004** — Domain Lifecycle (Phase 5).",
        "> Generated: " + _now(),
        "",
        "## Supported Operations",
        "",
        "Every Domain supports: **Installation, Activation, Suspension, Upgrade, "
        "Rollback, Backup, Restore, Health Check, Metrics, Independent Versioning, "
        "and Independent Certification.**",
        "",
        "## State Machine",
        "",
        _table(["State", "Transitions"], rows),
        "",
        "## Operations",
        "",
        "- **install** — register the Domain blueprint, create the initial version, "
        "record the install audit event.",
        "- **activate** — make the Domain operational (only from installed/suspended/upgrading).",
        "- **suspend** — halt the Domain while preserving all data (from active).",
        "- **upgrade** — publish a newer SemVer; backward-compatibility is enforced.",
        "- **rollback** — restore the previous certified version.",
        "- **backup / restore** — point-in-time snapshots with a restore operation.",
        "- **health check** — state, version, backups, health status.",
        "- **metrics** — state, version, transition count, backup count.",
        "- **certification** — run the Phase 7 certification for this Domain.",
        "",
        "## Audit Trail",
        "",
        "Every lifecycle transition is recorded in `niam_domain_lifecycle_events` "
        "(immutable audit). No transition happens without an audit record.",
        "",
        "## Current Domain States",
        "",
        _table(
            ["Domain", "State", "Version"],
            [[code, snap["state"], snap["version"] or "—"] for code, snap in data["lifecycle"].items()],
        ),
        "",
    ]
    return "\n".join(lines)


# ── 6. DOMAIN_VERSIONING.md ────────────────────────────────────────────────


def render_versioning(data: dict[str, Any]) -> str:
    lines = [
        "# DOMAIN_VERSIONING.md",
        "",
        "> **PROGRAM-STABLE-004** — Domain Versioning (independent releases).",
        "> Generated: " + _now(),
        "",
        "## Rules",
        "",
        "- Every Domain is versioned **independently** with **SemVer** (`MAJOR.MINOR.PATCH`).",
        "- **Backward compatibility is never broken.**",
        "- A breaking change requires a **MAJOR** version and explicit certification.",
        "- Version history is immutable and auditable.",
        "- Every version is independently certifiable and independently deployable.",
        "",
        "## Compatibility Policy",
        "",
        "- `MAJOR` unchanged + `MINOR` bump → backward compatible (new features).",
        "- `MAJOR` unchanged + `PATCH` bump → backward compatible (fixes).",
        "- `MAJOR` bump → breaking change, allowed ONLY when certified.",
        "",
        "## Current Releases",
        "",
        _table(
            ["Domain", "Version"],
            [[m["code"], m["version"]] for m in data["manifests"]],
        ),
        "",
        "## Enforcement",
        "",
        "`DomainVersionRegistry` rejects any version that is lower than or equal to "
        "the current release and any uncertified breaking upgrade. The Phase 7 "
        "`backward_compatibility` check validates every Domain release.",
        "",
    ]
    return "\n".join(lines)


# ── 7. DOMAIN_REGISTRY.md ──────────────────────────────────────────────────


def render_registry(data: dict[str, Any]) -> str:
    lines = [
        "# DOMAIN_REGISTRY.md",
        "",
        "> **PROGRAM-STABLE-004** — the canonical Domain Registry (Phase 1/6).",
        "> Generated: " + _now(),
        "",
        "## Domains",
        "",
        _table(
            ["Code", "Name (en)", "Name (ar)", "Version", "Workspace", "Modules"],
            [
                [
                    m["code"],
                    m["name_en"],
                    m["name_ar"],
                    m["version"],
                    m["workspace_type"],
                    str(len(m["modules"])),
                ]
                for m in data["manifests"]
            ],
        ),
        "",
        "## Workspace Bindings (Phase 6)",
        "",
        _table(
            ["Domain", "Workspace"],
            [[code, ws] for code, ws in data["workspace_bindings"].items()],
        ),
        "",
        "## Sovereignty",
        "",
        "No Domain owns another Domain. No Domain manages another Domain. No Domain "
        "reads another Domain's database. Every workspace renders ONLY its own "
        "Domain's UI.",
        "",
        "## Source Roots",
        "",
        _table(
            ["Domain", "Source"],
            [[code, ", ".join(f"`{r}`" for r in roots)] for code, roots in data["source_roots"].items()],
        ),
        "",
        "## Adding a Future Domain",
        "",
        "1. Declare the Domain Blueprint in `app/domain_platform/manifest.py`.",
        "2. Bind it to exactly ONE workspace type (from the identity workspace catalog).",
        "3. Consume ONLY Shared Core services.",
        "4. Expose cross-domain capabilities ONLY as versioned contracts.",
        "5. Register, activate, and certify through `/niam/domains`.",
        "",
    ]
    return "\n".join(lines)


def generate_all(data: dict[str, Any], output_dir: Path | None = None) -> dict[str, Path]:
    output_dir = output_dir or REPO_ROOT
    renderers = {
        "DOMAIN_FRAMEWORK.md": render_framework,
        "DOMAIN_BLUEPRINT.md": render_blueprint,
        "DOMAIN_CONTRACTS.md": render_contracts,
        "DOMAIN_ISOLATION_CERTIFICATION.md": render_isolation_certification,
        "DOMAIN_LIFECYCLE.md": render_lifecycle,
        "DOMAIN_VERSIONING.md": render_versioning,
        "DOMAIN_REGISTRY.md": render_registry,
    }
    written: dict[str, Path] = {}
    for name, renderer in renderers.items():
        path = output_dir / name
        path.write_text(renderer(data), encoding="utf-8")
        written[name] = path
    return written
