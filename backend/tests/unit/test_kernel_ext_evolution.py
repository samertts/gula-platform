"""Unit tests for GULA-KERNEL-EXT-001 Phase 8 — Evolution Engine."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.ext.evolution import (
    PROPOSAL_STATES,
    SIGNAL_KINDS,
    EvolutionEngine,
    EvolutionError,
    EvolutionSignal,
    RfcProposal,
)


class TestSignal:
    def test_valid_signal(self):
        signal = EvolutionSignal("EVO-100001", "repeated_fix", "imports")
        assert signal.count == 1

    def test_bad_id(self):
        with pytest.raises(EvolutionError):
            EvolutionSignal("BAD-1", "repeated_fix", "imports")

    def test_bad_kind(self):
        with pytest.raises(EvolutionError):
            EvolutionSignal("EVO-100001", "nope", "imports")

    def test_zero_count(self):
        with pytest.raises(EvolutionError):
            EvolutionSignal("EVO-100001", "repeated_fix", "imports", count=0)

    def test_all_kinds_valid(self):
        for kind in SIGNAL_KINDS:
            assert EvolutionSignal("EVO-100001", kind, "area").kind == kind


class TestProposal:
    def test_valid_proposal(self):
        proposal = RfcProposal("RFC-100001", "EVO-100001", "t", "r")
        assert proposal.status == "open"

    def test_bad_id(self):
        with pytest.raises(EvolutionError):
            RfcProposal("BAD-1", "EVO-100001", "t", "r")

    def test_bad_state(self):
        with pytest.raises(EvolutionError):
            RfcProposal("RFC-100001", "EVO-100001", "t", "r", status="bogus")

    def test_states_valid(self):
        for state in PROPOSAL_STATES:
            assert RfcProposal("RFC-100001", "EVO-100001", "t", "r", status=state).status == state


class TestEngine:
    def test_detect_below_threshold(self):
        engine = EvolutionEngine(threshold=3)
        engine.record("repeated_fix", "imports")
        engine.record("repeated_fix", "imports")
        assert engine.detect() == []

    def test_detect_at_threshold(self):
        engine = EvolutionEngine(threshold=2)
        engine.record("repeated_fix", "imports", "fix a")
        engine.record("repeated_fix", "imports", "fix b")
        signals = engine.detect()
        assert len(signals) == 1
        assert signals[0].kind == "repeated_fix"
        assert signals[0].count == 2

    def test_detect_once_per_key(self):
        engine = EvolutionEngine(threshold=2)
        engine.record("repeated_fix", "imports", "a")
        engine.record("repeated_fix", "imports", "b")
        assert len(engine.detect()) == 1
        assert len(engine.detect()) == 1

    def test_severity_escalation(self):
        engine = EvolutionEngine(threshold=2)
        for _ in range(5):
            engine.record("repeated_bug", "auth")
        signal = engine.detect()[0]
        assert signal.severity == "medium"

    def test_signals_by_kind(self):
        engine = EvolutionEngine(threshold=2)
        engine.record("repeated_fix", "a", "x")
        engine.record("repeated_fix", "a", "x")
        engine.record("repeated_bug", "b", "y")
        engine.record("repeated_bug", "b", "y")
        engine.detect()
        assert len(engine.signals("repeated_fix")) == 1
        assert len(engine.signals()) == 2

    def test_propose_unknown_signal(self):
        engine = EvolutionEngine()
        with pytest.raises(EvolutionError):
            engine.propose("EVO-999999", "t", "r")

    def test_propose_and_decide(self):
        engine = EvolutionEngine(threshold=2)
        engine.record("repeated_fix", "imports", "a")
        engine.record("repeated_fix", "imports", "b")
        signal = engine.detect()[0]
        proposal = engine.propose(signal.id, "consolidate imports", "evidence")
        assert proposal.status == "open"
        engine.decide(proposal.id, "accepted")
        assert proposal.status == "accepted"
        assert len(engine.proposals("accepted")) == 1

    def test_duplicate_proposal_raises(self):
        engine = EvolutionEngine(threshold=2)
        engine.record("repeated_fix", "imports", "a")
        engine.record("repeated_fix", "imports", "b")
        signal = engine.detect()[0]
        engine.propose(signal.id, "t", "r")
        with pytest.raises(EvolutionError):
            engine.propose(signal.id, "t2", "r2")

    def test_decide_unknown_proposal(self):
        engine = EvolutionEngine()
        with pytest.raises(EvolutionError):
            engine.decide("RFC-000000", "accepted")

    def test_decide_bad_verdict(self):
        engine = EvolutionEngine(threshold=2)
        engine.record("repeated_fix", "imports", "a")
        engine.record("repeated_fix", "imports", "b")
        signal = engine.detect()[0]
        proposal = engine.propose(signal.id, "t", "r")
        with pytest.raises(EvolutionError):
            engine.decide(proposal.id, "maybe")

    def test_reject_proposal(self):
        engine = EvolutionEngine(threshold=2)
        engine.record("repeated_fix", "imports", "a")
        engine.record("repeated_fix", "imports", "b")
        signal = engine.detect()[0]
        proposal = engine.propose(signal.id, "t", "r")
        engine.decide(proposal.id, "rejected")
        assert len(engine.proposals("rejected")) == 1

    def test_rfc_never_applies_directly(self):
        engine = EvolutionEngine(threshold=2)
        engine.record("repeated_fix", "imports", "a")
        engine.record("repeated_fix", "imports", "b")
        signal = engine.detect()[0]
        proposal = engine.propose(signal.id, "t", "r")
        assert proposal.status in PROPOSAL_STATES
        assert not hasattr(engine, "apply")

    def test_snapshot_and_save(self, tmp_path):
        engine = EvolutionEngine(threshold=2)
        engine.record("repeated_fix", "imports", "a")
        engine.record("repeated_fix", "imports", "b")
        engine.detect()
        path = engine.save(tmp_path / "evolution.json")
        data = path.read_text(encoding="utf-8")
        assert "repeated_fix" in data
