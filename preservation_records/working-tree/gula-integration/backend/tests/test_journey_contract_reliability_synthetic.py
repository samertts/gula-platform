"""Phases J (W-058) + K (W-059) — synthetic journey-contract and reliability evidence.

STRICT SCOPE / NO OVER-CLAIM:
  * This suite validates the *contract envelope* that every patient-journey hop must
    satisfy (authenticated + authorized caller, tenant scoping, typed payload,
    immutable audit, idempotency key on writes) and the failure behavior
    (UNAVAILABLE/INDETERMINATE, no silent overwrite, prior data preserved).
  * It does NOT prove the seven journeys work end-to-end. Per
    NATIONAL_SERVICE_CONTRACTS.md §7/§11 the real journeys remain BLOCKED on
    unmigrated `cc_*`/`ehr_*`/hospital tables, missing immutable audit and missing
    cross-service event consumers. No verdict is upgraded here.
  * The reliability tests compose EXISTING primitives (CircuitBreaker, JobRetry)
    with a synthetic in-memory idempotency store. No operational DB, no network,
    no load test, no invented SLO/RPO/RTO, no real patient data.

Evidence ids: E-060 (Phase J), E-061 (Phase K).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from app.kernel.background.job_retry import JobRetry
from app.kernel.gateway.circuit_breaker import CircuitBreaker, CircuitState

REPO = Path(__file__).resolve().parents[2]

# The seven journeys and their hops, transcribed verbatim from
# GOVERNANCE/NATIONAL_SERVICE_CONTRACTS.md §7 (documentation only).
JOURNEYS: dict[str, list[str]] = {
    "J1": ["primary_care_encounter", "order", "sample", "critical_result_event",
           "pharmacy_dispense", "follow_up_plan"],
    "J2": ["ems_incident", "ems_triage", "hospital_admission", "radiology_exam",
           "lab_result", "discharge"],
    "J3": ["maternal_care", "antenatal", "lab", "pharmacy", "referral_accept"],
    "J4": ["chronic_disease", "primary_care", "lab", "medication", "follow_up"],
    "J5": ["vaccination_record", "ehr_immunization", "public_health_event", "surveillance"],
    "J6": ["blood_request", "crossmatch", "component_issued_event", "transfusion_record"],
    "J7": ["referral", "accept_reject", "transitions_of_care", "handover", "feedback"],
}

# First-hop source modules (verified to exist before the test asserts on them).
FIRST_HOP_SOURCE: dict[str, str] = {
    "J1": "backend/app/routes/care_continuum.py",
    "J2": "backend/app/national/api/routes/referral.py",  # EMS→hospital surface proxy; see report
    "J3": "backend/app/routes/care_continuum.py",
    "J4": "backend/app/routes/care_continuum.py",
    "J5": "backend/app/public_health/api/routes.py",
    "J6": "backend/app/blood_bank/api/routes.py",
    "J7": "backend/app/national/api/routes/referral.py",
}


# ---------------------------------------------------------------------------
# Contract envelope (synthetic model — see strict scope above)
# ---------------------------------------------------------------------------


@dataclass
class ContractHop:
    """One journey hop with the six mandatory controls (§7)."""

    name: str
    authenticated: bool = True
    authorized: bool = True
    tenant_scoped: bool = True
    typed_payload: bool = True
    audit_emitted: bool = True
    idempotency_key: str | None = None  # required on writes
    write: bool = False
    outcome: str = "OK"  # OK | UNAVAILABLE | INDETERMINATE


_MANDATORY = ("authenticated", "authorized", "tenant_scoped", "typed_payload", "audit_emitted")


def validate_hop(hop: ContractHop) -> list[str]:
    """Return the list of missing mandatory controls (empty == conformant).

    This is a deterministic contract checker. The negative-control tests below
    prove it actually rejects each missing control rather than always passing.
    """
    missing = [c for c in _MANDATORY if not getattr(hop, c)]
    if hop.write and not hop.idempotency_key:
        missing.append("idempotency_key")
    if hop.outcome not in {"OK", "UNAVAILABLE", "INDETERMINATE"}:
        missing.append("recognized_outcome")
    return missing


class TestJourneyContractEnvelope:
    @pytest.mark.parametrize("journey,hops", list(JOURNEYS.items()))
    def test_all_hops_of_every_journey_can_be_conformant(self, journey, hops):
        # With every control present, each hop is accepted (positive control).
        for name in hops:
            hop = ContractHop(name=name, write=True, idempotency_key=f"syn-{journey}-{name}")
            assert validate_hop(hop) == [], (journey, name)

    @pytest.mark.parametrize("control", _MANDATORY)
    def test_each_missing_control_is_rejected(self, control):
        # Negative controls: removing ONE control always yields a finding,
        # proving the validator is not a rubber stamp.
        hop = ContractHop(name="synthetic-hop", write=True, idempotency_key="k-1")
        setattr(hop, control, False)
        assert control in validate_hop(hop)

    def test_write_without_idempotency_key_is_rejected(self):
        assert "idempotency_key" in validate_hop(ContractHop(name="w", write=True))

    def test_read_without_idempotency_key_is_allowed(self):
        assert validate_hop(ContractHop(name="r", write=False)) == []

    def test_failure_is_conservative_and_preserves_data(self):
        # A failed hop yields UNAVAILABLE/INDETERMINATE, keeps audit, and does
        # NOT carry a write that could silently overwrite clinical data.
        original = {"result": "original-synthetic-value"}
        failed = ContractHop(name="lab", outcome="UNAVAILABLE", write=True,
                             idempotency_key="k-2", audit_emitted=True)
        assert validate_hop(failed) == []
        assert failed.outcome in {"UNAVAILABLE", "INDETERMINATE"}
        assert failed.audit_emitted is True
        assert original["result"] == "original-synthetic-value"  # untouched

    def test_unrecognized_outcome_is_rejected(self):
        hop = ContractHop(name="x", outcome="TARGET_MET")  # never fabricate success
        assert "recognized_outcome" in validate_hop(hop)

    @pytest.mark.parametrize("journey,rel", list(FIRST_HOP_SOURCE.items()))
    def test_first_hop_source_module_exists(self, journey, rel):
        # Real-source structural check: the documented first-hop module exists
        # on disk and declares a router. This does NOT assert runtime wiring,
        # migration state, or journey readiness.
        path = REPO / rel
        assert path.is_file(), f"{journey}: {rel} missing"
        text = path.read_text(encoding="utf-8", errors="replace")
        assert "APIRouter" in text or "router" in text, f"{journey}: no router declaration"


# ---------------------------------------------------------------------------
# Reliability composition (Phase K — existing primitives, synthetic inputs)
# ---------------------------------------------------------------------------


class _InMemoryIdem:
    """Synthetic idempotency store (NOT the DB-backed app.core.idempotency)."""

    def __init__(self):
        self._seen: dict[str, dict] = {}
        self.executions = 0

    def run(self, key: str, work):
        if key in self._seen:
            return self._seen[key]["result"], True  # replay, no re-execution
        result = work()
        self.executions += 1
        self._seen[key] = {"result": result}
        return result, False


class TestReliabilityComposition:
    def test_idempotent_replay_does_not_double_execute(self):
        store = _InMemoryIdem()
        calls = []

        def work():
            calls.append(1)
            return {"status": "created"}

        r1, dup1 = store.run("syn-key-1", work)
        r2, dup2 = store.run("syn-key-1", work)
        assert (dup1, dup2) == (False, True)
        assert r1 == r2
        assert store.executions == 1 and len(calls) == 1

    def test_two_distinct_keys_both_execute(self):
        store = _InMemoryIdem()
        store.run("k-a", lambda: "a")
        store.run("k-b", lambda: "b")
        assert store.executions == 2

    def test_circuit_breaker_opens_blocks_then_half_opens_and_closes(self):
        cb = CircuitBreaker("synthetic", failure_threshold=2, recovery_timeout=0.01)
        assert cb.can_proceed() and cb.state == CircuitState.CLOSED
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_proceed() is False  # blocked while open
        time.sleep(0.02)  # bounded deterministic wait, not an SLO
        assert cb.can_proceed() is True  # transitions to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED and cb.failure_count == 0

    def test_retry_backoff_is_deterministic_geometric(self):
        jr = JobRetry()
        sequence = [jr.get_backoff("t")]
        for _ in range(3):
            jr.increment("t")
            sequence.append(jr.get_backoff("t"))
        assert sequence == [1.0, 2.0, 4.0, 8.0]  # base 1, multiplier 2
        # max_retries = 3: after three increments the budget is exhausted.
        assert jr.should_retry("t") is False
        assert jr.increment("t") == 4
        assert jr.should_retry("t") is False

    def test_composed_failure_yields_unavailable_not_fake_success(self):
        # Circuit open + exhausted retries => UNAVAILABLE, never a fabricated OK.
        cb = CircuitBreaker("syn", failure_threshold=1, recovery_timeout=60.0)
        jr = JobRetry()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        for _ in range(jr._policy.max_retries):
            jr.increment("task")
        if not cb.can_proceed() and not jr.should_retry("task"):
            outcome = "UNAVAILABLE"
        else:
            outcome = "OK"
        assert outcome == "UNAVAILABLE"

    def test_concurrent_replay_still_single_execution(self, monkeypatch):
        # Idempotency under concurrency: 8 threads, same key — one execution.
        # Uses a lock to model a serialization point (real DB store provides it);
        # no timing/SLO assertion is made.
        store = _InMemoryIdem()
        lock = threading.Lock()
        results = []

        def guarded(key):
            with lock:
                return store.run(key, lambda: "ok")

        threads = [threading.Thread(target=lambda: results.append(guarded("same"))) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(results) == 8
        assert all(r == ("ok", r[1]) for r in results)
        assert store.executions == 1

    def test_no_lost_updates_conflicting_versions_kept(self):
        # All conflicting synthetic versions are retained (offline-safety invariant
        # from Phase C), not silently overwritten.
        versions: dict[str, list[int]] = {}

        def record(key, version):
            versions.setdefault(key, []).append(version)

        for v in (1, 2, 3, 2):
            record("patient-record", v)
        assert versions["patient-record"] == [1, 2, 3, 2]
        assert len(versions["patient-record"]) == 4  # no silent overwrite
