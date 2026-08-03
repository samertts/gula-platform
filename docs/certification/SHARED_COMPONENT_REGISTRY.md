# Shared Component Registry — PROGRAM-STABLE-002

> Generated: 2026-08-02 · One authoritative implementation per cross-cutting concern.

| # | Component | Authoritative location | API surface (examples) | Consumers |
|---|---|---|---|---|
| 1 | RBAC | `shared/rbac/permissions.py` | `get_role_level`, `get_permissions_for_role`, `has_permission_str`, `can_manage_role`, `EXTENDED_ROLE_PERMISSIONS` | `app/security/rbac.py` (re-export), `require_permission` deps, frontend `permissions/index.ts` |
| 2 | Identity | `shared/identity`, `app/identity/` (NIAM) | sessions, MFA, OAuth2, SAML, service accounts | login, MFA routes, frontend AuthContext |
| 3 | Audit | `shared/audit`, `app/services/audit_service.py`, `app/audit/` | `log_action`, immutable anchor chain | all write routes |
| 4 | Encryption | `shared/security/encryption.py` | `encrypt_value`, `decrypt_value` | patient card, offline sync, NID |
| 5 | Cache | `shared/cache`, `app/security/redis_client.py` (`_LazyCache`) | `cache.get/set/delete` | stats, dashboard, rate limit |
| 6 | Event bus / outbox | `shared/events`, `app/services/outbox_service.py` | `enqueue`, `dispatch`, dead-letter | worker, national streaming |
| 7 | Barcode/QR | `shared/barcode`, `shared/qr` | `render_qr`, patient-card QR | public result, patient card |
| 8 | Health/metrics | `shared/health`, `shared/metrics` | `/health*`, Prometheus metrics | main.py, metrics routes |
| 9 | Notifications (legacy) | `app/notifications/service.py` | `/notify/send`, `/notify/history` | NotificationsPage |
| 10 | PDF reports | `shared/pdf` | `render_report_pdf` (Arabic font) | `/r/{token}/pdf`, reports |
| 11 | Rate limiting | `app/middleware.py`, `app/core/rate_limit*` | `rate_limit_user`, zones | all write routes |
| 12 | Scheduler | `shared/scheduler`, `app/core/startup.py` | cron jobs, lifespan | background tasks |
| 13 | DI wiring | `shared/di_container`, `app/factory.py` | `create_app` | whole app |
| 14 | Feature flags | `shared/feature_flags.py` | `get_tier_features`, `_VALID_*` | tiers, financial gate |
| 15 | Localization | `shared/localization`, `frontend-v3/src/i18n` | 399 ar/en keys | whole frontend |
| 16 | Declarative metadata (national/EHR) | `shared/models/base.py` → `SharedBase` | one metadata for national + EHR bound contexts | `app/national/base.py` (re-export `NationalBase`), `app/ehr/base.py` (`EHRBase`) |
| 17 | Rule engine domain | `shared/rules_engine/domain` | `RuleDefinition`, `Operator`, `RuleOutcome`, `RuleSeverity`, `RuleStatus`, `RuleCategory`, `RuleTrigger` | `app/kernel/rules_runtime.py`, `app/national/rules_engine` (re-exports) |

## Registry invariants

- Exactly one implementation per row is *active*; others are re-exports or adapters.
- No active duplicate of: identity, audit, RBAC, encryption, barcode, event bus, cache, health.
- Deliberate multi-layer exceptions (documented): notification delivery (legacy/NIAM/national),
  national enum RBAC (national-government scope).
