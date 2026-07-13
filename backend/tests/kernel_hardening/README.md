# Kernel Hardening — Production Readiness Suite

## Test Categories

| Category | File | Description |
|----------|------|-------------|
| Chaos | `test_chaos_engineering.py` | Inject failures into all kernel subsystems; verify graceful recovery |
| Stress | `test_stress.py` | 10k-100k events, 1000 concurrent tasks, high-frequency lookups |
| Leak | `test_memory_leaks.py` | Detect object, event, service, DI, event-store leaks via weakref |
| Performance | `test_performance_baseline.py` | Cold/warm start, shutdown, lookup/dispatch latency baselines |
| Security | `test_security_hardening.py` | Plugin isolation, unauthorized access, privilege escalation, tampering |
| Recovery | `test_recovery.py` | Crash, plugin crash, outbox/DLQ recovery, circuit breaker auto-recovery |
| Observability | `test_observability.py` | Health, readiness, liveness, state transitions, component registration |

## Running

```bash
# All hardening tests
cd <repo-root> && python -m pytest backend/tests/kernel_hardening/ -v

# By category
python -m pytest backend/tests/kernel_hardening/ -k "chaos" -v
python -m pytest backend/tests/kernel_hardening/ -k "stress" -v
python -m pytest backend/tests/kernel_hardening/ -k "memory" -v
python -m pytest backend/tests/kernel_hardening/ -k "performance" -v
python -m pytest backend/tests/kernel_hardening/ -k "security" -v
python -m pytest backend/tests/kernel_hardening/ -k "recovery" -v
python -m pytest backend/tests/kernel_hardening/ -k "observability" -v

# Slow tests only (stress + performance)
python -m pytest backend/tests/kernel_hardening/ -m "slow" -v

# Quick smoke test (skip slow)
python -m pytest backend/tests/kernel_hardening/ -m "not slow" -v
```

## Quality Gates

Before production certification, run:

```bash
cd <repo-root> && python -m pytest backend/tests/kernel/ backend/tests/kernel_hardening/ -v
```

## Production Certification Checklist

- [ ] All chaos tests pass (subsystems recover gracefully)
- [ ] 100k events in < 15s
- [ ] 10k service lookups in < 200ms
- [ ] 10k DI lookups in < 300ms
- [ ] 10k event dispatches in < 1s
- [ ] Cold start < 5s
- [ ] Shutdown < 2s
- [ ] No memory leaks detected
- [ ] Plugin sandbox blocks all dangerous modules
- [ ] Circuit breaker auto-recovers
- [ ] Dead letter queue supports replay
- [ ] Task retry with exponential backoff
