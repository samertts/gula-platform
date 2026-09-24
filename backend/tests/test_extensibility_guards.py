"""PROGRAM-EXT-001 — the nine guards, and the synthetic extension that proves the contract.

These exist so that the rules in docs/architecture/extensibility/ are enforced
rather than remembered. Two design choices run through all of them:

**A guard that fails on its first run gets deleted.** Where the estate already
violates a rule — and it does, in two places — the guard is a *ledger* in the
shape NR-044 established: the existing violations are recorded with their
counts, and the guard fails when a new one appears or an existing one grows.
Frozen, visible debt beats a gate that nobody can turn on.

**UNKNOWN is never VERIFIED.** Nothing here imports `app/capabilities/`, because
nine of those ten packages raise `ModuleNotFoundError` (NR-050); a guard that
swallowed that would report a clean estate it had not measured. The guards work
from the registry that actually loads, and from AST over source.
"""

from __future__ import annotations

import ast
import collections
import pathlib

import pytest
from app.kernel.capabilities_registry_populator import _get_all_descriptors
from app.kernel.extensibility import (
    GRANDFATHERED,
    REQUIRED_FIELDS,
    GlobalIntelligenceEntry,
    load_global_intelligence,
    validate_descriptor,
    validate_registry,
)
from app.kernel.types import (
    CapabilityAudit,
    CapabilityDeprecation,
    CapabilityDescriptor,
    CapabilityEvent,
    CapabilityMaturity,
    CapabilityStatus,
    FeatureFlagClass,
    TenantScope,
)

APP = pathlib.Path(__file__).resolve().parents[1] / "app"

# ── Shared AST helpers ────────────────────────────────────────────────────────


def _imports(path: pathlib.Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
        elif isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
    return found


def _python_files(root: pathlib.Path):
    for path in root.rglob("*.py"):
        if "__pycache__" not in path.parts:
            yield path


# ── Guard 1: a domain may not import another domain's internals ───────────────

DOMAINS = frozenset({
    "pharmacy", "nursing", "blood_bank", "radiology", "lims", "ems",
    "critical_care", "public_health", "biomedical", "hospital", "clinical",
    "ehr", "care_continuum", "national", "national_data", "nhdw", "insurance",
    "payments", "financial",
})

#: Package segments that are a domain's *inside*. A domain's routes and its
#: published contracts are fair game; its ORM rows, repositories and internal
#: application services are not.
_INTERNAL_SEGMENTS = frozenset({
    "models", "domain", "application", "infrastructure", "repositories", "repository",
})

#: Measured, not asserted. Every edge here is an existing violation, frozen so
#: it cannot grow. See docs/architecture/extensibility/core-boundary.md §3 for
#: why two of these read as a split bounded context and one reads as genuine
#: coupling.
DECLARED_CROSS_DOMAIN_EDGES: dict[tuple[str, str], int] = {
    ("national_data", "national"): 10,
    ("national", "ehr"): 6,
    ("nursing", "ehr"): 3,
    ("national_data", "ehr"): 3,
    ("payments", "financial"): 2,
    ("national", "lims"): 1,
}


def _cross_domain_edges() -> dict[tuple[str, str], int]:
    edges: collections.Counter = collections.Counter()
    for domain in sorted(DOMAINS):
        root = APP / domain
        if not root.exists():
            continue
        for path in _python_files(root):
            for module in _imports(path):
                if not module.startswith("app."):
                    continue
                parts = module.split(".")
                if len(parts) < 3:
                    continue
                other = parts[1]
                if other == domain or other not in DOMAINS:
                    continue
                if any(segment in _INTERNAL_SEGMENTS for segment in parts[2:]):
                    edges[(domain, other)] += 1
    return dict(edges)


def test_no_new_cross_domain_internal_dependency_appears() -> None:
    """Guard 1. A domain reading another domain's internals is coupled to its
    migration schedule: the moment the other team renames a column, a domain
    they have never heard of breaks. NR-047 is what that costs when it happens.

    Twenty-five such imports already exist along six edges. They are frozen
    here rather than forgiven: a new edge, or an existing edge growing, fails.
    """
    actual = _cross_domain_edges()

    new_edges = sorted(set(actual) - set(DECLARED_CROSS_DOMAIN_EDGES))
    assert not new_edges, (
        f"{new_edges} newly import another domain's internals. Depend on a Core "
        "contract, a versioned API, or a published event instead — see "
        "docs/architecture/extensibility/domain-contract.md §2."
    )

    grown = {
        edge: (DECLARED_CROSS_DOMAIN_EDGES[edge], count)
        for edge, count in actual.items()
        if count > DECLARED_CROSS_DOMAIN_EDGES[edge]
    }
    assert not grown, f"existing cross-domain coupling grew (declared, actual): {grown}"

    healed = sorted(set(DECLARED_CROSS_DOMAIN_EDGES) - set(actual))
    assert not healed, (
        f"{healed} no longer cross domain internals — good. Remove them from "
        "DECLARED_CROSS_DOMAIN_EDGES so the ledger keeps its meaning."
    )


# ── Guards 2-3: identity is unique ────────────────────────────────────────────


def test_no_two_capabilities_declare_the_same_id_or_name() -> None:
    """Guard 2. Two capabilities answering to one name is indistinguishable to
    a consumer, and the registry is a dict keyed by name — so the second simply
    replaces the first, silently.
    """
    descriptors = _get_all_descriptors()

    names = collections.Counter(d.name for d in descriptors)
    duplicate_names = {n: c for n, c in names.items() if c > 1}
    assert not duplicate_names, f"duplicate capability names: {duplicate_names}"

    ids = collections.Counter(d.capability_id for d in descriptors if d.capability_id)
    duplicate_ids = {i: c for i, c in ids.items() if c > 1}
    assert not duplicate_ids, f"duplicate capability_ids: {duplicate_ids}"


def test_no_two_capabilities_declare_the_same_event_name() -> None:
    """Guard 3. Event names are the platform's public vocabulary. Two
    capabilities publishing `document.created` with different payloads cannot be
    told apart by a consumer, and the second one to arrive wins by timing.
    """
    owners: dict[str, list[str]] = collections.defaultdict(list)
    for descriptor in _get_all_descriptors():
        for event in descriptor.events:
            owners[event.name].append(descriptor.name)
    contested = {name: sorted(set(who)) for name, who in owners.items() if len(set(who)) > 1}
    assert not contested, f"event names claimed by more than one capability: {contested}"


# ── Guards 4-7: the contract itself ───────────────────────────────────────────


def test_every_new_capability_declares_the_required_metadata() -> None:
    """Guard 4. The 52 that predate the contract are grandfathered by name;
    anything else must declare it.

    All 52 fail on the same four fields — capability_id, documentation,
    test_paths, module_path — which is the finding rather than an accident: the
    registry points at no code, no tests and no docs, so nothing it says can be
    checked against reality.
    """
    report = validate_registry(_get_all_descriptors())
    offenders = {name: violations for name, violations in report.items() if name not in GRANDFATHERED}
    assert not offenders, (
        "capabilities registered without the required metadata: "
        f"{offenders}. See docs/architecture/extensibility/capability-contract.md"
    )


def test_the_grandfathered_debt_never_grows() -> None:
    """Guard 4b. The exemption is a fixed list, not a policy.

    Without this, `GRANDFATHERED` becomes the place incomplete descriptors go to
    be forgiven, and the contract quietly stops applying to anything.
    """
    registered = {d.name for d in _get_all_descriptors()}
    assert registered >= GRANDFATHERED, (
        f"{sorted(GRANDFATHERED - registered)} are grandfathered but no longer "
        "registered — remove them from GRANDFATHERED"
    )
    assert len(GRANDFATHERED) == 52, (
        f"GRANDFATHERED holds {len(GRANDFATHERED)} entries, not the 52 recorded when "
        "the contract was written. It may only shrink."
    )


def test_a_capability_handling_sensitive_data_declares_an_audit_trail() -> None:
    """Guard 5/6. The one rule here that is a safety property.

    A capability that touches CLINICAL_SENSITIVE, PII or RESTRICTED data and
    does not declare that it writes audit is a finding, not a configuration.
    """
    for descriptor in _get_all_descriptors():
        if descriptor.audit.data_classification in {"CLINICAL_SENSITIVE", "PII", "RESTRICTED"}:
            assert descriptor.audit.writes_audit, (
                f"{descriptor.name} handles {descriptor.audit.data_classification} "
                "data but declares no audit trail"
            )


def test_every_capability_declares_a_tenant_scope_and_a_maturity() -> None:
    """Guard 5/7. Tenancy is the one property a signature never shows, and
    maturity is how much evidence stands behind the thing. Both are typed, so a
    string that looks right cannot pass.
    """
    for descriptor in _get_all_descriptors():
        assert isinstance(descriptor.tenant_scope, TenantScope), (
            f"{descriptor.name} has a tenant_scope that is not a TenantScope"
        )
        assert isinstance(descriptor.maturity, CapabilityMaturity), (
            f"{descriptor.name} has a maturity that is not a CapabilityMaturity"
        )


def test_a_capability_with_a_public_api_declares_its_authorization() -> None:
    """Guard 5. An endpoint with no declared permission is either public or
    unreviewed, and the descriptor cannot tell you which.

    Scoped to capabilities registered after the contract. Right now that set is
    empty, so this passes vacuously — stated plainly rather than counted as
    evidence. What it does today is stop the first new capability from shipping
    an unstated authorization surface; the synthetic extension exercises it for
    real.
    """
    new_capabilities = [d for d in _get_all_descriptors() if d.name not in GRANDFATHERED]
    for descriptor in new_capabilities:
        if any(api.auth_required for api in descriptor.api_endpoints):
            assert descriptor.required_permissions, (
                f"{descriptor.name} publishes authenticated endpoints but declares "
                "no required_permissions"
            )

    # The synthetic extension is the non-vacuous half.
    assert _synthetic().required_permissions


def test_a_deprecated_capability_names_its_replacement() -> None:
    """Guard 7. A capability that disappears without naming a successor breaks
    every consumer at once and tells none of them where to go.
    """
    for descriptor in _get_all_descriptors():
        if descriptor.maturity in {CapabilityMaturity.DEPRECATED, CapabilityMaturity.RETIRED}:
            assert descriptor.deprecation.is_declared(), (
                f"{descriptor.name} is {descriptor.maturity.value} but declares no "
                "since_version/removal_version/replacement"
            )


def test_a_public_contract_is_versioned() -> None:
    """Guard 7. Every capability carries a version, and every declared API path
    is explicitly versioned. GULA has mobile clients it does not control; an
    unversioned public route is a promise it cannot keep.
    """
    for descriptor in _get_all_descriptors():
        assert descriptor.version, f"{descriptor.name} declares no version"
        for api in descriptor.api_endpoints:
            if api.path.startswith("/api/"):
                assert "/v" in api.path, (
                    f"{descriptor.name} publishes {api.path} with no explicit version"
                )


# ── Guard 8: a flag is never an authorization decision ────────────────────────

_FLAG_CALLS = frozenset({
    "is_enabled", "visits_enabled", "national_id_enabled", "can_lab_access",
    "is_feature_enabled", "feature_enabled",
})

#: The paths where an authorization decision is actually made. A feature-flag
#: call inside one of these would mean availability standing in for permission.
_AUTHORIZATION_PATHS = (
    APP / "identity" / "services" / "authorization_decision.py",
    APP / "identity" / "services" / "authorization_service_v2.py",
    APP / "identity" / "services" / "clinical_authorization_context_service.py",
    APP / "identity" / "policy_engine.py",
    APP / "clinical_gateway" / "service.py",
    APP / "clinical_gateway" / "context.py",
)


def test_a_feature_flag_is_never_an_authorization_decision() -> None:
    """Guard 8. Flags answer "is this present?"; authorization answers "may this
    actor?".

    Substituting one for the other fails in both directions: turning a flag on
    grants everyone access, and turning it off hides a control failure behind an
    availability decision.
    """
    offenders: list[str] = []
    for path in _AUTHORIZATION_PATHS:
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = None
            if isinstance(node.func, ast.Attribute):
                name = node.func.attr
            elif isinstance(node.func, ast.Name):
                name = node.func.id
            if name in _FLAG_CALLS:
                offenders.append(f"{path.name}:{node.lineno} calls {name}()")
    assert offenders == [], (
        f"{offenders} — a feature flag is being consulted inside an authorization "
        "path. Server authorization is authoritative; see "
        "docs/architecture/extensibility/module-lifecycle.md §6.3"
    )


# ── Guard 9: do not duplicate a canonical capability ──────────────────────────

#: Concepts with a canonical owner. A *new* capability claiming one of these
#: names is duplication; the existing duplicates are listed in
#: docs/architecture/extensibility/reusable-capabilities.md and are a decision,
#: not something a test can resolve.
CANONICAL_CONCEPTS: dict[str, str] = {
    "audit": "app.identity.services.canonical_audit.CanonicalAuditService",
    "identity": "app.identity",
    "authentication": "app.identity.services.authentication_service",
    "authorization": "app.identity.services.authorization_decision",
    "verification": "app.identity.services.verification_workflow",
    "export": "app.platform.export",
    "search": "app.platform.search",
}

#: Names already registered that collide with a canonical concept. Recorded
#: because they exist, not because they are approved — each one is a
#: CONSOLIDATE decision in reusable-capabilities.md §5.
KNOWN_CONCEPT_COLLISIONS = frozenset({
    "audit_logging", "authentication", "authorization_rbac", "national_identity",
    "search_service",
})


def test_a_new_capability_does_not_duplicate_a_canonical_one() -> None:
    """Guard 9. Reuse Before Build, enforced at the point a capability is named.

    Four notification services means four places a national alert can silently
    fail to send and no single place to look. This blocks the fifth.
    """
    registered = {d.name for d in _get_all_descriptors()}
    suspects = {
        name for name in registered
        if any(concept in name for concept in CANONICAL_CONCEPTS)
    }
    unexpected = sorted(suspects - KNOWN_CONCEPT_COLLISIONS)
    assert not unexpected, (
        f"{unexpected} name a concept that already has a canonical owner "
        f"({CANONICAL_CONCEPTS}). Reuse it, or record the decision in "
        "docs/architecture/extensibility/reusable-capabilities.md first."
    )


# ── The canonical registry stays canonical ────────────────────────────────────


def test_no_new_code_registers_with_the_parallel_platform_registry() -> None:
    """`PlatformRegistry` is an untyped parallel store of the capability idea.

    It is not deleted — that would be unrelated remediation — but its use is
    frozen at the modules that already do it, so the canonical registry stays
    the one that matters.
    """
    users = sorted(
        path.relative_to(APP).as_posix()
        for path in _python_files(APP)
        if "PlatformRegistry" in path.read_text(encoding="utf-8", errors="ignore")
    )
    # All sixteen are app/platform's own modules registering themselves at
    # import, which is that package's design. The line being held is that
    # nothing *outside* app/platform may use it.
    outsiders = [u for u in users if not u.startswith("platform/")]
    assert outsiders == [], (
        f"PlatformRegistry is used outside app/platform/: {outsiders}. New "
        "capabilities register with kernel.runtime.capability_registry."
        "CapabilityRegistry — see docs/architecture/extensibility/core-boundary.md §5"
    )
    assert len(users) == 16, (
        f"app/platform grew to {len(users)} self-registering modules. That is the "
        "parallel registry expanding; add the capability to the canonical one."
    )


def test_the_capability_registry_still_loads_at_boot() -> None:
    """The contract is worth nothing if the registry it describes is not live."""
    bootloader = (APP / "kernel" / "runtime" / "bootloader.py").read_text(encoding="utf-8")
    assert "populate_registry" in bootloader, (
        "the capability registry is no longer populated at boot; the contract "
        "would describe something that never loads"
    )
    assert len(_get_all_descriptors()) >= 52


# ── PROGRAM-GLOBAL-001 foundation ─────────────────────────────────────────────


class TestGlobalIntelligence:
    """The structure exists and validates; the sweep has deliberately not run."""

    def test_the_registry_file_parses_and_every_entry_validates(self) -> None:
        for entry in load_global_intelligence():
            assert not entry.violations(), f"{entry.entry_id}: {entry.violations()}"

    def test_an_adopt_verdict_cannot_rest_on_anecdote(self) -> None:
        """The rule the registry exists to enforce.

        A strong recommendation on weak evidence is how a rumour becomes a
        roadmap item, so the two judgements are recorded separately and this
        combination is a violation rather than a warning.
        """
        weak = GlobalIntelligenceEntry(
            entry_id="probe", source="a conference hallway", country="XX",
            system="Something", domain="lab", evidence_quality="ANECDOTAL",
            licence="unknown", recommendation="ADOPT",
        )
        assert any("anecdotal" in v for v in weak.violations())

    def test_a_missing_licence_is_a_violation(self) -> None:
        """Free First and No Vendor Lock-In cannot be applied to something whose
        licence nobody wrote down."""
        entry = GlobalIntelligenceEntry(
            entry_id="probe", source="published report", country="XX",
            system="Something", domain="lab", evidence_quality="OFFICIAL_REPORT",
            recommendation="ADAPT",
        )
        assert any("licence" in v for v in entry.violations())


# ── Phase 13: the synthetic extension ─────────────────────────────────────────


def _synthetic() -> CapabilityDescriptor:
    """A complete, contract-satisfying capability — built in memory only.

    Deliberately not written to `app/`. A synthetic business implementation in
    the source tree is code that looks finished, does nothing, and gets copied:
    `app/capabilities/` already holds 267 modules of largely that, nine packages
    of which do not import (NR-050). This proves the contract without leaving
    another corpse.
    """
    return CapabilityDescriptor(
        capability_id="cap.synthetic.referral_echo",
        name="synthetic_referral_echo",
        version="1.2.0",
        owner="platform-architecture",
        description="A template-shaped capability used to prove the extension contract.",
        domain="clinical",
        status=CapabilityStatus.DRAFT,
        maturity=CapabilityMaturity.EXPERIMENTAL,
        flag_class=FeatureFlagClass.EXPERIMENTAL,
        feature_flag="ENABLE_SYNTHETIC_REFERRAL_ECHO",
        tenant_scope=TenantScope.TENANT,
        dependencies=["audit_logging", "authorization_rbac"],
        required_permissions=["referrals.read"],
        required_context=["tenant_id", "actor_account_id", "facility_id"],
        events=[CapabilityEvent(name="synthetic.referral_echoed", version=1)],
        data_contracts=["SyntheticReferralEcho"],
        audit=CapabilityAudit(
            writes_audit=True,
            audit_service="app.identity.services.canonical_audit.CanonicalAuditService",
            data_classification="CLINICAL_SENSITIVE",
            retention_days=3650,
        ),
        configuration={"echo_limit": 50},
        fhir_mappings={"ServiceRequest": "referral"},
        module_path="app/clinical/synthetic_referral_echo",
        documentation=["docs/architecture/extensibility/extension-template.md"],
        test_paths=["backend/tests/test_extensibility_guards.py"],
    )


class TestSyntheticExtension:
    """Phase 13 — the ten properties a real extension must demonstrate.

    None of this touches production clinical data: the descriptor is metadata,
    the registry instance is local to the test, and nothing is registered into
    the running kernel.
    """

    def test_1_it_registers_in_the_canonical_registry(self) -> None:
        from app.kernel.runtime.capability_registry import CapabilityRegistry

        registry = CapabilityRegistry()
        registry.register(_synthetic())
        assert registry.has("synthetic_referral_echo")
        assert registry.get("synthetic_referral_echo").capability_id == "cap.synthetic.referral_echo"

    def test_2_it_is_versioned(self) -> None:
        assert _synthetic().version == "1.2.0"

    def test_3_it_declares_its_dependencies(self) -> None:
        assert _synthetic().dependencies == ["audit_logging", "authorization_rbac"]

    def test_4_it_declares_authorization(self) -> None:
        descriptor = _synthetic()
        assert descriptor.required_permissions == ["referrals.read"]
        assert "actor_account_id" in descriptor.required_context

    def test_5_it_declares_the_events_it_publishes(self) -> None:
        """And the canonical envelope carries what a consumer needs, so the
        consumer never has to read this capability's tables to find out."""
        from app.kernel.event_bus.events import Event

        declared = _synthetic().events[0]
        published = Event(
            name=declared.name,
            version=declared.version,
            data={"referral_id": "ref-1"},
            source="synthetic_referral_echo",
            tenant_id="tenant-1",
            actor_id="acct-1",
            actor_type="account",
            resource_type="referral",
            resource_id="ref-1",
            provenance={"capability": "synthetic_referral_echo", "release": "1.2.0"},
        )
        assert published.id and published.timestamp
        assert published.tenant_id and published.actor_id and published.resource_id

    def test_6_it_declares_its_audit_obligation(self) -> None:
        audit = _synthetic().audit
        assert audit.writes_audit
        assert audit.data_classification == "CLINICAL_SENSITIVE"
        assert "CanonicalAuditService" in audit.audit_service

    def test_7_it_declares_a_tenant_scope(self) -> None:
        assert _synthetic().tenant_scope is TenantScope.TENANT

    def test_8_it_declares_a_feature_flag_consistent_with_its_maturity(self) -> None:
        descriptor = _synthetic()
        assert descriptor.feature_flag == "ENABLE_SYNTHETIC_REFERRAL_ECHO"
        assert descriptor.flag_class is FeatureFlagClass.EXPERIMENTAL
        assert descriptor.maturity is CapabilityMaturity.EXPERIMENTAL

    def test_9_it_declares_a_lifecycle_state(self) -> None:
        """Maturity and status move independently: this one is DRAFT to the
        platform and EXPERIMENTAL in evidence, and both are true at once."""
        descriptor = _synthetic()
        assert descriptor.maturity is CapabilityMaturity.EXPERIMENTAL
        assert descriptor.status is CapabilityStatus.DRAFT

    def test_10_it_can_carry_retirement_metadata(self) -> None:
        descriptor = _synthetic()
        assert not descriptor.deprecation.is_declared()  # not deprecated yet

        retiring = _synthetic()
        retiring.maturity = CapabilityMaturity.DEPRECATED
        assert validate_descriptor(retiring), "deprecating without a successor must fail"

        retiring.deprecation = CapabilityDeprecation(
            since_version="1.2.0",
            removal_version="2.0.0",
            replacement="referral_routing",
            migration_notes="Move to referral_routing; payload is unchanged.",
        )
        retiring.flag_class = FeatureFlagClass.DEPRECATED
        assert validate_descriptor(retiring) == []

    def test_the_whole_descriptor_satisfies_the_contract(self) -> None:
        assert validate_descriptor(_synthetic()) == []

    @pytest.mark.parametrize("field_name", REQUIRED_FIELDS)
    def test_removing_any_required_field_is_caught(self, field_name: str) -> None:
        """The contract is proved by breaking it, once per field.

        A validator is only worth what it rejects; asserting that a good
        descriptor passes says nothing about whether a bad one would.
        """
        descriptor = _synthetic()
        current = getattr(descriptor, field_name)
        # An enum field cleared to a list would make the validator raise on the
        # membership test before it could judge anything — clear each field to
        # an empty value of a compatible shape.
        setattr(descriptor, field_name, [] if isinstance(current, list) else "")
        violations = validate_descriptor(descriptor)
        assert any(field_name in v for v in violations), (
            f"clearing {field_name} was not caught: {violations}"
        )

    def test_a_sensitive_capability_without_audit_is_rejected(self) -> None:
        descriptor = _synthetic()
        descriptor.audit = CapabilityAudit(
            writes_audit=False, data_classification="CLINICAL_SENSITIVE",
        )
        assert any("audit" in v for v in validate_descriptor(descriptor))

    def test_a_mismatched_flag_class_is_rejected(self) -> None:
        descriptor = _synthetic()
        descriptor.maturity = CapabilityMaturity.PRODUCTION
        assert any("flag_class" in v for v in validate_descriptor(descriptor))
