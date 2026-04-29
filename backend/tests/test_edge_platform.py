"""Tests for the Edge AI Platform control plane.

Covers:
  - Device registration + list / get / quarantine / revoke / reinstate
  - Task submit + agent heartbeat (claim) + result reporting
  - Trust score adjustments and auto-quarantine on floor
  - Task signing & verification
  - Policy upsert + kind allow/deny enforcement
  - Stale task reaper
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from app.edge import config as edge_config, identity, policy as policy_mod, \
    registry, scheduler, trust as trust_mod, governance
from app.models.edge import EdgeDevice, EdgeTask
from app.security.auth import create_token


def _auth(user_id: int, lab_id: int, role: str = "admin") -> dict:
    """Bearer header for an admin user — same recipe as conftest.auth_headers."""
    token = create_token({"user_id": user_id, "lab_id": lab_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def lab(make_lab):
    return make_lab(name="Edge Test Lab")


@pytest.fixture
def admin_user(make_lab_user, lab):
    return make_lab_user(lab_id=lab.id, role="admin")


@pytest.fixture
def public_key_pem():
    # A minimal but well-formed PEM. The control plane only fingerprints it.
    return (
        "-----BEGIN PUBLIC KEY-----\n"
        "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtest_key_for_unit_tests\n"
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n"
        "-----END PUBLIC KEY-----\n"
    )


# ── identity helpers ─────────────────────────────────────────────────────────

def test_new_device_id_is_unique_and_prefixed():
    a = identity.new_device_id()
    b = identity.new_device_id()
    assert a != b
    assert a.startswith("EDG") and len(a) == 29


def test_fingerprint_is_stable_under_whitespace(public_key_pem):
    fp1 = identity.fingerprint_pem(public_key_pem)
    fp2 = identity.fingerprint_pem(public_key_pem + "\n   \n")
    assert fp1 == fp2
    assert fp1.startswith("sha256:")


def test_task_signature_round_trip():
    uid = identity.new_task_uid()
    payload = {"text": "hello", "model": "qwen2:1.5b"}
    sig = identity.sign_task(uid, "ai.translate", payload)
    assert identity.verify_task_signature(uid, "ai.translate", payload, sig)
    assert not identity.verify_task_signature(uid, "ai.translate",
                                              {"text": "tampered"}, sig)


# ── registry ─────────────────────────────────────────────────────────────────

def test_register_device_creates_active_after_heartbeat(db, lab, admin_user,
                                                        public_key_pem):
    d = registry.register_device(
        db, lab_id=lab.id, owner_user_id=admin_user.id,
        public_key_pem=public_key_pem, role_mode="personal",
    )
    assert d.status == "pending"
    assert d.cert_fingerprint and d.cert_fingerprint.startswith("sha256:")
    db.commit()

    after = registry.heartbeat(db, device_id=d.device_id, agent_version="0.1")
    db.commit()
    assert after.status == "active"
    assert after.last_seen_at is not None


def test_register_rejects_duplicate_public_key(db, lab, admin_user, public_key_pem):
    registry.register_device(db, lab_id=lab.id, owner_user_id=admin_user.id,
                             public_key_pem=public_key_pem, role_mode="personal")
    db.commit()
    with pytest.raises(registry.RegistryError):
        registry.register_device(db, lab_id=lab.id, owner_user_id=admin_user.id,
                                 public_key_pem=public_key_pem,
                                 role_mode="personal")


def test_quarantine_then_reinstate(db, lab, admin_user, public_key_pem):
    d = registry.register_device(db, lab_id=lab.id, owner_user_id=admin_user.id,
                                 public_key_pem=public_key_pem,
                                 role_mode="personal")
    registry.heartbeat(db, device_id=d.device_id)
    db.commit()
    registry.quarantine(db, d, reason="manual review", actor_user_id=admin_user.id)
    db.commit()
    assert d.status == "quarantined"
    registry.reinstate(db, d, actor_user_id=admin_user.id)
    db.commit()
    assert d.status == "active"


def test_revoked_device_cannot_be_reinstated(db, lab, admin_user, public_key_pem):
    d = registry.register_device(db, lab_id=lab.id, owner_user_id=admin_user.id,
                                 public_key_pem=public_key_pem,
                                 role_mode="personal")
    registry.heartbeat(db, device_id=d.device_id)
    registry.revoke(db, d, reason="lost device", actor_user_id=admin_user.id)
    db.commit()
    with pytest.raises(registry.RegistryError):
        registry.reinstate(db, d, actor_user_id=admin_user.id)


# ── trust ────────────────────────────────────────────────────────────────────

def test_trust_score_clamps_and_logs_event(db, lab, admin_user, public_key_pem):
    d = registry.register_device(db, lab_id=lab.id, owner_user_id=admin_user.id,
                                 public_key_pem=public_key_pem,
                                 role_mode="personal")
    db.commit()
    starting = d.trust_score
    new = trust_mod.adjust(db, d, reason="task_completed", actor_user_id=None)
    assert new == min(edge_config.EDGE_TRUST_MAX, starting + trust_mod.DELTAS["task_completed"])


def test_attestation_failure_quarantines(db, lab, admin_user, public_key_pem):
    d = registry.register_device(db, lab_id=lab.id, owner_user_id=admin_user.id,
                                 public_key_pem=public_key_pem,
                                 role_mode="personal")
    registry.heartbeat(db, device_id=d.device_id)
    db.commit()
    # one big hit
    trust_mod.adjust(db, d, reason="attestation_failure", actor_user_id=None)
    db.commit()
    assert d.status == "quarantined"


def test_privacy_floor_blocks_low_trust():
    assert trust_mod.passes_for_privacy(50.0, "standard")
    assert not trust_mod.passes_for_privacy(50.0, "phi")
    assert trust_mod.passes_for_privacy(90.0, "phi")


# ── scheduler ────────────────────────────────────────────────────────────────

def _make_active_device(db, lab, admin_user, pem_key, *, trust=80.0):
    d = registry.register_device(db, lab_id=lab.id, owner_user_id=admin_user.id,
                                 public_key_pem=pem_key,
                                 role_mode="personal",
                                 capabilities={"kinds": list(
                                     edge_config.ALLOWED_TASK_KINDS)})
    registry.heartbeat(db, device_id=d.device_id)
    d.trust_score = trust
    db.commit()
    return d


def test_submit_and_claim_round_trip(db, lab, admin_user, public_key_pem):
    d = _make_active_device(db, lab, admin_user, public_key_pem)
    t = scheduler.submit_task(
        db, lab_id=lab.id, kind="ai.translate",
        payload={"text": "hello", "target": "ar"},
        submitted_by_user_id=admin_user.id,
    )
    db.commit()
    assert t.status == "pending"
    assert t.payload_sig

    claimed = scheduler.claim_next_task(db, d)
    db.commit()
    assert claimed is not None
    assert claimed.task_uid == t.task_uid
    assert claimed.status == "dispatched"
    assert claimed.device_id == d.device_id
    assert claimed.attempts == 1


def test_phi_task_blocked_for_low_trust_device(db, lab, admin_user, public_key_pem):
    d = _make_active_device(db, lab, admin_user, public_key_pem, trust=50.0)
    t = scheduler.submit_task(
        db, lab_id=lab.id, kind="ai.summarize_report",
        privacy_level="phi", payload={"text": "x"},
    )
    db.commit()
    claimed = scheduler.claim_next_task(db, d)
    assert claimed is None


def test_reject_unknown_kind(db, lab):
    with pytest.raises(scheduler.SchedulerError):
        scheduler.submit_task(db, lab_id=lab.id, kind="some.evil.kind",
                              payload={})


def test_idempotency_returns_existing(db, lab, admin_user, public_key_pem):
    t1 = scheduler.submit_task(db, lab_id=lab.id, kind="diag.ping",
                               idempotency_key="abc123")
    t2 = scheduler.submit_task(db, lab_id=lab.id, kind="diag.ping",
                               idempotency_key="abc123")
    db.commit()
    assert t1.task_uid == t2.task_uid


def test_complete_task_marks_completed(db, lab, admin_user, public_key_pem):
    d = _make_active_device(db, lab, admin_user, public_key_pem)
    scheduler.submit_task(db, lab_id=lab.id, kind="diag.ping")
    db.commit()
    t = scheduler.claim_next_task(db, d)
    db.commit()
    scheduler.complete_task(db, t, result={"pong": True})
    db.commit()
    assert t.status == "completed"
    assert t.result == {"pong": True}


def test_fail_task_requeues_until_max_attempts(db, lab, admin_user, public_key_pem):
    d = _make_active_device(db, lab, admin_user, public_key_pem)
    scheduler.submit_task(db, lab_id=lab.id, kind="diag.ping", max_attempts=2)
    db.commit()
    t = scheduler.claim_next_task(db, d)
    db.commit()
    scheduler.fail_task(db, t, error="transient")
    db.commit()
    # First failure → re-queued
    assert t.status == "pending"

    # Pick again — should fail terminally on the 2nd attempt
    t2 = scheduler.claim_next_task(db, d)
    db.commit()
    assert t2.task_uid == t.task_uid
    scheduler.fail_task(db, t2, error="permanent")
    db.commit()
    assert t2.status == "failed"


def test_sweep_stale_marks_timeouts(db, lab, admin_user, public_key_pem):
    d = _make_active_device(db, lab, admin_user, public_key_pem)
    scheduler.submit_task(db, lab_id=lab.id, kind="diag.ping",
                          timeout_s=5)
    db.commit()
    t = scheduler.claim_next_task(db, d)
    db.commit()
    # Force stale dispatch in the past
    t.dispatched_at = datetime.now(timezone.utc) - timedelta(seconds=120)
    db.commit()
    n = scheduler.sweep_stale(db)
    db.commit()
    assert n >= 1


# ── policy ───────────────────────────────────────────────────────────────────

def test_policy_default_when_unset(db, lab):
    pol = policy_mod.get_policy(db, lab.id)
    assert pol.max_concurrent_per_device == 2
    assert pol.kill_switch is False


def test_policy_upsert_and_kind_filter(db, lab, admin_user, public_key_pem):
    policy_mod.upsert_policy(db, lab_id=lab.id, actor_user_id=admin_user.id,
                             deny_kinds=["ai.embed"])
    db.commit()
    pol = policy_mod.get_policy(db, lab.id)
    assert pol.deny_kinds == ["ai.embed"]
    assert pol.task_kind_allowed("ai.translate")
    assert not pol.task_kind_allowed("ai.embed")

    # Submitting a denied kind should fail.
    with pytest.raises(scheduler.SchedulerError):
        scheduler.submit_task(db, lab_id=lab.id, kind="ai.embed")


def test_kill_switch_blocks_submit(db, lab, admin_user):
    policy_mod.upsert_policy(db, lab_id=lab.id, actor_user_id=admin_user.id,
                             kill_switch=True)
    db.commit()
    with pytest.raises(scheduler.SchedulerError):
        scheduler.submit_task(db, lab_id=lab.id, kind="diag.ping")


# ── governance / canary rollout ──────────────────────────────────────────────

def test_register_model_lifecycle(db, admin_user):
    m = governance.register_model(db, name="qwen2", version="1.5b-q4",
                                  size_mb=1024.0, actor_user_id=admin_user.id)
    db.commit()
    assert m.status == "draft"
    governance.set_model_status(db, model_uid=m.model_uid,
                                status="active", rollout_pct=100.0,
                                actor_user_id=admin_user.id)
    db.commit()
    assert m.status == "active"
    assert m.rollout_pct == 100.0


def test_pick_models_for_active_assignment(db, lab, admin_user, public_key_pem):
    d = _make_active_device(db, lab, admin_user, public_key_pem)
    m = governance.register_model(db, name="qwen2", version="1.5b-q4")
    governance.set_model_status(db, model_uid=m.model_uid, status="active",
                                rollout_pct=100.0)
    governance.assign_model(db, model_uid=m.model_uid, lab_id=lab.id)
    db.commit()
    picks = governance.pick_models_for(db, d)
    assert any(p["model_uid"] == m.model_uid for p in picks)


# ── HTTP — operator API smoke ────────────────────────────────────────────────

def test_http_register_and_list(client, db, lab, admin_user, public_key_pem):
    
    headers = _auth(admin_user.id, lab.id, "admin")

    r = client.post("/edge/devices/register", json={
        "public_key_pem": public_key_pem,
        "role_mode": "personal",
        "display_name": "test-pc",
    }, headers=headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["device_id"].startswith("EDG")
    assert body["agent_token"]

    r2 = client.get("/edge/devices", headers=headers)
    assert r2.status_code == 200
    assert any(d["device_id"] == body["device_id"] for d in r2.json())


def test_http_agent_heartbeat_claims_task(client, db, lab, admin_user,
                                          public_key_pem):
    
    headers = _auth(admin_user.id, lab.id, "admin")

    reg = client.post("/edge/devices/register", json={
        "public_key_pem": public_key_pem,
        "role_mode": "personal",
        "capabilities": {"kinds": ["diag.ping"]},
    }, headers=headers).json()
    agent_token = reg["agent_token"]

    # Promote trust so default policy.min_trust_score (50) is met
    d = db.query(EdgeDevice).filter(EdgeDevice.device_id == reg["device_id"]).first()
    d.trust_score = 90.0
    d.status = "active"
    db.commit()

    sub = client.post("/edge/tasks", json={
        "kind": "diag.ping",
        "payload": {"hello": True},
        "priority": 1,
    }, headers=headers)
    assert sub.status_code == 201, sub.text

    hb = client.post("/edge/agent/heartbeat", json={
        "agent_version": "test", "telemetry": {"cpu_pct": 5.0},
    }, headers={"Authorization": f"Bearer {agent_token}"})
    assert hb.status_code == 200, hb.text
    body = hb.json()
    assert body["task"] is not None
    assert body["task"]["kind"] == "diag.ping"


def test_http_agent_token_invalid_signature_rejected(client, db, lab,
                                                     admin_user, public_key_pem):
    
    headers = _auth(admin_user.id, lab.id, "admin")
    reg = client.post("/edge/devices/register", json={
        "public_key_pem": public_key_pem, "role_mode": "personal",
    }, headers=headers).json()

    bad = reg["device_id"] + ".0000000000000000000000000000000000000000000000000000000000000000"
    r = client.post("/edge/agent/heartbeat", json={},
                    headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 401
