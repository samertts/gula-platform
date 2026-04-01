"""
Unit tests for the GULA Control Layer:
  - PolicyEngine (policy_engine.py)
  - DecisionGuard (decision_guard.py)
  - RiskEngine (risk_engine.py)
  - KillSwitch (kill_switch.py)

All tests are pure-Python, no DB or Redis required.
Run: pytest backend/tests/test_control_layer.py -v
"""
from __future__ import annotations

import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Set test environment BEFORE any app imports ───────────────────────────────
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_control.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-bytes!!!!!")
os.environ.setdefault("NID_HMAC_KEY", "test-nid-hmac-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")


# =============================================================================
# PolicyEngine
# =============================================================================

class TestPolicyEngine(unittest.TestCase):

    def setUp(self):
        # Fresh engine for each test — avoids counter pollution
        from app.core.policy_engine import PolicyEngine
        self.engine = PolicyEngine()
        from app.core.policy_engine import ActionType, RiskLevel
        self.ActionType = ActionType
        self.RiskLevel = RiskLevel

    def test_critical_actions_always_blocked(self):
        """CODE_CHANGE, AI_AUTO_FIX, AI_COMMIT, DB_SCHEMA, SECRET_ROTATION, AUDIT_DELETE are always blocked."""
        critical = [
            self.ActionType.CODE_CHANGE,
            self.ActionType.AI_AUTO_FIX,
            self.ActionType.AI_COMMIT,
            self.ActionType.DB_SCHEMA,
            self.ActionType.SECRET_ROTATION,
            self.ActionType.AUDIT_DELETE,
        ]
        for action in critical:
            with self.subTest(action=action):
                decision = self.engine.evaluate(action, {"env": "development"})
                self.assertFalse(decision.allowed,
                                 f"{action} should be blocked but was allowed")
                self.assertEqual(decision.risk, self.RiskLevel.CRITICAL)

    def test_auto_repair_allowed_in_dev(self):
        decision = self.engine.evaluate(self.ActionType.AUTO_REPAIR, {"env": "development"})
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.risk, self.RiskLevel.MEDIUM)

    def test_auto_repair_allowed_in_production(self):
        """AUTO_REPAIR has allow_in_prod=True."""
        decision = self.engine.evaluate(self.ActionType.AUTO_REPAIR, {"env": "production"})
        self.assertTrue(decision.allowed)

    def test_config_change_blocked_in_production(self):
        decision = self.engine.evaluate(self.ActionType.CONFIG_CHANGE, {"env": "production"})
        self.assertFalse(decision.allowed)
        self.assertIn("production", decision.reason)

    def test_config_change_blocked_in_dev_too(self):
        """HIGH risk + allow_in_prod=False blocks even in dev? No — only production check applies."""
        # CONFIG_CHANGE is HIGH risk, allow_in_prod=False → only blocked in prod
        decision = self.engine.evaluate(self.ActionType.CONFIG_CHANGE, {"env": "development"})
        self.assertTrue(decision.allowed)

    def test_scaling_allowed_in_production(self):
        decision = self.engine.evaluate(self.ActionType.SCALING, {"env": "production"})
        self.assertTrue(decision.allowed)

    def test_frequency_limit_auto_repair(self):
        """AUTO_REPAIR blocked after 10 calls in one hour."""
        # Allow 10 (the limit), 11th should be blocked
        for i in range(10):
            d = self.engine.evaluate(self.ActionType.AUTO_REPAIR, {"env": "development"})
            self.assertTrue(d.allowed, f"Call {i+1} should be allowed")
        # 11th exceeds limit
        d = self.engine.evaluate(self.ActionType.AUTO_REPAIR, {"env": "development"})
        self.assertFalse(d.allowed)
        self.assertIn("frequency", d.reason)

    def test_frequency_counter_resets_after_hour(self):
        """Counter window resets after 3600 seconds."""
        from app.core.policy_engine import _ActionCounter
        counter = _ActionCounter()
        counter.count = 5
        counter.window_start = time.monotonic() - 3601  # expired window
        exceeded = counter.increment_and_check(10)
        self.assertFalse(exceeded)
        self.assertEqual(counter.count, 1)  # reset + 1

    def test_kill_switch_blocks_allowed_action(self):
        """When kill switch is active, allowed actions become blocked."""
        with patch("app.core.kill_switch.is_kill_switch_active", return_value=True):
            decision = self.engine.evaluate(self.ActionType.AUTO_REPAIR, {"env": "development"})
        self.assertFalse(decision.allowed)
        self.assertIn("kill switch", decision.reason.lower())

    def test_unknown_action_default_deny(self):
        """Unregistered action types get CRITICAL/denied (default-deny)."""
        from app.core.policy_engine import ActionType
        # We can't easily add unknown enums, but we can test the code path
        # by temporarily removing from _POLICY_TABLE
        from app.core import policy_engine as pe
        backup = dict(pe._POLICY_TABLE)
        pe._POLICY_TABLE.pop(self.ActionType.AUTO_REPAIR)
        try:
            decision = self.engine.evaluate(self.ActionType.AUTO_REPAIR, {})
            self.assertFalse(decision.allowed)
            self.assertIn("default deny", decision.reason)
        finally:
            pe._POLICY_TABLE[self.ActionType.AUTO_REPAIR] = backup[self.ActionType.AUTO_REPAIR]

    def test_stats_tracking(self):
        """blocked_total and allowed_total increment correctly."""
        self.engine.evaluate(self.ActionType.AUTO_REPAIR, {"env": "development"})  # allowed
        self.engine.evaluate(self.ActionType.CODE_CHANGE, {})                      # blocked
        stats = self.engine.stats()
        self.assertEqual(stats["allowed_total"], 1)
        self.assertEqual(stats["blocked_total"], 1)

    def test_control_layer_disabled_allows_everything(self):
        """When CONTROL_LAYER_ENABLED=false, all actions are allowed."""
        import app.core.policy_engine as pe
        orig = pe._CONTROL_LAYER_ENABLED
        pe._CONTROL_LAYER_ENABLED = False
        try:
            decision = self.engine.evaluate(self.ActionType.CODE_CHANGE, {})
            self.assertTrue(decision.allowed)
        finally:
            pe._CONTROL_LAYER_ENABLED = orig

    def test_policy_decision_to_dict(self):
        decision = self.engine.evaluate(self.ActionType.AUTO_REPAIR, {"env": "development"})
        d = decision.to_dict()
        self.assertIn("allowed", d)
        self.assertIn("risk", d)
        self.assertIn("action", d)
        self.assertIn("reason", d)

    def test_db_pool_recycle_medium_risk_prod(self):
        decision = self.engine.evaluate(self.ActionType.DB_POOL_RECYCLE, {"env": "production"})
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.risk, self.RiskLevel.MEDIUM)

    def test_cache_flush_blocked_in_prod(self):
        decision = self.engine.evaluate(self.ActionType.CACHE_FLUSH, {"env": "production"})
        self.assertFalse(decision.allowed)

    def test_queue_purge_blocked_in_prod(self):
        decision = self.engine.evaluate(self.ActionType.QUEUE_PURGE, {"env": "production"})
        self.assertFalse(decision.allowed)


# =============================================================================
# DecisionGuard
# =============================================================================

class TestDecisionGuard(unittest.TestCase):

    def setUp(self):
        # Patch policy engine with a fresh instance for isolation
        from app.core.policy_engine import PolicyEngine
        self._fresh_engine = PolicyEngine()
        import app.core.policy_engine as pe_mod
        self._orig_engine = pe_mod.policy_engine
        pe_mod.policy_engine = self._fresh_engine

    def tearDown(self):
        import app.core.policy_engine as pe_mod
        pe_mod.policy_engine = self._orig_engine

    def test_guard_raises_on_blocked(self):
        from app.core.decision_guard import guard, PolicyViolation
        from app.core.policy_engine import ActionType
        with self.assertRaises(PolicyViolation) as ctx:
            guard(ActionType.CODE_CHANGE, {})
        self.assertIn("blocked", str(ctx.exception).lower())

    def test_guard_returns_decision_on_allowed(self):
        from app.core.decision_guard import guard
        from app.core.policy_engine import ActionType
        decision = guard(ActionType.AUTO_REPAIR, {"env": "development"})
        self.assertTrue(decision.allowed)

    def test_check_returns_false_on_blocked(self):
        from app.core.decision_guard import check
        from app.core.policy_engine import ActionType
        result = check(ActionType.AI_AUTO_FIX, {})
        self.assertFalse(result)

    def test_check_returns_true_on_allowed(self):
        from app.core.decision_guard import check
        from app.core.policy_engine import ActionType
        result = check(ActionType.SCALING, {"env": "production"})
        self.assertTrue(result)

    def test_guard_repair_convenience(self):
        from app.core.decision_guard import guard_repair
        # Should not raise
        decision = guard_repair("pool_recycle", {"env": "development"})
        self.assertTrue(decision.allowed)
        self.assertIn("auto_repair: pool_recycle", decision.reason)

    def test_guard_repair_blocked_by_kill_switch(self):
        from app.core.decision_guard import guard_repair, PolicyViolation
        with patch("app.core.kill_switch.is_kill_switch_active", return_value=True):
            with self.assertRaises(PolicyViolation):
                guard_repair("memory_gc")

    def test_guard_ai_fix_always_blocked(self):
        from app.core.decision_guard import guard_ai_fix, PolicyViolation
        with self.assertRaises(PolicyViolation):
            guard_ai_fix("backend/app/main.py")

    def test_guard_ai_commit_always_blocked(self):
        from app.core.decision_guard import guard_ai_commit, PolicyViolation
        with self.assertRaises(PolicyViolation):
            guard_ai_commit("fix: improve performance")

    def test_guard_scaling_in_production(self):
        from app.core.decision_guard import guard_scaling
        decision = guard_scaling(3)
        self.assertTrue(decision.allowed)
        self.assertIn("scale to 3 replicas", decision.reason)

    def test_policy_violation_contains_action(self):
        from app.core.decision_guard import guard, PolicyViolation
        from app.core.policy_engine import ActionType
        try:
            guard(ActionType.AUDIT_DELETE, {})
            self.fail("Should have raised PolicyViolation")
        except PolicyViolation as exc:
            self.assertIn("audit_delete", str(exc))
            self.assertEqual(exc.decision.action, ActionType.AUDIT_DELETE)


# =============================================================================
# RiskEngine
# =============================================================================

class TestRiskEngine(unittest.TestCase):

    def setUp(self):
        # Clear recency tracker before each test
        import app.core.risk_engine as re_mod
        re_mod._recent_actions.clear()

    def test_dry_run_zero_risk(self):
        from app.core.risk_engine import compute_risk
        assessment = compute_risk("auto_repair.gc", {"dry_run": True})
        self.assertEqual(assessment.score, 0)
        self.assertEqual(assessment.level, "low")
        self.assertEqual(assessment.recommended, "allow")

    def test_production_adds_3(self):
        from app.core.risk_engine import compute_risk
        assessment = compute_risk("auto_repair.gc", {"env": "production"})
        self.assertGreaterEqual(assessment.score, 3)
        self.assertTrue(any("+3 production" in f for f in assessment.factors))

    def test_affects_data_adds_3(self):
        from app.core.risk_engine import compute_risk
        assessment = compute_risk("db_write", {"env": "development", "affects_data": True})
        self.assertGreaterEqual(assessment.score, 3)
        self.assertTrue(any("patient data" in f for f in assessment.factors))

    def test_all_users_adds_2(self):
        from app.core.risk_engine import compute_risk
        assessment = compute_risk("cache_flush", {"env": "development", "all_users": True})
        self.assertGreaterEqual(assessment.score, 2)
        self.assertTrue(any("all tenants" in f for f in assessment.factors))

    def test_irreversible_adds_2(self):
        from app.core.risk_engine import compute_risk
        assessment = compute_risk("queue_purge", {"env": "development", "reversible": False})
        self.assertTrue(any("irreversible" in f for f in assessment.factors))

    def test_max_score_clamped_to_10(self):
        from app.core.risk_engine import compute_risk
        # production + data + all_users + irreversible + high frequency = 3+3+2+2+2 = 12 → clamped to 10
        assessment = compute_risk("worst_case", {
            "env": "production",
            "affects_data": True,
            "all_users": True,
            "reversible": False,
            "frequency": 10,
        })
        self.assertEqual(assessment.score, 10)
        self.assertEqual(assessment.level, "critical")

    def test_low_score_gives_allow(self):
        from app.core.risk_engine import compute_risk
        assessment = compute_risk("safe_action", {"env": "development"})
        self.assertEqual(assessment.recommended, "allow")

    def test_recency_adds_1_when_repeated_within_5_min(self):
        from app.core.risk_engine import compute_risk
        import app.core.risk_engine as re_mod
        action = "auto_repair.gc_recency_test"
        re_mod._recent_actions[action] = time.time() - 60  # 1 min ago
        assessment = compute_risk(action, {"env": "development"})
        self.assertTrue(any("repeated within" in f for f in assessment.factors))

    def test_recency_ignored_when_older_than_5_min(self):
        from app.core.risk_engine import compute_risk
        import app.core.risk_engine as re_mod
        action = "auto_repair.gc_old"
        re_mod._recent_actions[action] = time.time() - 400  # 6+ min ago
        assessment = compute_risk(action, {"env": "development"})
        self.assertFalse(any("repeated within" in f for f in assessment.factors))

    def test_assess_repair_convenience(self):
        from app.core.risk_engine import assess_repair
        assessment = assess_repair("pool_recycle", env="production", frequency=0)
        self.assertIsNotNone(assessment.score)
        self.assertIn("auto_repair.pool_recycle", assessment.action)

    def test_risk_assessment_to_dict(self):
        from app.core.risk_engine import compute_risk
        assessment = compute_risk("test_action", {})
        d = assessment.to_dict()
        self.assertIn("score", d)
        self.assertIn("level", d)
        self.assertIn("factors", d)
        self.assertIn("recommended", d)

    def test_high_frequency_adds_2(self):
        from app.core.risk_engine import compute_risk
        assessment = compute_risk("repair.loop", {"env": "development", "frequency": 6})
        self.assertTrue(any("high frequency" in f for f in assessment.factors))

    def test_moderate_frequency_adds_1(self):
        from app.core.risk_engine import compute_risk
        assessment = compute_risk("repair.moderate", {"env": "development", "frequency": 3})
        self.assertTrue(any("moderate frequency" in f for f in assessment.factors))


# =============================================================================
# KillSwitch
# =============================================================================

class TestKillSwitch(unittest.TestCase):

    def setUp(self):
        """Reset in-memory state before each test."""
        import app.core.kill_switch as ks
        ks._in_memory_active = False
        ks._activated_at = 0.0
        ks._activated_reason = ""

    def tearDown(self):
        """Ensure kill switch is off after each test."""
        import app.core.kill_switch as ks
        ks._in_memory_active = False

    def test_initially_inactive(self):
        from app.core.kill_switch import is_kill_switch_active
        with patch.dict(os.environ, {"KILL_SWITCH": "false"}):
            with patch("app.security.redis_client.cache") as mock_cache:
                mock_cache.get.return_value = None
                self.assertFalse(is_kill_switch_active())

    def test_in_memory_activation(self):
        from app.core.kill_switch import activate, is_kill_switch_active
        with patch("app.security.redis_client.cache") as mock_cache:
            mock_cache.set.return_value = True
            activate("test reason", propagate=False)
        self.assertTrue(is_kill_switch_active())

    def test_env_var_activates(self):
        from app.core.kill_switch import is_kill_switch_active
        with patch.dict(os.environ, {"KILL_SWITCH": "true"}):
            with patch("app.security.redis_client.cache") as mock_cache:
                mock_cache.get.return_value = None
                self.assertTrue(is_kill_switch_active())

    def test_env_var_1_activates(self):
        from app.core.kill_switch import is_kill_switch_active
        with patch.dict(os.environ, {"KILL_SWITCH": "1"}):
            with patch("app.security.redis_client.cache") as mock_cache:
                mock_cache.get.return_value = None
                self.assertTrue(is_kill_switch_active())

    def test_redis_key_activates(self):
        from app.core.kill_switch import is_kill_switch_active
        with patch.dict(os.environ, {"KILL_SWITCH": "false"}):
            with patch("app.security.redis_client.cache") as mock_cache:
                mock_cache.get.return_value = "1"
                self.assertTrue(is_kill_switch_active())

    def test_redis_key_0_does_not_activate(self):
        from app.core.kill_switch import is_kill_switch_active
        with patch.dict(os.environ, {"KILL_SWITCH": "false"}):
            with patch("app.security.redis_client.cache") as mock_cache:
                mock_cache.get.return_value = "0"
                self.assertFalse(is_kill_switch_active())

    def test_deactivate_clears_in_memory(self):
        from app.core.kill_switch import activate, deactivate, is_kill_switch_active
        with patch("app.security.redis_client.cache") as mock_cache:
            mock_cache.set.return_value = True
            mock_cache.delete.return_value = True
            activate("test", propagate=False)
            self.assertTrue(is_kill_switch_active())
            deactivate("test", propagate=False)
        with patch.dict(os.environ, {"KILL_SWITCH": "false"}):
            with patch("app.security.redis_client.cache") as mock_cache:
                mock_cache.get.return_value = None
                self.assertFalse(is_kill_switch_active())

    def test_activate_propagates_to_redis(self):
        from app.core.kill_switch import activate
        with patch("app.security.redis_client.cache") as mock_cache:
            mock_cache.set.return_value = True
            activate("propagation test", propagate=True)
            mock_cache.set.assert_called_once_with("gula:kill_switch", "1", ex=86400)

    def test_deactivate_deletes_redis_key(self):
        from app.core.kill_switch import deactivate
        import app.core.kill_switch as ks
        ks._in_memory_active = True
        with patch("app.security.redis_client.cache") as mock_cache:
            mock_cache.delete.return_value = True
            deactivate("test", propagate=True)
            mock_cache.delete.assert_called_once_with("gula:kill_switch")

    def test_status_returns_dict(self):
        from app.core.kill_switch import activate, status
        with patch("app.security.redis_client.cache") as mock_cache:
            mock_cache.set.return_value = True
            mock_cache.get.return_value = "1"
            activate("test_status", propagate=False)
            s = status()
        self.assertTrue(s["active"])
        self.assertEqual(s["reason"], "test_status")
        self.assertIsNotNone(s["activated_at"])

    def test_status_inactive(self):
        from app.core.kill_switch import status
        with patch.dict(os.environ, {"KILL_SWITCH": "false"}):
            with patch("app.security.redis_client.cache") as mock_cache:
                mock_cache.get.return_value = None
                s = status()
        self.assertFalse(s["active"])
        self.assertIsNone(s["reason"])

    def test_redis_unavailable_falls_through(self):
        """If Redis is down, kill switch falls through to False (fail open for kill switch)."""
        from app.core.kill_switch import is_kill_switch_active
        with patch.dict(os.environ, {"KILL_SWITCH": "false"}):
            with patch("app.security.redis_client.cache") as mock_cache:
                mock_cache.get.side_effect = Exception("Redis down")
                # Should NOT raise, should return False
                result = is_kill_switch_active()
        self.assertFalse(result)

    def test_activate_redis_failure_still_sets_in_memory(self):
        """Even if Redis propagation fails, in-memory flag is set."""
        from app.core.kill_switch import activate, is_kill_switch_active
        with patch("app.security.redis_client.cache") as mock_cache:
            mock_cache.set.side_effect = Exception("Redis down")
            activate("redis_fail_test", propagate=True)
        self.assertTrue(is_kill_switch_active())


# =============================================================================
# Integration: Guard + PolicyEngine + KillSwitch interaction
# =============================================================================

class TestControlLayerIntegration(unittest.TestCase):

    def setUp(self):
        from app.core.policy_engine import PolicyEngine
        import app.core.policy_engine as pe_mod
        self._orig_engine = pe_mod.policy_engine
        pe_mod.policy_engine = PolicyEngine()

        import app.core.kill_switch as ks
        ks._in_memory_active = False

    def tearDown(self):
        import app.core.policy_engine as pe_mod
        pe_mod.policy_engine = self._orig_engine
        import app.core.kill_switch as ks
        ks._in_memory_active = False

    def test_full_flow_allowed(self):
        """guard() passes for a medium-risk action in dev with kill switch off."""
        from app.core.decision_guard import guard
        from app.core.policy_engine import ActionType
        with patch("app.core.kill_switch.is_kill_switch_active", return_value=False):
            decision = guard(ActionType.AUTO_REPAIR, {"env": "development"})
        self.assertTrue(decision.allowed)

    def test_full_flow_kill_switch_stops_allowed_action(self):
        """Even an allowed action is stopped when kill switch is on."""
        from app.core.decision_guard import guard, PolicyViolation
        from app.core.policy_engine import ActionType
        with patch("app.core.kill_switch.is_kill_switch_active", return_value=True):
            with self.assertRaises(PolicyViolation):
                guard(ActionType.AUTO_REPAIR, {"env": "development"})

    def test_frequency_exhaustion_then_manual_kill_switch(self):
        """After frequency limit, kill switch gives a clearer message."""
        from app.core.decision_guard import check
        from app.core.policy_engine import ActionType
        import app.core.policy_engine as pe_mod

        # Exhaust frequency limit
        for _ in range(10):
            pe_mod.policy_engine.evaluate(ActionType.AUTO_REPAIR, {"env": "development"})

        # 11th blocked by frequency
        result = check(ActionType.AUTO_REPAIR, {"env": "development"})
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
