# Kernel Testing Guide

## Architecture

The Kernel test suite is organized by domain into focused test files, replacing
the previous monolithic `test_kernel.py` (1517 lines).

```
tests/kernel/
├── conftest.py              # Shared fixtures (reset_kernel, kernel, event_bus, descriptors)
├── test_runtime.py          # Kernel singleton, lifecycle, DI container, descriptor defaults
├── test_bootloader.py       # Bootloader phase enable/disable
├── test_lifecycle.py        # LifecycleManager, StartupManager, ShutdownManager
├── test_services.py         # ServiceRegistry
├── test_context.py          # ApplicationContext
├── test_event_bus.py        # EventBus publish/subscribe
├── test_event_store.py      # EventStore save/get/list
├── test_events.py           # Event defaults, event replay
├── test_versioning.py       # EventVersioning, ConfigVersioning
├── test_outbox.py           # OutboxPattern
├── test_inbox.py            # InboxPattern
├── test_retry_queue.py      # RetryQueue
├── test_dead_letter_queue.py # DeadLetterQueue
├── test_feature_flags.py    # FeatureFlag, KillSwitch, Regional, Tenant, Experimental, Capability
├── test_capabilities.py     # CapabilityRegistry
├── test_configuration.py    # ConfigurationRegistry, ConfigurationValidator
├── test_secrets.py          # SecretsLoader
├── test_reload.py           # RuntimeReloader
├── test_tenants.py          # TenantRegistry, Resolver, Isolation, Quotas, Configuration
├── test_gateway.py          # ServiceDiscovery, InternalRouter, HealthRouter
├── test_rate_limiting.py    # RateLimiter
├── test_circuit_breaker.py  # CircuitBreaker, CircuitBreakerManager
├── test_request_validation.py # RequestValidator
├── test_plugin_manager.py   # PluginManager
├── test_plugin_registry.py  # PluginRegistry, PluginDependencyResolver, descriptor defaults
├── test_plugin_permissions.py # PluginPermissionManager
├── test_plugin_versions.py  # PluginVersionManager
├── test_plugin_marketplace.py # PluginMarketplaceInterface
├── test_plugin_sandbox.py   # PluginSandbox
├── test_modules.py          # ModuleRegistry, DependencyResolver, VersionCompatibility, Metadata, Discovery
├── test_scheduler.py        # Scheduler, CronJob defaults, RetryPolicy defaults, Task defaults
├── test_cron.py             # CronEngine register/unregister/list
├── test_task_queue.py       # TaskQueue enqueue/dequeue/priority
├── test_worker_pool.py      # WorkerPool start/stop/size
├── test_priority_queue.py   # PriorityQueue push/pop/peek
├── test_retry.py            # JobRetry limit/backoff
├── test_locks.py            # DistributedLock acquire/release/expiry
├── test_validation.py       # Architecture, Dependency, Security, Performance, Memory, Stress validators
└── test_kernel_integration.py # Full lifecycle, integration module health/stop/warmup
```

## Test Categories

| Marker | Count | Description |
|--------|-------|-------------|
| `kernel` | 162 | All kernel tests (applied via conftest.py) |
| `unit` | 152 | Pure unit tests (no DB, no network) |
| `integration` | 10 | Integration tests (require booted kernel) |

## Fixture Catalog

### Autouse Fixtures
- `reset_kernel` — Resets `Kernel._instance` singleton before and after every test

### Function-Scoped Fixtures
- `kernel` — Returns a `Kernel(config=KernelConfig(environment="test", debug=True))` instance
- `booted_kernel` — Returns a kernel that has gone through `boot()`
- `running_kernel` — Returns a kernel that has gone through `boot()` + `start()`
- `event_bus` — Returns an `EventBus(kernel)` instance
- `sample_event` — Returns `Event(name="test.event", data={"key": "value"})`
- `service_descriptor` — Returns a `ServiceDescriptor` with singleton lifecycle
- `capability_descriptor` — Returns a `CapabilityDescriptor` for "test_cap"
- `plugin_descriptor` — Returns a `PluginDescriptor` with config.read permission
- `module_descriptor` — Returns a `ModuleDescriptor` for "test_module"
- `tenant_descriptor` — Returns a `TenantDescriptor` for "Test Lab" with professional plan

## Running Tests

```bash
# All kernel tests
cd backend && python -m pytest tests/kernel/ -v

# Single test file
cd backend && python -m pytest tests/kernel/test_runtime.py -v

# Single test
cd backend && python -m pytest tests/kernel/test_runtime.py::TestKernelSingleton::test_singleton -v

# By marker
cd backend && python -m pytest tests/kernel/ -m "unit" -v
cd backend && python -m pytest tests/kernel/ -m "integration" -v

# Parallel execution (pytest-xdist)
cd backend && python -m pytest tests/kernel/ -n auto -v

# Coverage
cd <repo-root> && python -m pytest backend/tests/kernel/ --cov=backend.app.kernel --cov-report=term-missing
```

## Coverage Report

Current coverage: **86%** (2315 lines, 333 missing).

### Low-coverage areas needing attention

| Module | Coverage | Gap |
|--------|----------|-----|
| `routes.py` | 0% | API route tests needed (requires FastAPI TestClient) |
| `lifecycle.py` | 72% | Missing stop_all, edge cases |
| `dependencies.py` | 68% | Missing validation edge cases |
| `di_container.py` | 85% | Missing lazy resolution, scope edge cases |
| `sandbox.py` | 84% | Missing module allow/deny edge cases |
| `security.py` (validation) | 81% | Missing issue detection edge cases |

## Test Dependency Graph

```
conftest.py ──────────────────────────────────────────────┐
  ├── reset_kernel (autouse)                               │
  ├── kernel → booted_kernel → running_kernel              │
  ├── event_bus                                            │
  └── sample_event, *_descriptor                           │
                                                           │
test_runtime.py ──── Kernel, DIContainer ──────────────────┤
test_bootloader.py ── Bootloader phases                    │
test_lifecycle.py ─── LifecycleManager, Startup, Shutdown  │
test_services.py ──── ServiceRegistry                      │
test_context.py ───── ApplicationContext                   │
test_event_bus.py ─── EventBus                             │
test_events.py ────── Event defaults, replay               │
test_event_store.py ─ EventStore                           │
test_outbox.py ────── OutboxPattern                        │
test_inbox.py ─────── InboxPattern                         │
test_retry_queue.py ── RetryQueue                          │
test_dead_letter_queue.py ─ DeadLetterQueue                │
test_versioning.py ─── EventVersioning, ConfigVersioning   │
test_feature_flags.py ─ Feature flags (all managers)       │
test_capabilities.py ── CapabilityRegistry                 │
test_configuration.py ─ ConfigurationRegistry, Validator   │
test_secrets.py ────── SecretsLoader                       │
test_reload.py ─────── RuntimeReloader                     │
test_tenants.py ────── All tenant modules                  │
test_gateway.py ────── ServiceDiscovery, Router            │
test_rate_limiting.py ─ RateLimiter                        │
test_circuit_breaker.py ─ CircuitBreaker                   │
test_request_validation.py ─ RequestValidator              │
test_plugin_manager.py ── PluginManager                    │
test_plugin_registry.py ── PluginRegistry, Dependencies    │
test_plugin_permissions.py ─ PluginPermissionManager       │
test_plugin_versions.py ─── PluginVersionManager           │
test_plugin_marketplace.py ─ PluginMarketplace             │
test_plugin_sandbox.py ──── PluginSandbox                  │
test_modules.py ─────────── Module system                  │
test_scheduler.py ───────── Scheduler                      │
test_cron.py ────────────── CronEngine                     │
test_task_queue.py ──────── TaskQueue                      │
test_worker_pool.py ─────── WorkerPool                     │
test_priority_queue.py ──── PriorityQueue                  │
test_retry.py ───────────── JobRetry                       │
test_locks.py ───────────── DistributedLock                │
test_validation.py ──────── All validators                 │
test_kernel_integration.py ─ Full integration              │
```

## Quality Gates

```bash
# Lint
ruff check backend/tests/kernel/

# Type check
mypy backend/tests/kernel/ --strict

# Run
pytest backend/tests/kernel/ -v

# Coverage
pytest backend/tests/kernel/ --cov=backend.app.kernel --cov-report=term-missing
```
