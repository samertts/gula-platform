"""AI guardrails & sandbox safety — Phase 5 hardening.

Production invariant:

    AI = Suggest. Human = Approve. System = Enforce.

This is the autonomy boundary documented in app/ai/guardrails.py. The
guardrails are defense-in-depth: they assume the AI model is potentially
adversarial and prevent capability escalation regardless of prompt
content.

Tests asserted:

  1. Absolutely-blocked operations are rejected at construction time
     (no AISuggestion can ever be created for them, regardless of how
     it's invoked — including through ai_suggest()).
  2. Suggestions default to UNTRUSTED (is_approved=False).
  3. Suggestions for absolutely-blocked operations cannot be smuggled
     in via direct AISuggestion(...) construction either.
  4. Sandbox refuses to execute approvals that are not in APPROVED state.
  5. Sandbox refuses to execute operations not in its whitelist.
  6. Sandbox handlers never mutate state — they're pure read-only.
  7. Display-only suggestions auto-approve but cannot escalate to
     state-changing operations.
  8. ApprovalStore TTL invalidates stale pending approvals.

These tests exercise pure Python invariants — no DB or HTTP needed.
Blast radius: zero. Risk: changes to the AI module that loosen these
invariants will fail loudly here.
"""
from __future__ import annotations

import os
import sys
import time

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.ai.approval import (
    ApprovalStatus,
    ApprovalStore,
)
from app.ai.guardrails import (
    _ABSOLUTELY_BLOCKED,
    _SUGGESTABLE,
    AIGuardrailViolation,
    AIOperationType,
    AISuggestion,
    ai_suggest,
)
from app.ai.sandbox import _REGISTRY, AISandbox

# ─── Phase 5.A — Absolutely blocked operations ───────────────────────────────


class TestAbsolutelyBlocked:
    """Operations in _ABSOLUTELY_BLOCKED can never be performed by AI,
    even with human approval. The guardrail must reject them at every
    entry point."""

    def test_ai_suggest_raises_on_blocked_operation(self):
        """Calling ai_suggest() with a blocked op must raise."""
        for op in _ABSOLUTELY_BLOCKED:
            with pytest.raises(AIGuardrailViolation):
                ai_suggest(op, {"foo": "bar"})

    def test_ai_suggestion_construction_blocks_directly(self):
        """Even bypassing ai_suggest() and constructing AISuggestion directly
        must fail — __post_init__ enforces the invariant."""
        for op in _ABSOLUTELY_BLOCKED:
            with pytest.raises(AIGuardrailViolation):
                AISuggestion(operation=op, payload={})

    def test_validate_order_is_blocked(self):
        """Specific high-risk ops are explicitly named."""
        assert "validate_order" in _ABSOLUTELY_BLOCKED
        assert "modify_result" in _ABSOLUTELY_BLOCKED
        assert "delete_patient" in _ABSOLUTELY_BLOCKED
        assert "change_role" in _ABSOLUTELY_BLOCKED
        assert "write_audit_log" in _ABSOLUTELY_BLOCKED
        assert "export_patient_data" in _ABSOLUTELY_BLOCKED


# ─── Phase 5.B — Suggestion defaults ─────────────────────────────────────────


class TestSuggestionDefaults:
    """Every suggestion is UNTRUSTED by default. Approval is opt-in,
    human-driven, and must never auto-flip from a state-changing op."""

    def test_suggestion_starts_unapproved(self):
        s = ai_suggest("suggest_interpretation",
                       {"test_name": "Glucose", "value": 100})
        assert s.is_approved is False

    def test_suggestion_id_is_unique(self):
        s1 = ai_suggest("suggest_interpretation", {})
        s2 = ai_suggest("suggest_interpretation", {})
        assert s1.id != s2.id

    def test_unknown_operation_classified_as_display_only(self):
        """Unknown ops default to DISPLAY_ONLY (least-privilege)."""
        s = ai_suggest("some_random_operation_not_in_registry", {})
        assert s.operation_type == AIOperationType.DISPLAY_ONLY

    def test_known_suggestable_classified_as_suggestion(self):
        s = ai_suggest("suggest_interpretation", {})
        assert s.operation_type == AIOperationType.SUGGESTION

    def test_confidence_must_be_in_range(self):
        with pytest.raises(ValueError):
            AISuggestion(operation="suggest_interpretation", confidence=1.5)
        with pytest.raises(ValueError):
            AISuggestion(operation="suggest_interpretation", confidence=-0.1)


# ─── Phase 5.C — Approval store state machine ────────────────────────────────


class TestApprovalStateMachine:
    """ApprovalStore enforces: PENDING → APPROVED → EXECUTED, no shortcuts."""

    def test_pending_approval_is_not_executable(self):
        store = ApprovalStore()
        s = ai_suggest("suggest_interpretation", {"test_name": "X", "value": 1})
        a = store.submit(s)
        assert a.status == ApprovalStatus.PENDING
        assert a.is_executable is False

    def test_approved_approval_is_executable(self):
        store = ApprovalStore()
        s = ai_suggest("suggest_interpretation", {"test_name": "X", "value": 1})
        a = store.submit(s)
        store.approve(a.id, approver="dr@hospital.com")
        assert a.status == ApprovalStatus.APPROVED
        assert a.is_executable is True

    def test_rejected_approval_cannot_be_approved(self):
        store = ApprovalStore()
        s = ai_suggest("suggest_interpretation", {"test_name": "X", "value": 1})
        a = store.submit(s)
        store.reject(a.id, approver="dr@hospital.com", reason="bad")
        with pytest.raises(ValueError):
            store.approve(a.id, approver="dr@hospital.com")

    def test_double_approve_is_rejected(self):
        """An already-approved approval cannot be re-approved (no replay)."""
        store = ApprovalStore()
        s = ai_suggest("suggest_interpretation", {"test_name": "X", "value": 1})
        a = store.submit(s)
        store.approve(a.id, approver="dr1@x.com")
        with pytest.raises(ValueError):
            store.approve(a.id, approver="dr2@x.com")

    def test_display_only_auto_approves(self):
        """DISPLAY_ONLY suggestions skip human review (they don't change state)."""
        store = ApprovalStore()
        s = ai_suggest("free_form_summary", {"text": "blah"})
        assert s.operation_type == AIOperationType.DISPLAY_ONLY
        a = store.submit(s)
        assert a.status == ApprovalStatus.APPROVED
        assert "system:display_only_auto" in (a.reviewed_by or "")


# ─── Phase 5.D — Sandbox executes only whitelisted, approved ops ─────────────


class TestSandboxExecution:
    """The sandbox is the final gate: even an APPROVED suggestion cannot run
    if the operation is not in the registered whitelist."""

    def test_unapproved_approval_cannot_execute(self):
        """Pending approval → AIGuardrailViolation."""
        store = ApprovalStore()
        s = ai_suggest("suggest_interpretation",
                       {"test_name": "Glucose", "value": 100})
        a = store.submit(s)
        # Status is PENDING — not executable
        with pytest.raises(AIGuardrailViolation):
            AISandbox.execute(a)

    def test_unwhitelisted_operation_blocked(self):
        """An operation not in _REGISTRY cannot be executed even if approved."""
        store = ApprovalStore()
        # Construct an AISuggestion + Approval directly with an op that is
        # _SUGGESTABLE but somehow NOT registered. We pick a name that
        # would slip past ai_suggest() but isn't in _REGISTRY.
        bogus = "operation_not_in_registry"
        # ai_suggest classifies unknown ops as DISPLAY_ONLY → auto-approve
        # That is the test: even an auto-approved unknown op must fail at
        # the sandbox because it's not whitelisted.
        s = ai_suggest(bogus, {})
        a = store.submit(s)
        # Approved (display_only) but not in _REGISTRY → sandbox refuses
        with pytest.raises(AIGuardrailViolation):
            AISandbox.execute(a)

    def test_approved_whitelisted_op_executes(self):
        # Sandbox.execute() calls approval_store.mark_executed, so we must
        # use the module-level global store the sandbox imports from.
        from app.ai.approval import approval_store
        s = ai_suggest(
            "suggest_interpretation",
            {"test_name": "Glucose", "value": 100,
             "unit": "mg/dL", "normal_low": 70, "normal_high": 100},
        )
        a = approval_store.submit(s)
        approval_store.approve(a.id, approver="dr@hospital.com")
        result = AISandbox.execute(a)
        assert result.success is True
        assert result.output["display_only"] is True

    def test_executed_approval_cannot_be_replayed(self):
        """After successful execution, the approval is marked EXECUTED and
        cannot be re-run (preventing replay attacks)."""
        store = ApprovalStore()
        s = ai_suggest(
            "suggest_interpretation",
            {"test_name": "Glucose", "value": 100,
             "unit": "mg/dL", "normal_low": 70, "normal_high": 100},
        )
        # We need to use the *module-level* approval_store because the
        # sandbox imports it directly. Recreate the flow there.
        from app.ai.approval import approval_store as global_store
        a = global_store.submit(s)
        global_store.approve(a.id, approver="dr@hospital.com")
        AISandbox.execute(a)
        assert a.status == ApprovalStatus.EXECUTED
        # Second execute attempt: status is EXECUTED, not APPROVED → blocked
        with pytest.raises(AIGuardrailViolation):
            AISandbox.execute(a)


# ─── Phase 5.E — Sandbox handlers are read-only ──────────────────────────────


class TestSandboxHandlersReadOnly:
    """Every registered handler must be a pure function — no DB writes,
    no external state. This is checked structurally: the handler signature
    accepts a dict payload and returns a dict; no Session is injected."""

    def test_all_registered_handlers_have_correct_arity(self):
        """Each registered handler accepts exactly one positional arg (payload)."""
        import inspect
        for op, handler in _REGISTRY.items():
            sig = inspect.signature(handler)
            params = list(sig.parameters.values())
            assert len(params) == 1, (
                f"sandbox handler {op!r} has unexpected signature {sig}; "
                "all handlers must accept exactly (payload: dict)"
            )

    def test_handlers_do_not_import_db_session(self):
        """A handler that imports get_db / SessionLocal would have DB write
        capability — that violates the read-only contract.

        We check the source code of each registered handler module-locally.
        """
        import inspect
        for op, handler in _REGISTRY.items():
            src = inspect.getsource(handler)
            # Forbidden DB-write entry points for handlers
            for forbidden in ("SessionLocal", "db.commit(", "db.add(", "db.delete("):
                assert forbidden not in src, (
                    f"sandbox handler {op!r} contains forbidden DB-write call "
                    f"{forbidden!r}; handlers must be read-only"
                )

    def test_registered_operations_are_subset_of_suggestable(self):
        """Only _SUGGESTABLE operations should be in the sandbox registry."""
        for op in _REGISTRY:
            assert op in _SUGGESTABLE, (
                f"Sandbox registered an operation {op!r} that is not in "
                f"_SUGGESTABLE — possible privilege expansion."
            )


# ─── Phase 5.F — TTL expiry on stale approvals ───────────────────────────────


class TestApprovalTTL:
    """Approvals must expire — a stale pending approval cannot be executed
    once past its TTL."""

    def test_expired_pending_approval_is_rejected_on_approve(self, monkeypatch):
        """Mock TTL to 0s and confirm an aged pending approval is rejected."""
        import app.ai.approval as appr
        monkeypatch.setattr(appr, "TTL_SECONDS", 0)
        store = appr.ApprovalStore()
        s = ai_suggest("suggest_interpretation",
                       {"test_name": "Glucose", "value": 100})
        a = store.submit(s)
        # With TTL=0 it's immediately expired
        with pytest.raises(ValueError):
            store.approve(a.id, approver="dr@x.com")

    def test_get_marks_expired_on_read(self, monkeypatch):
        import app.ai.approval as appr
        monkeypatch.setattr(appr, "TTL_SECONDS", 0)
        store = appr.ApprovalStore()
        s = ai_suggest("suggest_interpretation",
                       {"test_name": "Glucose", "value": 100})
        a = store.submit(s)
        fetched = store.get(a.id)
        assert fetched is not None
        assert fetched.status == appr.ApprovalStatus.EXPIRED


# ─── Phase 5.G — RBAC contract: AI can never escalate roles ──────────────────


class TestAIRBACBoundary:
    """The guardrail's _ABSOLUTELY_BLOCKED list contains every operation that
    would expand AI authority. These tests pin the list as a non-regression so
    that a future PR cannot silently move an operation out of the blocklist."""

    def test_role_changing_ops_are_blocked(self):
        for op in ("change_role", "create_lab_user"):
            assert op in _ABSOLUTELY_BLOCKED

    def test_data_destruction_ops_are_blocked(self):
        for op in ("delete_patient", "modify_result"):
            assert op in _ABSOLUTELY_BLOCKED

    def test_audit_integrity_ops_are_blocked(self):
        assert "write_audit_log" in _ABSOLUTELY_BLOCKED

    def test_clinical_signoff_ops_are_blocked(self):
        for op in ("validate_order", "approve_result", "send_critical_alert"):
            assert op in _ABSOLUTELY_BLOCKED

    def test_privacy_ops_are_blocked(self):
        assert "export_patient_data" in _ABSOLUTELY_BLOCKED
