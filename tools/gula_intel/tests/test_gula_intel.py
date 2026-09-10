"""Focused tests for the deterministic platform core.

Each test proves one capability from the acceptance criteria.  The detectors are
exercised against synthetic fixtures so a pass cannot depend on the current
state of the repository, plus one live assertion that the engine agrees with
independently established ground truth.
"""
from __future__ import annotations

import os
import pathlib
import sys
from typing import Any

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from gula_intel import detectors, impact, inventory, registry
from gula_intel.ai_boundary import AdapterViolation, assert_capability, build_context
from gula_intel.model import (
    CheckResult,
    DetectorState,
    Finding,
    FindingState,
    Severity,
    Status,
    stable_id,
)


def _inv(**kw: Any) -> inventory.Inventory:
    base: dict[str, Any] = {
        "tables": {},
        "migrations": {},
        "endpoints": 0,
        "modules": [],
        "transition_tables": {},
        "sources": {},
    }
    base.update(kw)
    return inventory.Inventory(**base)


# --- Evidence model: the mandatory not-run distinction -----------------------

def test_detector_that_did_not_run_is_unknown_not_verified() -> None:
    result = CheckResult("R", DetectorState.NOT_RUN)
    assert result.status is Status.UNKNOWN
    assert result.status is not Status.VERIFIED


def test_clean_run_is_verified_and_findings_are_failed() -> None:
    assert CheckResult("R", DetectorState.RAN_CLEAN).status is Status.VERIFIED
    assert CheckResult("R", DetectorState.RAN_FOUND).status is Status.FAILED
    assert CheckResult("R", DetectorState.RAN_NO_EVIDENCE).status is Status.PARTIALLY_VERIFIED


def test_missing_migrations_directory_reports_not_run() -> None:
    result = detectors.detect_duplicate_revisions(_inv())
    assert result.detector_state is DetectorState.NOT_RUN
    assert result.status is Status.UNKNOWN


# --- Detectors --------------------------------------------------------------

def test_duplicate_revision_is_detected() -> None:
    migrations = {"a1": {"file": "a.py", "downs": [], "files": ["a.py", "b.py"]}}
    result = detectors.detect_duplicate_revisions(_inv(migrations=migrations))
    assert result.status is Status.FAILED
    assert "a.py" in result.findings[0].affected


def test_multiple_heads_is_detected_and_single_head_is_clean() -> None:
    two = {"a": {"file": "a.py", "downs": [], "files": ["a.py"]},
           "b": {"file": "b.py", "downs": [], "files": ["b.py"]}}
    assert detectors.detect_multiple_heads(_inv(migrations=two)).status is Status.FAILED
    one = {"a": {"file": "a.py", "downs": [], "files": ["a.py"]},
           "b": {"file": "b.py", "downs": ["a"], "files": ["b.py"]}}
    assert detectors.detect_multiple_heads(_inv(migrations=one)).status is Status.VERIFIED


def test_table_owned_by_two_packages_is_detected() -> None:
    result = detectors.detect_table_ownership_conflicts(_inv(tables={"t": ["a", "b"], "u": ["a"]}))
    assert result.status is Status.FAILED
    assert len(result.findings) == 1
    assert result.findings[0].architecture_decision_required is True


def test_duplicate_state_key_is_per_dict_not_per_file() -> None:
    """A name reused by two separate maps is not a collision; within one map it is."""
    two_maps = {"f.py": [[("reserved", 1), ("issued", 2), ("x", 3), ("y", 4)],
                         [("reserved", 9), ("cancelled", 10), ("p", 11), ("q", 12)]]}
    assert detectors.detect_duplicate_state_keys(_inv(transition_tables=two_maps)).status is Status.VERIFIED
    one_map = {"f.py": [[("reserved", 1), ("issued", 2), ("x", 3), ("reserved", 9)]]}
    result = detectors.detect_duplicate_state_keys(_inv(transition_tables=one_map))
    assert result.status is Status.FAILED
    assert "reserved" in result.findings[0].title


# --- Live agreement with independently established ground truth --------------

def test_the_known_pharmacy_fk_blocker_stays_fixed() -> None:
    """NR-003 regression guard.

    This test previously asserted the blocker was PRESENT, which is what a
    detector-development test does. NR-003 has since been fixed: both
    substitution-rule columns are Integer foreign keys to the catalog's Integer
    key. Left as it was, the test would fail forever on a healthy repository
    and pass again only if the defect returned -- the opposite of a regression
    guard. It now asserts the fix holds.
    """
    result = detectors.detect_fk_type_mismatch()
    assert result.detector_state is DetectorState.RAN_CLEAN
    assert result.status is Status.VERIFIED
    assert result.findings == []


def test_repository_migration_graph_is_currently_clean() -> None:
    inv = inventory.collect()
    assert detectors.detect_duplicate_revisions(inv).status is Status.VERIFIED
    assert detectors.detect_multiple_heads(inv).status is Status.VERIFIED


# --- Change impact and test selection ---------------------------------------

def test_docs_only_change_has_no_known_impact_and_selects_no_tests() -> None:
    paths = ["docs/architecture/X.md"]
    assert impact.analyse(paths)[0].level == impact.NONE
    assert impact.select_tests(paths) == {}
    assert "remains valid" in impact.unaffected_note(paths)


def test_blood_bank_change_selects_blood_bank_tests_with_a_reason() -> None:
    selected = impact.select_tests(["backend/app/blood_bank/domain/state_machine.py"])
    assert "backend/tests/blood_bank/" in selected
    assert "Blood Bank" in selected["backend/tests/blood_bank/"][0]


def test_shared_clinical_guard_change_is_direct_impact() -> None:
    result = impact.analyse(["backend/app/clinical/command_guard.py"])[0]
    assert result.level == impact.DIRECT
    assert "many domains" in result.reason


def test_unmapped_path_is_possible_impact_never_safe() -> None:
    assert impact.analyse(["something/unknown.py"])[0].level == impact.POSSIBLE


# --- Recurrence memory ------------------------------------------------------

def _finding(oid: str) -> Finding:
    return Finding("R", oid, "t", Severity.P1, "c", "d", [], "e")


def test_previously_fixed_finding_that_returns_is_reported_as_recurred() -> None:
    state = {"occurrences": {"x": {"rule_id": "R", "state": FindingState.FIXED.value}}}
    out = registry.reconcile([CheckResult("R", DetectorState.RAN_FOUND, [_finding("x")])], state, "c1")
    assert out["transitions"]["x"] == registry.RECURRED


def test_new_and_still_open_are_distinguished() -> None:
    results = [CheckResult("R", DetectorState.RAN_FOUND, [_finding("a")])]
    assert registry.reconcile(results, {"occurrences": {}}, "c1")["transitions"]["a"] == registry.NEW
    open_state = {"occurrences": {"a": {"rule_id": "R", "state": FindingState.OPEN.value}}}
    assert registry.reconcile(results, open_state, "c2")["transitions"]["a"] == registry.STILL_OPEN


def test_a_detector_that_did_not_run_cannot_resolve_a_finding() -> None:
    state = {"occurrences": {"a": {"rule_id": "R", "state": FindingState.OPEN.value}}}
    out = registry.reconcile([CheckResult("R", DetectorState.NOT_RUN)], state, "c2")
    assert "a" not in out["transitions"]
    out2 = registry.reconcile([CheckResult("R", DetectorState.RAN_CLEAN)], state, "c2")
    assert out2["transitions"]["a"] == registry.RESOLVED


def test_occurrence_ids_are_stable_across_runs() -> None:
    assert stable_id("R", "t") == stable_id("R", "t")
    assert stable_id("R", "t") != stable_id("R", "u")


# --- AI boundary ------------------------------------------------------------

def test_ai_adapter_cannot_claim_a_deterministic_decision() -> None:
    for forbidden in ("mark_finding_verified", "decide_production_readiness", "authorize_user"):
        with pytest.raises(AdapterViolation):
            assert_capability(forbidden)
    assert_capability("explain")  # permitted


def test_context_for_ai_contains_only_already_decided_facts() -> None:
    ctx = build_context([CheckResult("R", DetectorState.RAN_CLEAN)], {"tables": 1})
    assert ctx["checks"][0]["status"] == Status.VERIFIED.value
    assert "mark_finding_verified" in ctx["contract"]["forbidden"]


def test_core_imports_no_ai_provider() -> None:
    for module in ("model", "inventory", "detectors", "impact", "registry"):
        source = (pathlib.Path(__file__).resolve().parents[1] / f"{module}.py").read_text()
        for banned in ("anthropic", "openai", "requests.post", "httpx"):
            assert banned not in source, f"{module}.py must not reach a model provider"


# --- Development planner ----------------------------------------------------

def test_docs_only_change_is_low_risk_and_requires_no_tests() -> None:
    from gula_intel import planner
    result = planner.plan(["docs/x.md"], include_open_blockers=False)
    assert result.risk == planner.LOW
    assert result.required_tests == {}
    assert result.migration_implications == []


def test_migration_change_is_critical_and_demands_a_clean_database_proof() -> None:
    from gula_intel import planner
    result = planner.plan(["backend/migrations/versions/x.py"], include_open_blockers=False)
    assert result.risk == planner.CRITICAL
    assert any("clean-database" in e for e in result.evidence_required)
    assert "backend/tests/migrations/" in result.required_tests


def test_shared_clinical_guard_change_is_high_risk_with_safety_implications() -> None:
    from gula_intel import planner
    result = planner.plan(["backend/app/clinical/command_guard.py"], include_open_blockers=False)
    assert result.risk == planner.HIGH
    assert result.clinical_safety_implications
    assert result.security_implications


def test_risk_factors_are_explicit_and_explainable() -> None:
    from gula_intel import planner
    result = planner.plan(["backend/app/blood_bank/x.py"], include_open_blockers=False)
    assert result.factors and all({"factor", "weight", "matched"} <= set(f) for f in result.factors)


def test_planner_never_claims_deployment_safety() -> None:
    from gula_intel import planner
    for paths in (["docs/x.md"], ["backend/migrations/versions/x.py"]):
        blob = str(planner.plan(paths, include_open_blockers=False).to_dict()).lower()
        assert "safe to deploy" not in blob
        assert "production ready" not in blob


# ── GULA-SCHEMA-002: ORM vs migration-built schema ──────────────────────────


def test_schema_002_reports_no_evidence_without_a_database(monkeypatch) -> None:
    """The rule the platform must never break: UNKNOWN is not VERIFIED.

    An ORM cannot be checked against a schema that is not there. Reporting
    "no findings" would present an unrun comparison as a healthy one.
    """
    monkeypatch.delenv("GULA_INTEL_DATABASE_URL", raising=False)
    result = detectors.detect_orm_schema_drift()
    assert result.detector_state is DetectorState.RAN_NO_EVIDENCE
    assert result.findings == []
    assert result.detector_state is not DetectorState.RAN_CLEAN


def test_schema_002_reports_no_evidence_when_the_database_is_unreachable() -> None:
    """A refused connection is absence of evidence, not evidence of health."""
    result = detectors.detect_orm_schema_drift(
        "postgresql+psycopg2://nobody@127.0.0.1:1/does-not-exist"
    )
    assert result.detector_state in {
        DetectorState.RAN_NO_EVIDENCE,
        DetectorState.NOT_RUN,
    }
    assert result.findings == []


def test_schema_002_renders_both_sides_through_one_dialect() -> None:
    """The false positive that made this detector hard.

    str(TIMESTAMP(timezone=True)) is "TIMESTAMP", which does not match an ORM
    column rendered as "TIMESTAMP WITH TIME ZONE" even though the two agree.
    Comparing through the dialect is what makes the detector trustworthy.
    """
    import sqlalchemy

    aware = sqlalchemy.DateTime(timezone=True)
    naive = sqlalchemy.DateTime(timezone=False)

    assert detectors._render(aware) == detectors._render(aware)
    assert detectors._render(aware) != detectors._render(naive)
    assert "TIME ZONE" in detectors._render(aware)


def test_schema_002_rule_is_registered_and_blocking() -> None:
    rule = detectors.RULES["GULA-SCHEMA-002"]
    assert rule.severity is Severity.P0
    assert rule.architecture_decision_required is True
    assert "GULA-SCHEMA-002" in {r.rule_id for r in detectors.run_all(inventory.collect())}


# --- BATCH-1: cross-domain schema truth --------------------------------------
#
# GULA-SCHEMA-002 compares columns, so it skips tables that do not exist at all
# and reported zero findings for a repository where 402 mapped tables have no
# schema. These two rules close that hole. They need a migration-built database;
# without one they must say so rather than report health.

_DB = os.environ.get("GULA_INTEL_DATABASE_URL")
_needs_db = pytest.mark.skipif(not _DB, reason="GULA_INTEL_DATABASE_URL is not configured")


@pytest.mark.parametrize(
    "detector",
    [
        detectors.detect_orm_tables_without_physical_table,
        detectors.detect_cross_domain_missing_dependency,
        detectors.detect_orm_schema_drift,
    ],
)
def test_without_a_database_the_schema_detectors_report_unavailable_not_clean(
    monkeypatch: pytest.MonkeyPatch, detector: Any
) -> None:
    """The fail-closed requirement, asserted for every schema detector.

    An unreachable database yields no findings. If that were reported as
    RAN_CLEAN it would read as VERIFIED, which is precisely the false-green
    this batch exists to remove.
    """
    monkeypatch.delenv("GULA_INTEL_DATABASE_URL", raising=False)
    result = detector()
    assert result.detector_state is DetectorState.RAN_NO_EVIDENCE
    assert result.status is Status.PARTIALLY_VERIFIED
    assert result.status is not Status.VERIFIED
    assert result.findings == []


@pytest.mark.parametrize(
    "detector",
    [
        detectors.detect_orm_tables_without_physical_table,
        detectors.detect_cross_domain_missing_dependency,
    ],
)
def test_an_unreachable_database_is_unavailable_not_clean(detector: Any) -> None:
    """A URL that points at nothing must not read as a clean run either."""
    result = detector("postgresql+psycopg2://postgres@127.0.0.1:1/does-not-exist")
    assert result.detector_state is DetectorState.RAN_NO_EVIDENCE
    assert result.findings == []


@_needs_db
def test_ehr_has_no_physical_schema_and_that_is_a_blocker() -> None:
    """MCM-P0-2, as a detector finding rather than a paragraph in a report.

    Every EHR table is mapped and none exists. The old detector said nothing
    about this domain at all.
    """
    result = detectors.detect_orm_tables_without_physical_table()
    assert result.detector_state is DetectorState.RAN_FOUND
    ehr = [f for f in result.findings if f.domain.startswith("app.ehr")]
    assert len(ehr) == 18, f"expected all 18 EHR tables missing, got {len(ehr)}"
    assert all(f.severity is Severity.P0 for f in ehr)
    assert "ehr" in result.note


@_needs_db
def test_pharmacy_is_broken_by_a_table_it_does_not_own() -> None:
    """MCM-P0-3, the finding per-domain verification structurally cannot make.

    Pharmacy is 27/27 against its own schema and GULA-SCHEMA-002 reports it
    clean. It still writes ehr_medication_dispenses, which does not exist, so a
    sale carrying a patient id cannot complete.
    """
    result = detectors.detect_cross_domain_missing_dependency()
    assert result.detector_state is DetectorState.RAN_FOUND
    pharmacy = [f for f in result.findings if f.domain == "backend/app/pharmacy"]
    assert len(pharmacy) == 1
    assert pharmacy[0].affected == ["pharmacy/services.py", "ehr_medication_dispenses"]
    assert pharmacy[0].severity is Severity.P0


@_needs_db
def test_measurement_covers_every_domain_not_just_the_reconciled_one() -> None:
    """The scope fix itself.

    Enrolment was one domain, so the detector could only ever describe one
    domain. Discovery now finds every declarative base, and RECONCILED_DOMAINS
    records what has been proven without suppressing anything.
    """
    bases = detectors._load_orm_metadata()
    labels = {label for label, _ in bases}
    assert len(bases) >= 18, f"expected every declarative base, found {len(bases)}"
    for expected in ("app.pharmacy", "app.ehr", "app.identity", "app.national"):
        assert any(label.startswith(expected) for label in labels), expected
    assert frozenset({"pharmacy"}) == detectors.RECONCILED_DOMAINS


@_needs_db
def test_a_module_that_cannot_be_imported_is_recorded_not_skipped() -> None:
    """UNMEASURED must be visible. Silence here would be indistinguishable
    from a domain that measured clean."""
    detectors._load_orm_metadata()
    unimportable = detectors._unimportable_model_modules()
    assert isinstance(unimportable, dict)
    if unimportable:
        result = detectors.detect_orm_tables_without_physical_table()
        assert "UNMEASURED" in result.note


# --- BATCH-1: metadata registry drift ----------------------------------------


def test_the_alembic_registry_is_resolved_by_identity_not_by_name() -> None:
    """Names would invent drift that is not there.

    ``CareContinuumBase`` and ``CareContinuumAuditEntity`` are two names for one
    MetaData. A name comparison reports the second unregistered; an identity
    comparison does not.
    """
    registered, note = detectors._registered_metadata_ids()
    assert registered, note
    assert "unresolved" not in note, note


def test_every_declarative_base_is_either_registered_or_reported() -> None:
    """Recurrence protection for the registry itself.

    A base that alembic cannot see produces an empty autogenerate diff, which is
    indistinguishable from an accurate one. This fails if a new unregistered
    base appears without the count being reconsidered.
    """
    result = detectors.detect_unregistered_declarative_bases()
    assert result.detector_state in {
        DetectorState.RAN_FOUND,
        DetectorState.RAN_CLEAN,
    }, result.note
    bases = detectors._load_orm_metadata()
    registered, _ = detectors._registered_metadata_ids()
    accounted = len(result.findings) + sum(1 for _, md in bases if id(md) in registered)
    # Every base is either registered or carries a finding. Neither list may
    # quietly shrink.
    assert accounted == len(bases)
    assert len(result.findings) == 2, (
        "the set of bases alembic cannot see changed; confirm this is intended "
        "and update the expected count: " + result.note
    )
    # The two that remain are deliberate, not forgotten: insurance is DEFER
    # (13 tables, none physical, no reachable operation, awaiting a product
    # decision) and national.task_engine is RETIRE (15 tables, same evidence).
    domains = {f.domain for f in result.findings}
    assert any("insurance" in d for d in domains)
    assert any("task_engine" in d for d in domains)


def test_the_canonical_core_registry_is_the_one_alembic_knows() -> None:
    """app.models.base.Base carries the core tables and must stay registered."""
    bases = dict(detectors._load_orm_metadata())
    registered, _ = detectors._registered_metadata_ids()
    core = bases.get("app.models.base.Base")
    assert core is not None, "the core declarative base was not discovered"
    assert id(core) in registered
    for table in ("patients", "labs", "lab_orders", "lab_results"):
        assert table in core.tables, f"{table} is not on the canonical core base"


# --- BATCH-2.5: alembic must not be handed an empty metadata ------------------


@_needs_db
def test_no_registered_base_resolves_to_an_empty_metadata() -> None:
    """The hazard NR-018's registration created, before it could fire.

    Importing a *base* module registers no tables — the models live elsewhere.
    Four of the eight bases registered in target_metadata (pharmacy, radiology,
    nhdw, nursing) resolved to an EMPTY MetaData from a base-only import. An
    empty metadata is worse than an unregistered one: autogenerate compares zero
    mapped tables against a populated database and proposes dropping all of
    them. env.py now calls import_all_models() before building target_metadata.
    """
    registered, _ = detectors._registered_metadata_ids()
    bases = detectors._load_orm_metadata()
    empty = {
        label for label, metadata in bases
        if id(metadata) in registered and not metadata.tables
    }
    # CitizenPlatformBase is a pre-existing instance, not one this work
    # introduced: it is registered in target_metadata and maps nothing, because
    # no concrete model inherits from its abstract entities. Recorded as NR-024.
    # (`citizens` and `citizen_links` are physical and ARE mapped — by
    # app.database.Base. An earlier draft of NR-024 said otherwise; that was
    # measured on a partial import graph.) Pinned rather than asserted empty so
    # a *new* empty registration fails here.
    known = {"app.citizen_platform.base.CitizenAuditEntity"}
    assert empty <= known, (
        "a base is registered for autogeneration but maps no tables, so "
        "autogenerate would propose dropping its physical tables: "
        + ", ".join(sorted(empty - known))
    )
    assert empty == known, (
        "NR-024 appears to be resolved; update this guard rather than leaving "
        "it asserting a defect that no longer exists"
    )


@_needs_db
def test_the_cross_metadata_collision_blocking_autogenerate_is_exactly_one() -> None:
    """NR-023's remaining blocker, pinned so it cannot grow silently.

    Foreign keys cannot resolve across MetaData objects. Measured against the
    exact env.py import graph: 360 references to 24 distinct targets sit in a
    different metadata from the table referencing them, and 6 of the 18
    registered metadata objects fail their topological sort because of it.
    Every one of those 24 targets IS mapped — just elsewhere — so the canonical
    fix is one shared MetaData. It is blocked by table-name collisions, of which
    there is exactly one: national_facilities, mapped by both app.database.Base
    and app.national.base. That is NR-006.
    """
    bases = detectors._load_orm_metadata()
    owners: dict[str, list[str]] = {}
    for label, metadata in bases:
        for table in metadata.tables:
            owners.setdefault(table, []).append(label)
    collisions = {t: o for t, o in owners.items() if len(o) > 1}
    assert set(collisions) == {"national_facilities"}, (
        "the set of table names blocking a shared MetaData changed: " + str(collisions)
    )
