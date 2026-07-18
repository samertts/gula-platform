# Core — Infrastructure & Cross-Cutting Modules

This module contains core infrastructure services used across the platform: `startup_guard.py` (readiness gating), `self_healing.py` (circuit breaker, degraded mode), `auto_repair.py` (GC, pool recycle), `feature_flags.py` (per-tenant), `sndhs_flags.py` (deployment toggles), `policy_engine.py`, `logging_config.py` (structured JSON), `cache_manager.py`, `events.py`, `resilience.py`, `kill_switch.py`, `risk_engine.py`, `runtime_guard.py`, `idempotency.py`, `decision_guard.py`, `ai_dataset_flags.py`.
