# GULA Technical Debt Registry

**Generated:** 2026-07-18 12:18 UTC  

**Total Items:** 647  

**Total Estimated Effort:** 1644.0 hours  


## Summary

| Priority | Count | Definition | SLA |
|----------|-------|------------|-----|
| **P0** | 4 | Blocking — deployment, data loss, security breach | 24 hours |
| **P1** | 13 | Critical — constitution, patient safety, regulatory | 7 days |
| **P2** | 448 | Major — best practices, tech debt accumulation | 30 days |
| **P3** | 182 | Minor — cosmetic, naming, documentation | 90 days |

### Status Breakdown

| Status | Count |
|--------|-------|
| ○ Open | 647 |

### Effort by Priority

| Priority | Est. Hours |
|----------|------------|
| **P0** | 68.0 |
| **P1** | 86.0 |
| **P2** | 1262.0 |
| **P3** | 228.0 |

### Category Breakdown

| Category | Count | Est. Hours |
|----------|-------|------------|
| Constitution Contradictions | 14 | 120.0 |
| Circular Dependencies | 7 | 56.0 |
| Layer Violations | 26 | 52.0 |
| Forbidden Imports | 52 | 53.0 |
| Cross-Domain Leakage | 365 | 1095.0 |
| Coverage Deficits | 1 | 40.0 |
| Documentation Gaps | 60 | 60.0 |
| Large Files/Functions | 67 | 134.0 |
| Naming Violations | 50 | 25.0 |
| Missing ADRs | 5 | 9.0 |

## Detailed Items

| ID | Priority | Category | Description | File | Lines | Est. Hrs | Status | Owner |
|----|----------|----------|-------------|------|-------|----------|--------|-------|
| TD-3883 | P0 | Constitution Contradictions | C1: Coverage Target Conflict (CRITICAL) | — | — | 16.0 | ○ open | unassigned |
| TD-3884 | P0 | Constitution Contradictions | C2: UUID PK Mandate vs Integer PKs (CRITICAL) | — | — | 40.0 | ○ open | unassigned |
| TD-3888 | P0 | Constitution Contradictions | C6: mTLS Mandate vs HTTP Comms (CRITICAL) | — | — | 8.0 | ○ open | unassigned |
| TD-3893 | P0 | Constitution Contradictions | C11: Circular Dep Check Missing from CI (MAJOR) | — | — | 4.0 | ○ open | unassigned |
| TD-3282 | P1 | Circular Dependencies | database → core.self_healing → database | backend/app/database.py | — | 8.0 | ○ open | Claude |
| TD-3283 | P1 | Circular Dependencies | kernel.config.registry → kernel.config.reload → kernel.config.registry | backend/app/kernel/config/registry.py | — | 8.0 | ○ open | Samertts |
| TD-3284 | P1 | Circular Dependencies | kernel.tenant.registry → kernel.tenant.resolver → kernel.tenant.registry | backend/app/kernel/tenant/registry.py | — | 8.0 | ○ open | Samertts |
| TD-3285 | P1 | Circular Dependencies | kernel.event_bus.bus → kernel.event_bus.replay → kernel.event_bus.bus | backend/app/kernel/event_bus/bus.py | — | 8.0 | ○ open | Samertts |
| TD-3286 | P1 | Circular Dependencies | kernel.plugin.hot_reload → kernel.plugin.manager → kernel.plugin.hot_reload | backend/app/kernel/plugin/hot_reload.py | — | 8.0 | ○ open | Samertts |
| TD-3287 | P1 | Circular Dependencies | national.background_platform.domain.entities → national.background_platform.appl | backend/app/national/background_platform/domain/en | — | 8.0 | ○ open | Samertts |
| TD-3288 | P1 | Circular Dependencies | main → routes.metrics → main | backend/app/main.py | — | 8.0 | ○ open | Samertts |
| TD-3885 | P1 | Constitution Contradictions | C3: Architecture Layer Naming (MAJOR) | — | — | 4.0 | ○ open | unassigned |
| TD-3887 | P1 | Constitution Contradictions | C5: FHIR Mandate Ambiguity (MAJOR) | — | — | 4.0 | ○ open | unassigned |
| TD-3889 | P1 | Constitution Contradictions | C7: SBOM Mandate vs No SBOM in CI (MAJOR) | — | — | 4.0 | ○ open | unassigned |
| TD-3892 | P1 | Constitution Contradictions | C10: No README per Module (MAJOR) | — | — | 8.0 | ○ open | unassigned |
| TD-3894 | P1 | Constitution Contradictions | C12: Failed Tests Contradiction (MAJOR) | — | — | 8.0 | ○ open | unassigned |
| TD-3289 | P1 | Forbidden Imports | domain.order_state:15 domain importing from fastapi framework (from fastapi impo | backend/app/domain/order_state.py | 15 | 2.0 | ○ open | Claude |
| TD-3886 | P2 | Constitution Contradictions | C4: Version Mismatch (MINOR) | — | — | 1.0 | ○ open | unassigned |
| TD-3890 | P2 | Constitution Contradictions | C8: Duplicate Files (MINOR) | — | — | 1.0 | ○ open | unassigned |
| TD-3891 | P2 | Constitution Contradictions | C9: DIGITAL-CONSTITUTION.md Status (MAJOR) | — | — | 2.0 | ○ open | unassigned |
| TD-3895 | P2 | Constitution Contradictions | C13: Retention Policy Enforcement Missing (MAJOR) | — | — | 16.0 | ○ open | unassigned |
| TD-3898 | P2 | Constitution Contradictions | G3: Constitution Enforcer Gaps | — | — | 4.0 | ○ open | unassigned |
| TD-3902 | P2 | Coverage Deficits | Test coverage at 55% — below 60% threshold. Need comprehensive test suite across | — | — | 40.0 | ○ open | unassigned |
| TD-3341 | P2 | Cross-Domain Leakage | ai_fabric.agents.base:11 bounded context leakage: 'ai_fabric' imports from 'ai'  | backend/app/ai_fabric/agents/base.py | 11 | 3.0 | ○ open | Samertts |
| TD-3342 | P2 | Cross-Domain Leakage | ai_fabric.agents.citizen_agent:6 bounded context leakage: 'ai_fabric' imports fr | backend/app/ai_fabric/agents/citizen_agent.py | 6 | 3.0 | ○ open | Samertts |
| TD-3343 | P2 | Cross-Domain Leakage | ai_fabric.agents.citizen_agent:6 bounded context leakage: 'ai_fabric' imports fr | backend/app/ai_fabric/agents/citizen_agent.py | 6 | 3.0 | ○ open | Samertts |
| TD-3344 | P2 | Cross-Domain Leakage | ai_fabric.agents.clinical_agent:6 bounded context leakage: 'ai_fabric' imports f | backend/app/ai_fabric/agents/clinical_agent.py | 6 | 3.0 | ○ open | Samertts |
| TD-3345 | P2 | Cross-Domain Leakage | ai_fabric.agents.clinical_agent:7 bounded context leakage: 'ai_fabric' imports f | backend/app/ai_fabric/agents/clinical_agent.py | 7 | 3.0 | ○ open | Samertts |
| TD-3346 | P2 | Cross-Domain Leakage | ai_fabric.agents.clinical_agent:8 bounded context leakage: 'ai_fabric' imports f | backend/app/ai_fabric/agents/clinical_agent.py | 8 | 3.0 | ○ open | Samertts |
| TD-3347 | P2 | Cross-Domain Leakage | ai_fabric.agents.clinical_agent:8 bounded context leakage: 'ai_fabric' imports f | backend/app/ai_fabric/agents/clinical_agent.py | 8 | 3.0 | ○ open | Samertts |
| TD-3348 | P2 | Cross-Domain Leakage | ai_fabric.agents.engineering_agent:6 bounded context leakage: 'ai_fabric' import | backend/app/ai_fabric/agents/engineering_agent.py | 6 | 3.0 | ○ open | Samertts |
| TD-3349 | P2 | Cross-Domain Leakage | ai_fabric.agents.engineering_agent:6 bounded context leakage: 'ai_fabric' import | backend/app/ai_fabric/agents/engineering_agent.py | 6 | 3.0 | ○ open | Samertts |
| TD-3350 | P2 | Cross-Domain Leakage | ai_fabric.agents.laboratory_agent:6 bounded context leakage: 'ai_fabric' imports | backend/app/ai_fabric/agents/laboratory_agent.py | 6 | 3.0 | ○ open | Samertts |
| TD-3351 | P2 | Cross-Domain Leakage | ai_fabric.agents.laboratory_agent:6 bounded context leakage: 'ai_fabric' imports | backend/app/ai_fabric/agents/laboratory_agent.py | 6 | 3.0 | ○ open | Samertts |
| TD-3352 | P2 | Cross-Domain Leakage | ai_fabric.agents.registry:6 bounded context leakage: 'ai_fabric' imports from 'a | backend/app/ai_fabric/agents/registry.py | 6 | 3.0 | ○ open | Samertts |
| TD-3353 | P2 | Cross-Domain Leakage | ai_fabric.agents.registry:7 bounded context leakage: 'ai_fabric' imports from 'a | backend/app/ai_fabric/agents/registry.py | 7 | 3.0 | ○ open | Samertts |
| TD-3354 | P2 | Cross-Domain Leakage | ai_fabric.agents.security_agent:6 bounded context leakage: 'ai_fabric' imports f | backend/app/ai_fabric/agents/security_agent.py | 6 | 3.0 | ○ open | Samertts |
| TD-3355 | P2 | Cross-Domain Leakage | ai_fabric.agents.security_agent:6 bounded context leakage: 'ai_fabric' imports f | backend/app/ai_fabric/agents/security_agent.py | 6 | 3.0 | ○ open | Samertts |
| TD-3356 | P2 | Cross-Domain Leakage | ai_fabric.clinical:9 bounded context leakage: 'ai_fabric' imports from 'ai' (app | backend/app/ai_fabric/clinical.py | 9 | 3.0 | ○ open | Samertts |
| TD-3357 | P2 | Cross-Domain Leakage | ai_fabric.clinical:10 bounded context leakage: 'ai_fabric' imports from 'ai' (ap | backend/app/ai_fabric/clinical.py | 10 | 3.0 | ○ open | Samertts |
| TD-3358 | P2 | Cross-Domain Leakage | ai_fabric.gateway:9 bounded context leakage: 'ai_fabric' imports from 'ai' (app. | backend/app/ai_fabric/gateway.py | 9 | 3.0 | ○ open | Samertts |
| TD-3359 | P2 | Cross-Domain Leakage | ai_fabric.gateway:9 bounded context leakage: 'ai_fabric' imports from 'ai' (app. | backend/app/ai_fabric/gateway.py | 9 | 3.0 | ○ open | Samertts |
| TD-3360 | P2 | Cross-Domain Leakage | ai_fabric.gateway:10 bounded context leakage: 'ai_fabric' imports from 'ai' (app | backend/app/ai_fabric/gateway.py | 10 | 3.0 | ○ open | Samertts |
| TD-3361 | P2 | Cross-Domain Leakage | ai_fabric.governance:10 bounded context leakage: 'ai_fabric' imports from 'ai' ( | backend/app/ai_fabric/governance.py | 10 | 3.0 | ○ open | Samertts |
| TD-3362 | P2 | Cross-Domain Leakage | ai_fabric.governance:11 bounded context leakage: 'ai_fabric' imports from 'ai' ( | backend/app/ai_fabric/governance.py | 11 | 3.0 | ○ open | Samertts |
| TD-3363 | P2 | Cross-Domain Leakage | ai_fabric.integration:8 bounded context leakage: 'ai_fabric' imports from 'ai' ( | backend/app/ai_fabric/integration.py | 8 | 3.0 | ○ open | Samertts |
| TD-3364 | P2 | Cross-Domain Leakage | ai_fabric.integration:9 bounded context leakage: 'ai_fabric' imports from 'ai' ( | backend/app/ai_fabric/integration.py | 9 | 3.0 | ○ open | Samertts |
| TD-3365 | P2 | Cross-Domain Leakage | ai_fabric.integration:10 bounded context leakage: 'ai_fabric' imports from 'ai'  | backend/app/ai_fabric/integration.py | 10 | 3.0 | ○ open | Samertts |
| TD-3366 | P2 | Cross-Domain Leakage | ai_fabric.integration:11 bounded context leakage: 'ai_fabric' imports from 'ai'  | backend/app/ai_fabric/integration.py | 11 | 3.0 | ○ open | Samertts |
| TD-3367 | P2 | Cross-Domain Leakage | ai_fabric.integration:12 bounded context leakage: 'ai_fabric' imports from 'ai'  | backend/app/ai_fabric/integration.py | 12 | 3.0 | ○ open | Samertts |
| TD-3368 | P2 | Cross-Domain Leakage | ai_fabric.integration:13 bounded context leakage: 'ai_fabric' imports from 'ai'  | backend/app/ai_fabric/integration.py | 13 | 3.0 | ○ open | Samertts |
| TD-3369 | P2 | Cross-Domain Leakage | ai_fabric.integration:14 bounded context leakage: 'ai_fabric' imports from 'ai'  | backend/app/ai_fabric/integration.py | 14 | 3.0 | ○ open | Samertts |
| TD-3370 | P2 | Cross-Domain Leakage | ai_fabric.integration:15 bounded context leakage: 'ai_fabric' imports from 'ai'  | backend/app/ai_fabric/integration.py | 15 | 3.0 | ○ open | Samertts |
| TD-3371 | P2 | Cross-Domain Leakage | ai_fabric.integration:15 bounded context leakage: 'ai_fabric' imports from 'ai'  | backend/app/ai_fabric/integration.py | 15 | 3.0 | ○ open | Samertts |
| TD-3372 | P2 | Cross-Domain Leakage | ai_fabric.integration:15 bounded context leakage: 'ai_fabric' imports from 'ai'  | backend/app/ai_fabric/integration.py | 15 | 3.0 | ○ open | Samertts |
| TD-3373 | P2 | Cross-Domain Leakage | ai_fabric.integration:16 bounded context leakage: 'ai_fabric' imports from 'ai'  | backend/app/ai_fabric/integration.py | 16 | 3.0 | ○ open | Samertts |
| TD-3374 | P2 | Cross-Domain Leakage | ai_fabric.integration:17 bounded context leakage: 'ai_fabric' imports from 'ai'  | backend/app/ai_fabric/integration.py | 17 | 3.0 | ○ open | Samertts |
| TD-3375 | P2 | Cross-Domain Leakage | ai_fabric.knowledge_graph:8 bounded context leakage: 'ai_fabric' imports from 'k | backend/app/ai_fabric/knowledge_graph.py | 8 | 3.0 | ○ open | Samertts |
| TD-3376 | P2 | Cross-Domain Leakage | ai_fabric.knowledge_graph:92 bounded context leakage: 'ai_fabric' imports from ' | backend/app/ai_fabric/knowledge_graph.py | 92 | 3.0 | ○ open | Samertts |
| TD-3377 | P2 | Cross-Domain Leakage | ai_fabric.knowledge_graph:110 bounded context leakage: 'ai_fabric' imports from  | backend/app/ai_fabric/knowledge_graph.py | 110 | 3.0 | ○ open | Samertts |
| TD-3378 | P2 | Cross-Domain Leakage | ai_fabric.knowledge_graph:130 bounded context leakage: 'ai_fabric' imports from  | backend/app/ai_fabric/knowledge_graph.py | 130 | 3.0 | ○ open | Samertts |
| TD-3379 | P2 | Cross-Domain Leakage | ai_fabric.knowledge_graph:165 bounded context leakage: 'ai_fabric' imports from  | backend/app/ai_fabric/knowledge_graph.py | 165 | 3.0 | ○ open | Samertts |
| TD-3380 | P2 | Cross-Domain Leakage | ai_fabric.local_ai:8 bounded context leakage: 'ai_fabric' imports from 'ai' (app | backend/app/ai_fabric/local_ai.py | 8 | 3.0 | ○ open | Samertts |
| TD-3381 | P2 | Cross-Domain Leakage | ai_fabric.local_ai:9 bounded context leakage: 'ai_fabric' imports from 'kernel'  | backend/app/ai_fabric/local_ai.py | 9 | 3.0 | ○ open | Samertts |
| TD-3382 | P2 | Cross-Domain Leakage | ai_fabric.local_ai:9 bounded context leakage: 'ai_fabric' imports from 'kernel'  | backend/app/ai_fabric/local_ai.py | 9 | 3.0 | ○ open | Samertts |
| TD-3383 | P2 | Cross-Domain Leakage | ai_fabric.local_ai:10 bounded context leakage: 'ai_fabric' imports from 'kernel' | backend/app/ai_fabric/local_ai.py | 10 | 3.0 | ○ open | Samertts |
| TD-3384 | P2 | Cross-Domain Leakage | ai_fabric.observability:9 bounded context leakage: 'ai_fabric' imports from 'ai' | backend/app/ai_fabric/observability.py | 9 | 3.0 | ○ open | Samertts |
| TD-3385 | P2 | Cross-Domain Leakage | ai_fabric.observability:9 bounded context leakage: 'ai_fabric' imports from 'ai' | backend/app/ai_fabric/observability.py | 9 | 3.0 | ○ open | Samertts |
| TD-3386 | P2 | Cross-Domain Leakage | ai_fabric.rag:12 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/rag.py | 12 | 3.0 | ○ open | Samertts |
| TD-3387 | P2 | Cross-Domain Leakage | ai_fabric.rag:13 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/rag.py | 13 | 3.0 | ○ open | Samertts |
| TD-3388 | P2 | Cross-Domain Leakage | ai_fabric.routes:8 bounded context leakage: 'ai_fabric' imports from 'ai' (app.a | backend/app/ai_fabric/routes.py | 8 | 3.0 | ○ open | Samertts |
| TD-3389 | P2 | Cross-Domain Leakage | ai_fabric.routes:9 bounded context leakage: 'ai_fabric' imports from 'ai' (app.a | backend/app/ai_fabric/routes.py | 9 | 3.0 | ○ open | Samertts |
| TD-3390 | P2 | Cross-Domain Leakage | ai_fabric.routes:9 bounded context leakage: 'ai_fabric' imports from 'ai' (app.a | backend/app/ai_fabric/routes.py | 9 | 3.0 | ○ open | Samertts |
| TD-3391 | P2 | Cross-Domain Leakage | ai_fabric.routes:9 bounded context leakage: 'ai_fabric' imports from 'ai' (app.a | backend/app/ai_fabric/routes.py | 9 | 3.0 | ○ open | Samertts |
| TD-3392 | P2 | Cross-Domain Leakage | ai_fabric.routes:10 bounded context leakage: 'ai_fabric' imports from 'ai' (app. | backend/app/ai_fabric/routes.py | 10 | 3.0 | ○ open | Samertts |
| TD-3393 | P2 | Cross-Domain Leakage | ai_fabric.routes:11 bounded context leakage: 'ai_fabric' imports from 'ai' (app. | backend/app/ai_fabric/routes.py | 11 | 3.0 | ○ open | Samertts |
| TD-3394 | P2 | Cross-Domain Leakage | ai_fabric.routes:14 bounded context leakage: 'ai_fabric' imports from 'ai' (app. | backend/app/ai_fabric/routes.py | 14 | 3.0 | ○ open | Samertts |
| TD-3395 | P2 | Cross-Domain Leakage | ai_fabric.routes:15 bounded context leakage: 'ai_fabric' imports from 'ai' (app. | backend/app/ai_fabric/routes.py | 15 | 3.0 | ○ open | Samertts |
| TD-3396 | P2 | Cross-Domain Leakage | ai_fabric.routes:63 bounded context leakage: 'ai_fabric' imports from 'ai' (app. | backend/app/ai_fabric/routes.py | 63 | 3.0 | ○ open | Samertts |
| TD-3397 | P2 | Cross-Domain Leakage | ai_fabric.sdk:6 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_f | backend/app/ai_fabric/sdk.py | 6 | 3.0 | ○ open | Samertts |
| TD-3398 | P2 | Cross-Domain Leakage | ai_fabric.sdk:7 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_f | backend/app/ai_fabric/sdk.py | 7 | 3.0 | ○ open | Samertts |
| TD-3399 | P2 | Cross-Domain Leakage | ai_fabric.sdk:8 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_f | backend/app/ai_fabric/sdk.py | 8 | 3.0 | ○ open | Samertts |
| TD-3400 | P2 | Cross-Domain Leakage | ai_fabric.sdk:8 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_f | backend/app/ai_fabric/sdk.py | 8 | 3.0 | ○ open | Samertts |
| TD-3401 | P2 | Cross-Domain Leakage | ai_fabric.sdk:8 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_f | backend/app/ai_fabric/sdk.py | 8 | 3.0 | ○ open | Samertts |
| TD-3402 | P2 | Cross-Domain Leakage | ai_fabric.sdk:13 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 13 | 3.0 | ○ open | Samertts |
| TD-3403 | P2 | Cross-Domain Leakage | ai_fabric.sdk:14 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 14 | 3.0 | ○ open | Samertts |
| TD-3404 | P2 | Cross-Domain Leakage | ai_fabric.sdk:17 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 17 | 3.0 | ○ open | Samertts |
| TD-3405 | P2 | Cross-Domain Leakage | ai_fabric.sdk:20 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 20 | 3.0 | ○ open | Samertts |
| TD-3406 | P2 | Cross-Domain Leakage | ai_fabric.sdk:20 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 20 | 3.0 | ○ open | Samertts |
| TD-3407 | P2 | Cross-Domain Leakage | ai_fabric.sdk:20 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 20 | 3.0 | ○ open | Samertts |
| TD-3408 | P2 | Cross-Domain Leakage | ai_fabric.sdk:20 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 20 | 3.0 | ○ open | Samertts |
| TD-3409 | P2 | Cross-Domain Leakage | ai_fabric.sdk:26 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 26 | 3.0 | ○ open | Samertts |
| TD-3410 | P2 | Cross-Domain Leakage | ai_fabric.sdk:26 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 26 | 3.0 | ○ open | Samertts |
| TD-3411 | P2 | Cross-Domain Leakage | ai_fabric.sdk:26 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 26 | 3.0 | ○ open | Samertts |
| TD-3412 | P2 | Cross-Domain Leakage | ai_fabric.sdk:26 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 26 | 3.0 | ○ open | Samertts |
| TD-3413 | P2 | Cross-Domain Leakage | ai_fabric.sdk:27 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 27 | 3.0 | ○ open | Samertts |
| TD-3414 | P2 | Cross-Domain Leakage | ai_fabric.sdk:28 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 28 | 3.0 | ○ open | Samertts |
| TD-3415 | P2 | Cross-Domain Leakage | ai_fabric.sdk:28 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 28 | 3.0 | ○ open | Samertts |
| TD-3416 | P2 | Cross-Domain Leakage | ai_fabric.sdk:28 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 28 | 3.0 | ○ open | Samertts |
| TD-3417 | P2 | Cross-Domain Leakage | ai_fabric.sdk:33 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 33 | 3.0 | ○ open | Samertts |
| TD-3418 | P2 | Cross-Domain Leakage | ai_fabric.sdk:33 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 33 | 3.0 | ○ open | Samertts |
| TD-3419 | P2 | Cross-Domain Leakage | ai_fabric.sdk:33 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 33 | 3.0 | ○ open | Samertts |
| TD-3420 | P2 | Cross-Domain Leakage | ai_fabric.sdk:34 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai_ | backend/app/ai_fabric/sdk.py | 34 | 3.0 | ○ open | Samertts |
| TD-3421 | P2 | Cross-Domain Leakage | ai_fabric.sdk:152 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai | backend/app/ai_fabric/sdk.py | 152 | 3.0 | ○ open | Samertts |
| TD-3422 | P2 | Cross-Domain Leakage | ai_fabric.sdk:209 bounded context leakage: 'ai_fabric' imports from 'ai' (app.ai | backend/app/ai_fabric/sdk.py | 209 | 3.0 | ○ open | Samertts |
| TD-3423 | P2 | Cross-Domain Leakage | biomedical.api.routes:20 bounded context leakage: 'biomedical' imports from 'ker | backend/app/biomedical/api/routes.py | 20 | 3.0 | ○ open | Samertts |
| TD-3424 | P2 | Cross-Domain Leakage | biomedical.application.service:39 bounded context leakage: 'biomedical' imports  | backend/app/biomedical/application/service.py | 39 | 3.0 | ○ open | Samertts |
| TD-3425 | P2 | Cross-Domain Leakage | biomedical.domain.events:5 bounded context leakage: 'biomedical' imports from 'n | backend/app/biomedical/domain/events.py | 5 | 3.0 | ○ open | Samertts |
| TD-3426 | P2 | Cross-Domain Leakage | biomedical.infrastructure.models:5 bounded context leakage: 'biomedical' imports | backend/app/biomedical/infrastructure/models.py | 5 | 3.0 | ○ open | Samertts |
| TD-3427 | P2 | Cross-Domain Leakage | biomedical.infrastructure.models:5 bounded context leakage: 'biomedical' imports | backend/app/biomedical/infrastructure/models.py | 5 | 3.0 | ○ open | Samertts |
| TD-3428 | P2 | Cross-Domain Leakage | blood_bank.api.routes:24 bounded context leakage: 'blood_bank' imports from 'ker | backend/app/blood_bank/api/routes.py | 24 | 3.0 | ○ open | Samertts |
| TD-3429 | P2 | Cross-Domain Leakage | blood_bank.application.service:46 bounded context leakage: 'blood_bank' imports  | backend/app/blood_bank/application/service.py | 46 | 3.0 | ○ open | Samertts |
| TD-3430 | P2 | Cross-Domain Leakage | blood_bank.domain.events:5 bounded context leakage: 'blood_bank' imports from 'n | backend/app/blood_bank/domain/events.py | 5 | 3.0 | ○ open | Samertts |
| TD-3431 | P2 | Cross-Domain Leakage | blood_bank.infrastructure.models:15 bounded context leakage: 'blood_bank' import | backend/app/blood_bank/infrastructure/models.py | 15 | 3.0 | ○ open | Samertts |
| TD-3432 | P2 | Cross-Domain Leakage | blood_bank.infrastructure.models:15 bounded context leakage: 'blood_bank' import | backend/app/blood_bank/infrastructure/models.py | 15 | 3.0 | ○ open | Samertts |
| TD-3433 | P2 | Cross-Domain Leakage | care_continuum.models.primary_care:18 bounded context leakage: 'care_continuum'  | backend/app/care_continuum/models/primary_care.py | 18 | 3.0 | ○ open | Samertts |
| TD-3434 | P2 | Cross-Domain Leakage | care_continuum.models.referral:6 bounded context leakage: 'care_continuum' impor | backend/app/care_continuum/models/referral.py | 6 | 3.0 | ○ open | Samertts |
| TD-3435 | P2 | Cross-Domain Leakage | care_continuum.models.referral:6 bounded context leakage: 'care_continuum' impor | backend/app/care_continuum/models/referral.py | 6 | 3.0 | ○ open | Samertts |
| TD-3436 | P2 | Cross-Domain Leakage | certification.dimensions.architecture:5 bounded context leakage: 'certification' | backend/app/certification/dimensions/architecture. | 5 | 3.0 | ○ open | Samertts |
| TD-3437 | P2 | Cross-Domain Leakage | certification.dimensions.architecture:6 bounded context leakage: 'certification' | backend/app/certification/dimensions/architecture. | 6 | 3.0 | ○ open | Samertts |
| TD-3438 | P2 | Cross-Domain Leakage | certification.dimensions.architecture:7 bounded context leakage: 'certification' | backend/app/certification/dimensions/architecture. | 7 | 3.0 | ○ open | Samertts |
| TD-3439 | P2 | Cross-Domain Leakage | certification.dimensions.maintainability:8 bounded context leakage: 'certificati | backend/app/certification/dimensions/maintainabili | 8 | 3.0 | ○ open | Samertts |
| TD-3440 | P2 | Cross-Domain Leakage | certification.dimensions.performance:5 bounded context leakage: 'certification'  | backend/app/certification/dimensions/performance.p | 5 | 3.0 | ○ open | Samertts |
| TD-3441 | P2 | Cross-Domain Leakage | certification.dimensions.security:5 bounded context leakage: 'certification' imp | backend/app/certification/dimensions/security.py | 5 | 3.0 | ○ open | Samertts |
| TD-3442 | P2 | Cross-Domain Leakage | certification.dimensions.security:5 bounded context leakage: 'certification' imp | backend/app/certification/dimensions/security.py | 5 | 3.0 | ○ open | Samertts |
| TD-3443 | P2 | Cross-Domain Leakage | certification.release_gates:179 bounded context leakage: 'certification' imports | backend/app/certification/release_gates.py | 179 | 3.0 | ○ open | Samertts |
| TD-3444 | P2 | Cross-Domain Leakage | certification.release_gates:189 bounded context leakage: 'certification' imports | backend/app/certification/release_gates.py | 189 | 3.0 | ○ open | Samertts |
| TD-3445 | P2 | Cross-Domain Leakage | citizen_platform.accessibility:8 bounded context leakage: 'citizen_platform' imp | backend/app/citizen_platform/accessibility.py | 8 | 3.0 | ○ open | Samertts |
| TD-3446 | P2 | Cross-Domain Leakage | citizen_platform.appointments:9 bounded context leakage: 'citizen_platform' impo | backend/app/citizen_platform/appointments.py | 9 | 3.0 | ○ open | Samertts |
| TD-3447 | P2 | Cross-Domain Leakage | citizen_platform.appointments:9 bounded context leakage: 'citizen_platform' impo | backend/app/citizen_platform/appointments.py | 9 | 3.0 | ○ open | Samertts |
| TD-3448 | P2 | Cross-Domain Leakage | citizen_platform.appointments:9 bounded context leakage: 'citizen_platform' impo | backend/app/citizen_platform/appointments.py | 9 | 3.0 | ○ open | Samertts |
| TD-3449 | P2 | Cross-Domain Leakage | citizen_platform.appointments:14 bounded context leakage: 'citizen_platform' imp | backend/app/citizen_platform/appointments.py | 14 | 3.0 | ○ open | Samertts |
| TD-3450 | P2 | Cross-Domain Leakage | citizen_platform.identity:10 bounded context leakage: 'citizen_platform' imports | backend/app/citizen_platform/identity.py | 10 | 3.0 | ○ open | Samertts |
| TD-3451 | P2 | Cross-Domain Leakage | citizen_platform.integration:48 bounded context leakage: 'citizen_platform' impo | backend/app/citizen_platform/integration.py | 48 | 3.0 | ○ open | Samertts |
| TD-3452 | P2 | Cross-Domain Leakage | citizen_platform.integration:49 bounded context leakage: 'citizen_platform' impo | backend/app/citizen_platform/integration.py | 49 | 3.0 | ○ open | Samertts |
| TD-3453 | P2 | Cross-Domain Leakage | citizen_platform.integration:50 bounded context leakage: 'citizen_platform' impo | backend/app/citizen_platform/integration.py | 50 | 3.0 | ○ open | Samertts |
| TD-3454 | P2 | Cross-Domain Leakage | citizen_platform.integration:51 bounded context leakage: 'citizen_platform' impo | backend/app/citizen_platform/integration.py | 51 | 3.0 | ○ open | Samertts |
| TD-3455 | P2 | Cross-Domain Leakage | citizen_platform.integration:52 bounded context leakage: 'citizen_platform' impo | backend/app/citizen_platform/integration.py | 52 | 3.0 | ○ open | Samertts |
| TD-3456 | P2 | Cross-Domain Leakage | citizen_platform.integration:53 bounded context leakage: 'citizen_platform' impo | backend/app/citizen_platform/integration.py | 53 | 3.0 | ○ open | Samertts |
| TD-3457 | P2 | Cross-Domain Leakage | citizen_platform.medications:9 bounded context leakage: 'citizen_platform' impor | backend/app/citizen_platform/medications.py | 9 | 3.0 | ○ open | Samertts |
| TD-3458 | P2 | Cross-Domain Leakage | citizen_platform.notifications:10 bounded context leakage: 'citizen_platform' im | backend/app/citizen_platform/notifications.py | 10 | 3.0 | ○ open | Samertts |
| TD-3459 | P2 | Cross-Domain Leakage | citizen_platform.notifications:11 bounded context leakage: 'citizen_platform' im | backend/app/citizen_platform/notifications.py | 11 | 3.0 | ○ open | Samertts |
| TD-3460 | P2 | Cross-Domain Leakage | citizen_platform.offline:9 bounded context leakage: 'citizen_platform' imports f | backend/app/citizen_platform/offline.py | 9 | 3.0 | ○ open | Samertts |
| TD-3461 | P2 | Cross-Domain Leakage | citizen_platform.offline:10 bounded context leakage: 'citizen_platform' imports  | backend/app/citizen_platform/offline.py | 10 | 3.0 | ○ open | Samertts |
| TD-3462 | P2 | Cross-Domain Leakage | citizen_platform.phr:10 bounded context leakage: 'citizen_platform' imports from | backend/app/citizen_platform/phr.py | 10 | 3.0 | ○ open | Samertts |
| TD-3463 | P2 | Cross-Domain Leakage | citizen_platform.portal:7 bounded context leakage: 'citizen_platform' imports fr | backend/app/citizen_platform/portal.py | 7 | 3.0 | ○ open | Samertts |
| TD-3464 | P2 | Cross-Domain Leakage | command_center.api.routes:26 bounded context leakage: 'command_center' imports f | backend/app/command_center/api/routes.py | 26 | 3.0 | ○ open | Samertts |
| TD-3465 | P2 | Cross-Domain Leakage | command_center.application.service:26 bounded context leakage: 'command_center'  | backend/app/command_center/application/service.py | 26 | 3.0 | ○ open | Samertts |
| TD-3466 | P2 | Cross-Domain Leakage | command_center.application.service:158 bounded context leakage: 'command_center' | backend/app/command_center/application/service.py | 158 | 3.0 | ○ open | Samertts |
| TD-3467 | P2 | Cross-Domain Leakage | command_center.application.service:169 bounded context leakage: 'command_center' | backend/app/command_center/application/service.py | 169 | 3.0 | ○ open | Samertts |
| TD-3468 | P2 | Cross-Domain Leakage | command_center.application.service:179 bounded context leakage: 'command_center' | backend/app/command_center/application/service.py | 179 | 3.0 | ○ open | Samertts |
| TD-3469 | P2 | Cross-Domain Leakage | command_center.application.service:191 bounded context leakage: 'command_center' | backend/app/command_center/application/service.py | 191 | 3.0 | ○ open | Samertts |
| TD-3470 | P2 | Cross-Domain Leakage | command_center.application.service:199 bounded context leakage: 'command_center' | backend/app/command_center/application/service.py | 199 | 3.0 | ○ open | Samertts |
| TD-3471 | P2 | Cross-Domain Leakage | command_center.domain.events:3 bounded context leakage: 'command_center' imports | backend/app/command_center/domain/events.py | 3 | 3.0 | ○ open | Samertts |
| TD-3472 | P2 | Cross-Domain Leakage | command_center.infrastructure.models:3 bounded context leakage: 'command_center' | backend/app/command_center/infrastructure/models.p | 3 | 3.0 | ○ open | Samertts |
| TD-3473 | P2 | Cross-Domain Leakage | control_plane.analytics:9 bounded context leakage: 'control_plane' imports from  | backend/app/control_plane/analytics.py | 9 | 3.0 | ○ open | Samertts |
| TD-3474 | P2 | Cross-Domain Leakage | control_plane.config.features:6 bounded context leakage: 'control_plane' imports | backend/app/control_plane/config/features.py | 6 | 3.0 | ○ open | Samertts |
| TD-3475 | P2 | Cross-Domain Leakage | control_plane.config.features:6 bounded context leakage: 'control_plane' imports | backend/app/control_plane/config/features.py | 6 | 3.0 | ○ open | Samertts |
| TD-3476 | P2 | Cross-Domain Leakage | control_plane.config.features:7 bounded context leakage: 'control_plane' imports | backend/app/control_plane/config/features.py | 7 | 3.0 | ○ open | Samertts |
| TD-3477 | P2 | Cross-Domain Leakage | control_plane.config.features:8 bounded context leakage: 'control_plane' imports | backend/app/control_plane/config/features.py | 8 | 3.0 | ○ open | Samertts |
| TD-3478 | P2 | Cross-Domain Leakage | control_plane.config.features:9 bounded context leakage: 'control_plane' imports | backend/app/control_plane/config/features.py | 9 | 3.0 | ○ open | Samertts |
| TD-3479 | P2 | Cross-Domain Leakage | control_plane.config.features:10 bounded context leakage: 'control_plane' import | backend/app/control_plane/config/features.py | 10 | 3.0 | ○ open | Samertts |
| TD-3480 | P2 | Cross-Domain Leakage | control_plane.config.manager:9 bounded context leakage: 'control_plane' imports  | backend/app/control_plane/config/manager.py | 9 | 3.0 | ○ open | Samertts |
| TD-3481 | P2 | Cross-Domain Leakage | control_plane.config.manager:10 bounded context leakage: 'control_plane' imports | backend/app/control_plane/config/manager.py | 10 | 3.0 | ○ open | Samertts |
| TD-3482 | P2 | Cross-Domain Leakage | control_plane.config.manager:26 bounded context leakage: 'control_plane' imports | backend/app/control_plane/config/manager.py | 26 | 3.0 | ○ open | Samertts |
| TD-3483 | P2 | Cross-Domain Leakage | control_plane.config.secrets:8 bounded context leakage: 'control_plane' imports  | backend/app/control_plane/config/secrets.py | 8 | 3.0 | ○ open | Samertts |
| TD-3484 | P2 | Cross-Domain Leakage | control_plane.config.secrets:9 bounded context leakage: 'control_plane' imports  | backend/app/control_plane/config/secrets.py | 9 | 3.0 | ○ open | Samertts |
| TD-3485 | P2 | Cross-Domain Leakage | control_plane.integration:9 bounded context leakage: 'control_plane' imports fro | backend/app/control_plane/integration.py | 9 | 3.0 | ○ open | Samertts |
| TD-3486 | P2 | Cross-Domain Leakage | control_plane.multi_tenant:10 bounded context leakage: 'control_plane' imports f | backend/app/control_plane/multi_tenant.py | 10 | 3.0 | ○ open | Samertts |
| TD-3487 | P2 | Cross-Domain Leakage | control_plane.multi_tenant:11 bounded context leakage: 'control_plane' imports f | backend/app/control_plane/multi_tenant.py | 11 | 3.0 | ○ open | Samertts |
| TD-3488 | P2 | Cross-Domain Leakage | control_plane.multi_tenant:12 bounded context leakage: 'control_plane' imports f | backend/app/control_plane/multi_tenant.py | 12 | 3.0 | ○ open | Samertts |
| TD-3489 | P2 | Cross-Domain Leakage | control_plane.registry.component:10 bounded context leakage: 'control_plane' imp | backend/app/control_plane/registry/component.py | 10 | 3.0 | ○ open | Samertts |
| TD-3490 | P2 | Cross-Domain Leakage | control_plane.service_manager:9 bounded context leakage: 'control_plane' imports | backend/app/control_plane/service_manager.py | 9 | 3.0 | ○ open | Samertts |
| TD-3491 | P2 | Cross-Domain Leakage | control_plane.service_manager:9 bounded context leakage: 'control_plane' imports | backend/app/control_plane/service_manager.py | 9 | 3.0 | ○ open | Samertts |
| TD-3492 | P2 | Cross-Domain Leakage | control_plane.service_manager:10 bounded context leakage: 'control_plane' import | backend/app/control_plane/service_manager.py | 10 | 3.0 | ○ open | Samertts |
| TD-3493 | P2 | Cross-Domain Leakage | critical_care.api.routes:22 bounded context leakage: 'critical_care' imports fro | backend/app/critical_care/api/routes.py | 22 | 3.0 | ○ open | Samertts |
| TD-3494 | P2 | Cross-Domain Leakage | critical_care.application.service:45 bounded context leakage: 'critical_care' im | backend/app/critical_care/application/service.py | 45 | 3.0 | ○ open | Samertts |
| TD-3495 | P2 | Cross-Domain Leakage | critical_care.domain.events:5 bounded context leakage: 'critical_care' imports f | backend/app/critical_care/domain/events.py | 5 | 3.0 | ○ open | Samertts |
| TD-3496 | P2 | Cross-Domain Leakage | critical_care.infrastructure.models:5 bounded context leakage: 'critical_care' i | backend/app/critical_care/infrastructure/models.py | 5 | 3.0 | ○ open | Samertts |
| TD-3497 | P2 | Cross-Domain Leakage | critical_care.infrastructure.models:5 bounded context leakage: 'critical_care' i | backend/app/critical_care/infrastructure/models.py | 5 | 3.0 | ○ open | Samertts |
| TD-3498 | P2 | Cross-Domain Leakage | ems.api.routes:23 bounded context leakage: 'ems' imports from 'kernel' (app.kern | backend/app/ems/api/routes.py | 23 | 3.0 | ○ open | Samertts |
| TD-3499 | P2 | Cross-Domain Leakage | ems.application.service:48 bounded context leakage: 'ems' imports from 'national | backend/app/ems/application/service.py | 48 | 3.0 | ○ open | Samertts |
| TD-3500 | P2 | Cross-Domain Leakage | ems.domain.events:5 bounded context leakage: 'ems' imports from 'national' (app. | backend/app/ems/domain/events.py | 5 | 3.0 | ○ open | Samertts |
| TD-3501 | P2 | Cross-Domain Leakage | ems.infrastructure.models:15 bounded context leakage: 'ems' imports from 'nation | backend/app/ems/infrastructure/models.py | 15 | 3.0 | ○ open | Samertts |
| TD-3502 | P2 | Cross-Domain Leakage | ems.infrastructure.models:15 bounded context leakage: 'ems' imports from 'nation | backend/app/ems/infrastructure/models.py | 15 | 3.0 | ○ open | Samertts |
| TD-3503 | P2 | Cross-Domain Leakage | governance.routes.governance_routes:24 bounded context leakage: 'governance' imp | backend/app/governance/routes/governance_routes.py | 24 | 3.0 | ○ open | Samertts |
| TD-3504 | P2 | Cross-Domain Leakage | governance.routes.governance_routes:24 bounded context leakage: 'governance' imp | backend/app/governance/routes/governance_routes.py | 24 | 3.0 | ○ open | Samertts |
| TD-3505 | P2 | Cross-Domain Leakage | health_data.data_lake.storage:85 bounded context leakage: 'health_data' imports  | backend/app/health_data/data_lake/storage.py | 85 | 3.0 | ○ open | Samertts |
| TD-3506 | P2 | Cross-Domain Leakage | health_data.event_store.store:10 bounded context leakage: 'health_data' imports  | backend/app/health_data/event_store/store.py | 10 | 3.0 | ○ open | Samertts |
| TD-3507 | P2 | Cross-Domain Leakage | health_data.event_store.store:11 bounded context leakage: 'health_data' imports  | backend/app/health_data/event_store/store.py | 11 | 3.0 | ○ open | Samertts |
| TD-3508 | P2 | Cross-Domain Leakage | health_data.streaming.pipeline:10 bounded context leakage: 'health_data' imports | backend/app/health_data/streaming/pipeline.py | 10 | 3.0 | ○ open | Samertts |
| TD-3509 | P2 | Cross-Domain Leakage | health_data.streaming.pipeline:11 bounded context leakage: 'health_data' imports | backend/app/health_data/streaming/pipeline.py | 11 | 3.0 | ○ open | Samertts |
| TD-3510 | P2 | Cross-Domain Leakage | interoperability.adapter_base:21 bounded context leakage: 'interoperability' imp | backend/app/interoperability/adapter_base.py | 21 | 3.0 | ○ open | Claude |
| TD-3511 | P2 | Cross-Domain Leakage | interoperability.manifest:14 bounded context leakage: 'interoperability' imports | backend/app/interoperability/manifest.py | 14 | 3.0 | ○ open | Claude |
| TD-3512 | P2 | Cross-Domain Leakage | interoperability.manifest:14 bounded context leakage: 'interoperability' imports | backend/app/interoperability/manifest.py | 14 | 3.0 | ○ open | Claude |
| TD-3513 | P2 | Cross-Domain Leakage | interoperability.manifest:14 bounded context leakage: 'interoperability' imports | backend/app/interoperability/manifest.py | 14 | 3.0 | ○ open | Claude |
| TD-3514 | P2 | Cross-Domain Leakage | kernel.ai_runtime:10 bounded context leakage: 'kernel' imports from 'ai' (app.ai | backend/app/kernel/ai_runtime.py | 10 | 3.0 | ○ open | Samertts |
| TD-3515 | P2 | Cross-Domain Leakage | kernel.ai_runtime:10 bounded context leakage: 'kernel' imports from 'ai' (app.ai | backend/app/kernel/ai_runtime.py | 10 | 3.0 | ○ open | Samertts |
| TD-3516 | P2 | Cross-Domain Leakage | kernel.ai_runtime:11 bounded context leakage: 'kernel' imports from 'ai' (app.ai | backend/app/kernel/ai_runtime.py | 11 | 3.0 | ○ open | Samertts |
| TD-3517 | P2 | Cross-Domain Leakage | kernel.ai_runtime:12 bounded context leakage: 'kernel' imports from 'ai' (app.ai | backend/app/kernel/ai_runtime.py | 12 | 3.0 | ○ open | Samertts |
| TD-3518 | P2 | Cross-Domain Leakage | kernel.ai_runtime:12 bounded context leakage: 'kernel' imports from 'ai' (app.ai | backend/app/kernel/ai_runtime.py | 12 | 3.0 | ○ open | Samertts |
| TD-3519 | P2 | Cross-Domain Leakage | kernel.ai_runtime:13 bounded context leakage: 'kernel' imports from 'ai' (app.ai | backend/app/kernel/ai_runtime.py | 13 | 3.0 | ○ open | Samertts |
| TD-3520 | P2 | Cross-Domain Leakage | kernel.ai_runtime:13 bounded context leakage: 'kernel' imports from 'ai' (app.ai | backend/app/kernel/ai_runtime.py | 13 | 3.0 | ○ open | Samertts |
| TD-3521 | P2 | Cross-Domain Leakage | kernel.generate_capabilities:5 bounded context leakage: 'kernel' imports from 'e | backend/app/kernel/generate_capabilities.py | 5 | 3.0 | ○ open | Samertts |
| TD-3522 | P2 | Cross-Domain Leakage | kernel.generate_capabilities:5 bounded context leakage: 'kernel' imports from 'e | backend/app/kernel/generate_capabilities.py | 5 | 3.0 | ○ open | Samertts |
| TD-3523 | P2 | Cross-Domain Leakage | kernel.generate_capabilities:5 bounded context leakage: 'kernel' imports from 'e | backend/app/kernel/generate_capabilities.py | 5 | 3.0 | ○ open | Samertts |
| TD-3524 | P2 | Cross-Domain Leakage | kernel.rules_runtime:10 bounded context leakage: 'kernel' imports from 'national | backend/app/kernel/rules_runtime.py | 10 | 3.0 | ○ open | Samertts |
| TD-3525 | P2 | Cross-Domain Leakage | kernel.rules_runtime:13 bounded context leakage: 'kernel' imports from 'national | backend/app/kernel/rules_runtime.py | 13 | 3.0 | ○ open | Samertts |
| TD-3526 | P2 | Cross-Domain Leakage | kernel.rules_runtime:13 bounded context leakage: 'kernel' imports from 'national | backend/app/kernel/rules_runtime.py | 13 | 3.0 | ○ open | Samertts |
| TD-3527 | P2 | Cross-Domain Leakage | kernel.rules_runtime:13 bounded context leakage: 'kernel' imports from 'national | backend/app/kernel/rules_runtime.py | 13 | 3.0 | ○ open | Samertts |
| TD-3528 | P2 | Cross-Domain Leakage | kernel.rules_runtime:13 bounded context leakage: 'kernel' imports from 'national | backend/app/kernel/rules_runtime.py | 13 | 3.0 | ○ open | Samertts |
| TD-3529 | P2 | Cross-Domain Leakage | knowledge_graph.event_catalog:57 bounded context leakage: 'knowledge_graph' impo | backend/app/knowledge_graph/event_catalog.py | 57 | 3.0 | ○ open | Samertts |
| TD-3530 | P2 | Cross-Domain Leakage | knowledge_graph.event_catalog:178 bounded context leakage: 'knowledge_graph' imp | backend/app/knowledge_graph/event_catalog.py | 178 | 3.0 | ○ open | Samertts |
| TD-3531 | P2 | Cross-Domain Leakage | knowledge_graph.service_catalog:137 bounded context leakage: 'knowledge_graph' i | backend/app/knowledge_graph/service_catalog.py | 137 | 3.0 | ○ open | Samertts |
| TD-3532 | P2 | Cross-Domain Leakage | lifecycle_platform.api.routes:29 bounded context leakage: 'lifecycle_platform' i | backend/app/lifecycle_platform/api/routes.py | 29 | 3.0 | ○ open | Samertts |
| TD-3533 | P2 | Cross-Domain Leakage | lifecycle_platform.domain.events:3 bounded context leakage: 'lifecycle_platform' | backend/app/lifecycle_platform/domain/events.py | 3 | 3.0 | ○ open | Samertts |
| TD-3534 | P2 | Cross-Domain Leakage | lifecycle_platform.infrastructure.models:3 bounded context leakage: 'lifecycle_p | backend/app/lifecycle_platform/infrastructure/mode | 3 | 3.0 | ○ open | Samertts |
| TD-3535 | P2 | Cross-Domain Leakage | lims.routes:1533 bounded context leakage: 'lims' imports from 'workflows' (workf | backend/app/lims/routes.py | 1533 | 3.0 | ○ open | Samertts |
| TD-3536 | P2 | Cross-Domain Leakage | lims.routes:1556 bounded context leakage: 'lims' imports from 'workflows' (workf | backend/app/lims/routes.py | 1556 | 3.0 | ○ open | Samertts |
| TD-3537 | P2 | Cross-Domain Leakage | lims.services:41 bounded context leakage: 'lims' imports from 'workflows' (workf | backend/app/lims/services.py | 41 | 3.0 | ○ open | Samertts |
| TD-3538 | P2 | Cross-Domain Leakage | national.background_platform.api.routes:37 bounded context leakage: 'national' i | backend/app/national/background_platform/api/route | 37 | 3.0 | ○ open | Samertts |
| TD-3539 | P2 | Cross-Domain Leakage | national.background_platform.api.routes:38 bounded context leakage: 'national' i | backend/app/national/background_platform/api/route | 38 | 3.0 | ○ open | Samertts |
| TD-3540 | P2 | Cross-Domain Leakage | national.background_platform.application.service:9 bounded context leakage: 'nat | backend/app/national/background_platform/applicati | 9 | 3.0 | ○ open | Samertts |
| TD-3541 | P2 | Cross-Domain Leakage | national.background_platform.application.service:10 bounded context leakage: 'na | backend/app/national/background_platform/applicati | 10 | 3.0 | ○ open | Samertts |
| TD-3542 | P2 | Cross-Domain Leakage | national.document_platform.api.routes:38 bounded context leakage: 'national' imp | backend/app/national/document_platform/api/routes. | 38 | 3.0 | ○ open | Samertts |
| TD-3543 | P2 | Cross-Domain Leakage | national.document_platform.api.routes:39 bounded context leakage: 'national' imp | backend/app/national/document_platform/api/routes. | 39 | 3.0 | ○ open | Samertts |
| TD-3544 | P2 | Cross-Domain Leakage | national.document_platform.application.service:10 bounded context leakage: 'nati | backend/app/national/document_platform/application | 10 | 3.0 | ○ open | Samertts |
| TD-3545 | P2 | Cross-Domain Leakage | national.document_platform.application.service:11 bounded context leakage: 'nati | backend/app/national/document_platform/application | 11 | 3.0 | ○ open | Samertts |
| TD-3546 | P2 | Cross-Domain Leakage | national.ecosystem.connectors.messaging_connector:186 bounded context leakage: ' | backend/app/national/ecosystem/connectors/messagin | 186 | 3.0 | ○ open | Samertts |
| TD-3547 | P2 | Cross-Domain Leakage | national.ecosystem.connectors.messaging_connector:225 bounded context leakage: ' | backend/app/national/ecosystem/connectors/messagin | 225 | 3.0 | ○ open | Samertts |
| TD-3548 | P2 | Cross-Domain Leakage | national.ecosystem.gateway.routes:7 bounded context leakage: 'national' imports  | backend/app/national/ecosystem/gateway/routes.py | 7 | 3.0 | ○ open | Samertts |
| TD-3549 | P2 | Cross-Domain Leakage | national.ecosystem.gateway.routes:7 bounded context leakage: 'national' imports  | backend/app/national/ecosystem/gateway/routes.py | 7 | 3.0 | ○ open | Samertts |
| TD-3550 | P2 | Cross-Domain Leakage | national.ecosystem.gateway.routes:40 bounded context leakage: 'national' imports | backend/app/national/ecosystem/gateway/routes.py | 40 | 3.0 | ○ open | Samertts |
| TD-3551 | P2 | Cross-Domain Leakage | national.ecosystem.gateway.routes:40 bounded context leakage: 'national' imports | backend/app/national/ecosystem/gateway/routes.py | 40 | 3.0 | ○ open | Samertts |
| TD-3552 | P2 | Cross-Domain Leakage | national.ecosystem.gateway.routes:40 bounded context leakage: 'national' imports | backend/app/national/ecosystem/gateway/routes.py | 40 | 3.0 | ○ open | Samertts |
| TD-3553 | P2 | Cross-Domain Leakage | national.ecosystem.gateway.routes:40 bounded context leakage: 'national' imports | backend/app/national/ecosystem/gateway/routes.py | 40 | 3.0 | ○ open | Samertts |
| TD-3554 | P2 | Cross-Domain Leakage | national.ecosystem.gateway.routes:40 bounded context leakage: 'national' imports | backend/app/national/ecosystem/gateway/routes.py | 40 | 3.0 | ○ open | Samertts |
| TD-3555 | P2 | Cross-Domain Leakage | national.ecosystem.gateway.routes:40 bounded context leakage: 'national' imports | backend/app/national/ecosystem/gateway/routes.py | 40 | 3.0 | ○ open | Samertts |
| TD-3556 | P2 | Cross-Domain Leakage | national.ecosystem.gateway.routes:40 bounded context leakage: 'national' imports | backend/app/national/ecosystem/gateway/routes.py | 40 | 3.0 | ○ open | Samertts |
| TD-3557 | P2 | Cross-Domain Leakage | national.ecosystem.gateway.routes:40 bounded context leakage: 'national' imports | backend/app/national/ecosystem/gateway/routes.py | 40 | 3.0 | ○ open | Samertts |
| TD-3558 | P2 | Cross-Domain Leakage | national.fhir.allergy_intolerance:5 bounded context leakage: 'national' imports  | backend/app/national/fhir/allergy_intolerance.py | 5 | 3.0 | ○ open | Samertts |
| TD-3559 | P2 | Cross-Domain Leakage | national.fhir.care_plan:5 bounded context leakage: 'national' imports from 'ehr' | backend/app/national/fhir/care_plan.py | 5 | 3.0 | ○ open | Samertts |
| TD-3560 | P2 | Cross-Domain Leakage | national.fhir.care_plan:5 bounded context leakage: 'national' imports from 'ehr' | backend/app/national/fhir/care_plan.py | 5 | 3.0 | ○ open | Samertts |
| TD-3561 | P2 | Cross-Domain Leakage | national.fhir.care_plan:5 bounded context leakage: 'national' imports from 'ehr' | backend/app/national/fhir/care_plan.py | 5 | 3.0 | ○ open | Samertts |
| TD-3562 | P2 | Cross-Domain Leakage | national.fhir.condition:5 bounded context leakage: 'national' imports from 'ehr' | backend/app/national/fhir/condition.py | 5 | 3.0 | ○ open | Samertts |
| TD-3563 | P2 | Cross-Domain Leakage | national.fhir.condition:5 bounded context leakage: 'national' imports from 'ehr' | backend/app/national/fhir/condition.py | 5 | 3.0 | ○ open | Samertts |
| TD-3564 | P2 | Cross-Domain Leakage | national.fhir.condition:5 bounded context leakage: 'national' imports from 'ehr' | backend/app/national/fhir/condition.py | 5 | 3.0 | ○ open | Samertts |
| TD-3565 | P2 | Cross-Domain Leakage | national.fhir.immunization:5 bounded context leakage: 'national' imports from 'e | backend/app/national/fhir/immunization.py | 5 | 3.0 | ○ open | Samertts |
| TD-3566 | P2 | Cross-Domain Leakage | national.fhir.medication_request:5 bounded context leakage: 'national' imports f | backend/app/national/fhir/medication_request.py | 5 | 3.0 | ○ open | Samertts |
| TD-3567 | P2 | Cross-Domain Leakage | national.fhir.medication_statement:5 bounded context leakage: 'national' imports | backend/app/national/fhir/medication_statement.py | 5 | 3.0 | ○ open | Samertts |
| TD-3568 | P2 | Cross-Domain Leakage | national.observability.api.routes:31 bounded context leakage: 'national' imports | backend/app/national/observability/api/routes.py | 31 | 3.0 | ○ open | Samertts |
| TD-3569 | P2 | Cross-Domain Leakage | national.observability.api.routes:32 bounded context leakage: 'national' imports | backend/app/national/observability/api/routes.py | 32 | 3.0 | ○ open | Samertts |
| TD-3570 | P2 | Cross-Domain Leakage | national.observability.application.service:9 bounded context leakage: 'national' | backend/app/national/observability/application/ser | 9 | 3.0 | ○ open | Samertts |
| TD-3571 | P2 | Cross-Domain Leakage | national.observability.application.service:10 bounded context leakage: 'national | backend/app/national/observability/application/ser | 10 | 3.0 | ○ open | Samertts |
| TD-3572 | P2 | Cross-Domain Leakage | national.rules_engine.api.routes:33 bounded context leakage: 'national' imports  | backend/app/national/rules_engine/api/routes.py | 33 | 3.0 | ○ open | Samertts |
| TD-3573 | P2 | Cross-Domain Leakage | national.rules_engine.api.routes:34 bounded context leakage: 'national' imports  | backend/app/national/rules_engine/api/routes.py | 34 | 3.0 | ○ open | Samertts |
| TD-3574 | P2 | Cross-Domain Leakage | national.rules_engine.application.service:9 bounded context leakage: 'national'  | backend/app/national/rules_engine/application/serv | 9 | 3.0 | ○ open | Samertts |
| TD-3575 | P2 | Cross-Domain Leakage | national.rules_engine.application.service:10 bounded context leakage: 'national' | backend/app/national/rules_engine/application/serv | 10 | 3.0 | ○ open | Samertts |
| TD-3576 | P2 | Cross-Domain Leakage | national.scheduling_platform.api.routes:38 bounded context leakage: 'national' i | backend/app/national/scheduling_platform/api/route | 38 | 3.0 | ○ open | Samertts |
| TD-3577 | P2 | Cross-Domain Leakage | national.scheduling_platform.api.routes:39 bounded context leakage: 'national' i | backend/app/national/scheduling_platform/api/route | 39 | 3.0 | ○ open | Samertts |
| TD-3578 | P2 | Cross-Domain Leakage | national.scheduling_platform.application.service:9 bounded context leakage: 'nat | backend/app/national/scheduling_platform/applicati | 9 | 3.0 | ○ open | Samertts |
| TD-3579 | P2 | Cross-Domain Leakage | national.scheduling_platform.application.service:10 bounded context leakage: 'na | backend/app/national/scheduling_platform/applicati | 10 | 3.0 | ○ open | Samertts |
| TD-3580 | P2 | Cross-Domain Leakage | national.search_platform.api.routes:25 bounded context leakage: 'national' impor | backend/app/national/search_platform/api/routes.py | 25 | 3.0 | ○ open | Samertts |
| TD-3581 | P2 | Cross-Domain Leakage | national.search_platform.api.routes:26 bounded context leakage: 'national' impor | backend/app/national/search_platform/api/routes.py | 26 | 3.0 | ○ open | Samertts |
| TD-3582 | P2 | Cross-Domain Leakage | national.search_platform.application.service:8 bounded context leakage: 'nationa | backend/app/national/search_platform/application/s | 8 | 3.0 | ○ open | Samertts |
| TD-3583 | P2 | Cross-Domain Leakage | national.search_platform.application.service:9 bounded context leakage: 'nationa | backend/app/national/search_platform/application/s | 9 | 3.0 | ○ open | Samertts |
| TD-3584 | P2 | Cross-Domain Leakage | national_data.models.ai_data.DeidentificationJob:3 bounded context leakage: 'nat | backend/app/national_data/models/ai_data/Deidentif | 3 | 3.0 | ○ open | Samertts |
| TD-3585 | P2 | Cross-Domain Leakage | national_data.models.ai_data.FeatureStore:3 bounded context leakage: 'national_d | backend/app/national_data/models/ai_data/FeatureSt | 3 | 3.0 | ○ open | Samertts |
| TD-3586 | P2 | Cross-Domain Leakage | national_data.models.ai_data.FeatureValue:6 bounded context leakage: 'national_d | backend/app/national_data/models/ai_data/FeatureVa | 6 | 3.0 | ○ open | Samertts |
| TD-3587 | P2 | Cross-Domain Leakage | national_data.models.ai_data.KnowledgeGraphEdge:3 bounded context leakage: 'nati | backend/app/national_data/models/ai_data/Knowledge | 3 | 3.0 | ○ open | Samertts |
| TD-3588 | P2 | Cross-Domain Leakage | national_data.models.ai_data.KnowledgeGraphNode:3 bounded context leakage: 'nati | backend/app/national_data/models/ai_data/Knowledge | 3 | 3.0 | ○ open | Samertts |
| TD-3589 | P2 | Cross-Domain Leakage | national_data.models.ai_data.SyntheticDataJob:3 bounded context leakage: 'nation | backend/app/national_data/models/ai_data/Synthetic | 3 | 3.0 | ○ open | Samertts |
| TD-3590 | P2 | Cross-Domain Leakage | national_data.models.ai_data.TrainingDataset:6 bounded context leakage: 'nationa | backend/app/national_data/models/ai_data/TrainingD | 6 | 3.0 | ○ open | Samertts |
| TD-3591 | P2 | Cross-Domain Leakage | national_data.models.ai_data.VectorEmbedding:6 bounded context leakage: 'nationa | backend/app/national_data/models/ai_data/VectorEmb | 6 | 3.0 | ○ open | Samertts |
| TD-3592 | P2 | Cross-Domain Leakage | national_data.models.canonical_document:8 bounded context leakage: 'national_dat | backend/app/national_data/models/canonical_documen | 8 | 3.0 | ○ open | Samertts |
| TD-3593 | P2 | Cross-Domain Leakage | national_data.models.canonical_document:9 bounded context leakage: 'national_dat | backend/app/national_data/models/canonical_documen | 9 | 3.0 | ○ open | Samertts |
| TD-3594 | P2 | Cross-Domain Leakage | national_data.models.canonical_document:10 bounded context leakage: 'national_da | backend/app/national_data/models/canonical_documen | 10 | 3.0 | ○ open | Samertts |
| TD-3595 | P2 | Cross-Domain Leakage | national_data.models.canonical_document:11 bounded context leakage: 'national_da | backend/app/national_data/models/canonical_documen | 11 | 3.0 | ○ open | Samertts |
| TD-3596 | P2 | Cross-Domain Leakage | national_data.models.canonical_encounter:9 bounded context leakage: 'national_da | backend/app/national_data/models/canonical_encount | 9 | 3.0 | ○ open | Samertts |
| TD-3597 | P2 | Cross-Domain Leakage | national_data.models.canonical_encounter:11 bounded context leakage: 'national_d | backend/app/national_data/models/canonical_encount | 11 | 3.0 | ○ open | Samertts |
| TD-3598 | P2 | Cross-Domain Leakage | national_data.models.canonical_encounter:12 bounded context leakage: 'national_d | backend/app/national_data/models/canonical_encount | 12 | 3.0 | ○ open | Samertts |
| TD-3599 | P2 | Cross-Domain Leakage | national_data.models.canonical_medication:8 bounded context leakage: 'national_d | backend/app/national_data/models/canonical_medicat | 8 | 3.0 | ○ open | Samertts |
| TD-3600 | P2 | Cross-Domain Leakage | national_data.models.canonical_medication:9 bounded context leakage: 'national_d | backend/app/national_data/models/canonical_medicat | 9 | 3.0 | ○ open | Samertts |
| TD-3601 | P2 | Cross-Domain Leakage | national_data.models.canonical_medication:9 bounded context leakage: 'national_d | backend/app/national_data/models/canonical_medicat | 9 | 3.0 | ○ open | Samertts |
| TD-3602 | P2 | Cross-Domain Leakage | national_data.models.canonical_medication:9 bounded context leakage: 'national_d | backend/app/national_data/models/canonical_medicat | 9 | 3.0 | ○ open | Samertts |
| TD-3603 | P2 | Cross-Domain Leakage | national_data.models.canonical_medication:9 bounded context leakage: 'national_d | backend/app/national_data/models/canonical_medicat | 9 | 3.0 | ○ open | Samertts |
| TD-3604 | P2 | Cross-Domain Leakage | national_data.models.canonical_medication:15 bounded context leakage: 'national_ | backend/app/national_data/models/canonical_medicat | 15 | 3.0 | ○ open | Samertts |
| TD-3605 | P2 | Cross-Domain Leakage | national_data.models.canonical_observation:9 bounded context leakage: 'national_ | backend/app/national_data/models/canonical_observa | 9 | 3.0 | ○ open | Samertts |
| TD-3606 | P2 | Cross-Domain Leakage | national_data.models.canonical_observation:13 bounded context leakage: 'national | backend/app/national_data/models/canonical_observa | 13 | 3.0 | ○ open | Samertts |
| TD-3607 | P2 | Cross-Domain Leakage | national_data.models.canonical_observation:14 bounded context leakage: 'national | backend/app/national_data/models/canonical_observa | 14 | 3.0 | ○ open | Samertts |
| TD-3608 | P2 | Cross-Domain Leakage | national_data.models.canonical_patient:9 bounded context leakage: 'national_data | backend/app/national_data/models/canonical_patient | 9 | 3.0 | ○ open | Samertts |
| TD-3609 | P2 | Cross-Domain Leakage | national_data.models.canonical_patient:11 bounded context leakage: 'national_dat | backend/app/national_data/models/canonical_patient | 11 | 3.0 | ○ open | Samertts |
| TD-3610 | P2 | Cross-Domain Leakage | national_data.models.canonical_patient:12 bounded context leakage: 'national_dat | backend/app/national_data/models/canonical_patient | 12 | 3.0 | ○ open | Samertts |
| TD-3611 | P2 | Cross-Domain Leakage | national_data.models.canonical_procedure:9 bounded context leakage: 'national_da | backend/app/national_data/models/canonical_procedu | 9 | 3.0 | ○ open | Samertts |
| TD-3612 | P2 | Cross-Domain Leakage | national_data.models.canonical_procedure:11 bounded context leakage: 'national_d | backend/app/national_data/models/canonical_procedu | 11 | 3.0 | ○ open | Samertts |
| TD-3613 | P2 | Cross-Domain Leakage | national_data.models.canonical_procedure:12 bounded context leakage: 'national_d | backend/app/national_data/models/canonical_procedu | 12 | 3.0 | ○ open | Samertts |
| TD-3614 | P2 | Cross-Domain Leakage | national_data.models.event_store.EventRetentionPolicy:3 bounded context leakage: | backend/app/national_data/models/event_store/Event | 3 | 3.0 | ○ open | Samertts |
| TD-3615 | P2 | Cross-Domain Leakage | national_data.models.event_store.EventSnapshot:6 bounded context leakage: 'natio | backend/app/national_data/models/event_store/Event | 6 | 3.0 | ○ open | Samertts |
| TD-3616 | P2 | Cross-Domain Leakage | national_data.models.event_store.StoredEvent:6 bounded context leakage: 'nationa | backend/app/national_data/models/event_store/Store | 6 | 3.0 | ○ open | Samertts |
| TD-3617 | P2 | Cross-Domain Leakage | national_data.models.governance.ConsentDirective:3 bounded context leakage: 'nat | backend/app/national_data/models/governance/Consen | 3 | 3.0 | ○ open | Samertts |
| TD-3618 | P2 | Cross-Domain Leakage | national_data.models.governance.DataCatalogEntry:3 bounded context leakage: 'nat | backend/app/national_data/models/governance/DataCa | 3 | 3.0 | ○ open | Samertts |
| TD-3619 | P2 | Cross-Domain Leakage | national_data.models.governance.DataClassification:3 bounded context leakage: 'n | backend/app/national_data/models/governance/DataCl | 3 | 3.0 | ○ open | Samertts |
| TD-3620 | P2 | Cross-Domain Leakage | national_data.models.governance.DataLineageEntry:6 bounded context leakage: 'nat | backend/app/national_data/models/governance/DataLi | 6 | 3.0 | ○ open | Samertts |
| TD-3621 | P2 | Cross-Domain Leakage | national_data.models.governance.DataQualityCheck:6 bounded context leakage: 'nat | backend/app/national_data/models/governance/DataQu | 6 | 3.0 | ○ open | Samertts |
| TD-3622 | P2 | Cross-Domain Leakage | national_data.models.governance.DataQualityRule:3 bounded context leakage: 'nati | backend/app/national_data/models/governance/DataQu | 3 | 3.0 | ○ open | Samertts |
| TD-3623 | P2 | Cross-Domain Leakage | national_data.models.governance.DataSteward:3 bounded context leakage: 'national | backend/app/national_data/models/governance/DataSt | 3 | 3.0 | ○ open | Samertts |
| TD-3624 | P2 | Cross-Domain Leakage | national_data.models.governance.MetadataEntry:3 bounded context leakage: 'nation | backend/app/national_data/models/governance/Metada | 3 | 3.0 | ○ open | Samertts |
| TD-3625 | P2 | Cross-Domain Leakage | national_data.models.governance.RetentionPolicy:3 bounded context leakage: 'nati | backend/app/national_data/models/governance/Retent | 3 | 3.0 | ○ open | Samertts |
| TD-3626 | P2 | Cross-Domain Leakage | national_data.models.mdm.DeviceRegistry:3 bounded context leakage: 'national_dat | backend/app/national_data/models/mdm/DeviceRegistr | 3 | 3.0 | ○ open | Samertts |
| TD-3627 | P2 | Cross-Domain Leakage | national_data.models.mdm.DuplicateRecord:3 bounded context leakage: 'national_da | backend/app/national_data/models/mdm/DuplicateReco | 3 | 3.0 | ○ open | Samertts |
| TD-3628 | P2 | Cross-Domain Leakage | national_data.models.mdm.GoldenRecord:3 bounded context leakage: 'national_data' | backend/app/national_data/models/mdm/GoldenRecord. | 3 | 3.0 | ○ open | Samertts |
| TD-3629 | P2 | Cross-Domain Leakage | national_data.models.mdm.LocationRegistry:3 bounded context leakage: 'national_d | backend/app/national_data/models/mdm/LocationRegis | 3 | 3.0 | ○ open | Samertts |
| TD-3630 | P2 | Cross-Domain Leakage | national_data.models.mdm.MergeAction:6 bounded context leakage: 'national_data'  | backend/app/national_data/models/mdm/MergeAction.p | 6 | 3.0 | ○ open | Samertts |
| TD-3631 | P2 | Cross-Domain Leakage | national_data.models.mdm.ProviderRegistry:3 bounded context leakage: 'national_d | backend/app/national_data/models/mdm/ProviderRegis | 3 | 3.0 | ○ open | Samertts |
| TD-3632 | P2 | Cross-Domain Leakage | national_data.models.mdm.SourceSystem:3 bounded context leakage: 'national_data' | backend/app/national_data/models/mdm/SourceSystem. | 3 | 3.0 | ○ open | Samertts |
| TD-3633 | P2 | Cross-Domain Leakage | national_data.models.mdm.TerminologyRegistry:3 bounded context leakage: 'nationa | backend/app/national_data/models/mdm/TerminologyRe | 3 | 3.0 | ○ open | Samertts |
| TD-3634 | P2 | Cross-Domain Leakage | national_data.models.warehouse.DimDate:3 bounded context leakage: 'national_data | backend/app/national_data/models/warehouse/DimDate | 3 | 3.0 | ○ open | Samertts |
| TD-3635 | P2 | Cross-Domain Leakage | national_data.models.warehouse.DimDiagnosis:3 bounded context leakage: 'national | backend/app/national_data/models/warehouse/DimDiag | 3 | 3.0 | ○ open | Samertts |
| TD-3636 | P2 | Cross-Domain Leakage | national_data.models.warehouse.DimFacility:3 bounded context leakage: 'national_ | backend/app/national_data/models/warehouse/DimFaci | 3 | 3.0 | ○ open | Samertts |
| TD-3637 | P2 | Cross-Domain Leakage | national_data.models.warehouse.DimPatient:3 bounded context leakage: 'national_d | backend/app/national_data/models/warehouse/DimPati | 3 | 3.0 | ○ open | Samertts |
| TD-3638 | P2 | Cross-Domain Leakage | national_data.models.warehouse.DimProvider:3 bounded context leakage: 'national_ | backend/app/national_data/models/warehouse/DimProv | 3 | 3.0 | ○ open | Samertts |
| TD-3639 | P2 | Cross-Domain Leakage | national_data.models.warehouse.FactDiagnosis:3 bounded context leakage: 'nationa | backend/app/national_data/models/warehouse/FactDia | 3 | 3.0 | ○ open | Samertts |
| TD-3640 | P2 | Cross-Domain Leakage | national_data.models.warehouse.FactLabResult:3 bounded context leakage: 'nationa | backend/app/national_data/models/warehouse/FactLab | 3 | 3.0 | ○ open | Samertts |
| TD-3641 | P2 | Cross-Domain Leakage | national_data.models.warehouse.FactPatientVisit:3 bounded context leakage: 'nati | backend/app/national_data/models/warehouse/FactPat | 3 | 3.0 | ○ open | Samertts |
| TD-3642 | P2 | Cross-Domain Leakage | nhdw.kpi:8 bounded context leakage: 'nhdw' imports from 'hospital' (hospital.mod | backend/app/nhdw/kpi.py | 8 | 3.0 | ○ open | Samertts |
| TD-3643 | P2 | Cross-Domain Leakage | nhdw.kpi:8 bounded context leakage: 'nhdw' imports from 'hospital' (hospital.mod | backend/app/nhdw/kpi.py | 8 | 3.0 | ○ open | Samertts |
| TD-3644 | P2 | Cross-Domain Leakage | nhdw.kpi:8 bounded context leakage: 'nhdw' imports from 'hospital' (hospital.mod | backend/app/nhdw/kpi.py | 8 | 3.0 | ○ open | Samertts |
| TD-3645 | P2 | Cross-Domain Leakage | nhdw.kpi:8 bounded context leakage: 'nhdw' imports from 'hospital' (hospital.mod | backend/app/nhdw/kpi.py | 8 | 3.0 | ○ open | Samertts |
| TD-3646 | P2 | Cross-Domain Leakage | nhdw.services:9 bounded context leakage: 'nhdw' imports from 'hospital' (hospita | backend/app/nhdw/services.py | 9 | 3.0 | ○ open | Samertts |
| TD-3647 | P2 | Cross-Domain Leakage | nhdw.services:9 bounded context leakage: 'nhdw' imports from 'hospital' (hospita | backend/app/nhdw/services.py | 9 | 3.0 | ○ open | Samertts |
| TD-3648 | P2 | Cross-Domain Leakage | nhdw.services:9 bounded context leakage: 'nhdw' imports from 'hospital' (hospita | backend/app/nhdw/services.py | 9 | 3.0 | ○ open | Samertts |
| TD-3649 | P2 | Cross-Domain Leakage | nursing.medication:13 bounded context leakage: 'nursing' imports from 'ehr' (app | backend/app/nursing/medication.py | 13 | 3.0 | ○ open | Samertts |
| TD-3650 | P2 | Cross-Domain Leakage | nursing.medication:13 bounded context leakage: 'nursing' imports from 'ehr' (app | backend/app/nursing/medication.py | 13 | 3.0 | ○ open | Samertts |
| TD-3651 | P2 | Cross-Domain Leakage | nursing.services:684 bounded context leakage: 'nursing' imports from 'ehr' (app. | backend/app/nursing/services.py | 684 | 3.0 | ○ open | Samertts |
| TD-3652 | P2 | Cross-Domain Leakage | nursing.services:684 bounded context leakage: 'nursing' imports from 'ehr' (app. | backend/app/nursing/services.py | 684 | 3.0 | ○ open | Samertts |
| TD-3653 | P2 | Cross-Domain Leakage | nursing.services:717 bounded context leakage: 'nursing' imports from 'ehr' (app. | backend/app/nursing/services.py | 717 | 3.0 | ○ open | Samertts |
| TD-3654 | P2 | Cross-Domain Leakage | nursing.services:717 bounded context leakage: 'nursing' imports from 'ehr' (app. | backend/app/nursing/services.py | 717 | 3.0 | ○ open | Samertts |
| TD-3655 | P2 | Cross-Domain Leakage | pilot_platform.api.routes:27 bounded context leakage: 'pilot_platform' imports f | backend/app/pilot_platform/api/routes.py | 27 | 3.0 | ○ open | Samertts |
| TD-3656 | P2 | Cross-Domain Leakage | pilot_platform.application.service:207 bounded context leakage: 'pilot_platform' | backend/app/pilot_platform/application/service.py | 207 | 3.0 | ○ open | Samertts |
| TD-3657 | P2 | Cross-Domain Leakage | pilot_platform.domain.events:3 bounded context leakage: 'pilot_platform' imports | backend/app/pilot_platform/domain/events.py | 3 | 3.0 | ○ open | Samertts |
| TD-3658 | P2 | Cross-Domain Leakage | pilot_platform.infrastructure.models:3 bounded context leakage: 'pilot_platform' | backend/app/pilot_platform/infrastructure/models.p | 3 | 3.0 | ○ open | Samertts |
| TD-3659 | P2 | Cross-Domain Leakage | platform.search:42 bounded context leakage: 'platform' imports from 'national' ( | backend/app/platform/search.py | 42 | 3.0 | ○ open | Samertts |
| TD-3660 | P2 | Cross-Domain Leakage | platform.validation:31 bounded context leakage: 'platform' imports from 'nationa | backend/app/platform/validation.py | 31 | 3.0 | ○ open | Samertts |
| TD-3661 | P2 | Cross-Domain Leakage | platform.validation:37 bounded context leakage: 'platform' imports from 'nationa | backend/app/platform/validation.py | 37 | 3.0 | ○ open | Samertts |
| TD-3662 | P2 | Cross-Domain Leakage | platform.workflow:33 bounded context leakage: 'platform' imports from 'national' | backend/app/platform/workflow.py | 33 | 3.0 | ○ open | Samertts |
| TD-3663 | P2 | Cross-Domain Leakage | platform.workflow:34 bounded context leakage: 'platform' imports from 'national' | backend/app/platform/workflow.py | 34 | 3.0 | ○ open | Samertts |
| TD-3664 | P2 | Cross-Domain Leakage | platform.workflow:45 bounded context leakage: 'platform' imports from 'national' | backend/app/platform/workflow.py | 45 | 3.0 | ○ open | Samertts |
| TD-3665 | P2 | Cross-Domain Leakage | platform.workflow:51 bounded context leakage: 'platform' imports from 'national' | backend/app/platform/workflow.py | 51 | 3.0 | ○ open | Samertts |
| TD-3666 | P2 | Cross-Domain Leakage | platform.workflow:66 bounded context leakage: 'platform' imports from 'national' | backend/app/platform/workflow.py | 66 | 3.0 | ○ open | Samertts |
| TD-3667 | P2 | Cross-Domain Leakage | public_health.api.routes:27 bounded context leakage: 'public_health' imports fro | backend/app/public_health/api/routes.py | 27 | 3.0 | ○ open | Samertts |
| TD-3668 | P2 | Cross-Domain Leakage | public_health.application.service:9 bounded context leakage: 'public_health' imp | backend/app/public_health/application/service.py | 9 | 3.0 | ○ open | Samertts |
| TD-3669 | P2 | Cross-Domain Leakage | public_health.application.service:205 bounded context leakage: 'public_health' i | backend/app/public_health/application/service.py | 205 | 3.0 | ○ open | Samertts |
| TD-3670 | P2 | Cross-Domain Leakage | public_health.application.service:205 bounded context leakage: 'public_health' i | backend/app/public_health/application/service.py | 205 | 3.0 | ○ open | Samertts |
| TD-3671 | P2 | Cross-Domain Leakage | public_health.application.service:225 bounded context leakage: 'public_health' i | backend/app/public_health/application/service.py | 225 | 3.0 | ○ open | Samertts |
| TD-3672 | P2 | Cross-Domain Leakage | public_health.application.service:225 bounded context leakage: 'public_health' i | backend/app/public_health/application/service.py | 225 | 3.0 | ○ open | Samertts |
| TD-3673 | P2 | Cross-Domain Leakage | public_health.domain.events:3 bounded context leakage: 'public_health' imports f | backend/app/public_health/domain/events.py | 3 | 3.0 | ○ open | Samertts |
| TD-3674 | P2 | Cross-Domain Leakage | public_health.infrastructure.models:3 bounded context leakage: 'public_health' i | backend/app/public_health/infrastructure/models.py | 3 | 3.0 | ○ open | Samertts |
| TD-3675 | P2 | Cross-Domain Leakage | research_platform.base:6 bounded context leakage: 'research_platform' imports fr | backend/app/research_platform/base.py | 6 | 3.0 | ○ open | Samertts |
| TD-3676 | P2 | Cross-Domain Leakage | research_platform.base:7 bounded context leakage: 'research_platform' imports fr | backend/app/research_platform/base.py | 7 | 3.0 | ○ open | Samertts |
| TD-3677 | P2 | Cross-Domain Leakage | research_platform.bi_dashboards:9 bounded context leakage: 'research_platform' i | backend/app/research_platform/bi_dashboards.py | 9 | 3.0 | ○ open | Samertts |
| TD-3678 | P2 | Cross-Domain Leakage | research_platform.bi_dashboards:10 bounded context leakage: 'research_platform'  | backend/app/research_platform/bi_dashboards.py | 10 | 3.0 | ○ open | Samertts |
| TD-3679 | P2 | Cross-Domain Leakage | research_platform.bi_dashboards:10 bounded context leakage: 'research_platform'  | backend/app/research_platform/bi_dashboards.py | 10 | 3.0 | ○ open | Samertts |
| TD-3680 | P2 | Cross-Domain Leakage | research_platform.data_lake:10 bounded context leakage: 'research_platform' impo | backend/app/research_platform/data_lake.py | 10 | 3.0 | ○ open | Samertts |
| TD-3681 | P2 | Cross-Domain Leakage | research_platform.data_lake:10 bounded context leakage: 'research_platform' impo | backend/app/research_platform/data_lake.py | 10 | 3.0 | ○ open | Samertts |
| TD-3682 | P2 | Cross-Domain Leakage | research_platform.data_lake:10 bounded context leakage: 'research_platform' impo | backend/app/research_platform/data_lake.py | 10 | 3.0 | ○ open | Samertts |
| TD-3683 | P2 | Cross-Domain Leakage | research_platform.data_lake:10 bounded context leakage: 'research_platform' impo | backend/app/research_platform/data_lake.py | 10 | 3.0 | ○ open | Samertts |
| TD-3684 | P2 | Cross-Domain Leakage | research_platform.data_lake:10 bounded context leakage: 'research_platform' impo | backend/app/research_platform/data_lake.py | 10 | 3.0 | ○ open | Samertts |
| TD-3685 | P2 | Cross-Domain Leakage | research_platform.data_lake:10 bounded context leakage: 'research_platform' impo | backend/app/research_platform/data_lake.py | 10 | 3.0 | ○ open | Samertts |
| TD-3686 | P2 | Cross-Domain Leakage | research_platform.data_lake:18 bounded context leakage: 'research_platform' impo | backend/app/research_platform/data_lake.py | 18 | 3.0 | ○ open | Samertts |
| TD-3687 | P2 | Cross-Domain Leakage | research_platform.data_lake:18 bounded context leakage: 'research_platform' impo | backend/app/research_platform/data_lake.py | 18 | 3.0 | ○ open | Samertts |
| TD-3688 | P2 | Cross-Domain Leakage | research_platform.data_lake:18 bounded context leakage: 'research_platform' impo | backend/app/research_platform/data_lake.py | 18 | 3.0 | ○ open | Samertts |
| TD-3689 | P2 | Cross-Domain Leakage | research_platform.epidemiology:10 bounded context leakage: 'research_platform' i | backend/app/research_platform/epidemiology.py | 10 | 3.0 | ○ open | Samertts |
| TD-3690 | P2 | Cross-Domain Leakage | research_platform.epidemiology:10 bounded context leakage: 'research_platform' i | backend/app/research_platform/epidemiology.py | 10 | 3.0 | ○ open | Samertts |
| TD-3691 | P2 | Cross-Domain Leakage | research_platform.gis:7 bounded context leakage: 'research_platform' imports fro | backend/app/research_platform/gis.py | 7 | 3.0 | ○ open | Samertts |
| TD-3692 | P2 | Cross-Domain Leakage | research_platform.gis:7 bounded context leakage: 'research_platform' imports fro | backend/app/research_platform/gis.py | 7 | 3.0 | ○ open | Samertts |
| TD-3693 | P2 | Cross-Domain Leakage | research_platform.integration:56 bounded context leakage: 'research_platform' im | backend/app/research_platform/integration.py | 56 | 3.0 | ○ open | Samertts |
| TD-3694 | P2 | Cross-Domain Leakage | research_platform.integration:56 bounded context leakage: 'research_platform' im | backend/app/research_platform/integration.py | 56 | 3.0 | ○ open | Samertts |
| TD-3695 | P2 | Cross-Domain Leakage | research_platform.kpi_engine:10 bounded context leakage: 'research_platform' imp | backend/app/research_platform/kpi_engine.py | 10 | 3.0 | ○ open | Samertts |
| TD-3696 | P2 | Cross-Domain Leakage | research_platform.kpi_engine:10 bounded context leakage: 'research_platform' imp | backend/app/research_platform/kpi_engine.py | 10 | 3.0 | ○ open | Samertts |
| TD-3697 | P2 | Cross-Domain Leakage | research_platform.open_apis:9 bounded context leakage: 'research_platform' impor | backend/app/research_platform/open_apis.py | 9 | 3.0 | ○ open | Samertts |
| TD-3698 | P2 | Cross-Domain Leakage | research_platform.open_apis:9 bounded context leakage: 'research_platform' impor | backend/app/research_platform/open_apis.py | 9 | 3.0 | ○ open | Samertts |
| TD-3699 | P2 | Cross-Domain Leakage | research_platform.population_health:8 bounded context leakage: 'research_platfor | backend/app/research_platform/population_health.py | 8 | 3.0 | ○ open | Samertts |
| TD-3700 | P2 | Cross-Domain Leakage | research_platform.population_health:8 bounded context leakage: 'research_platfor | backend/app/research_platform/population_health.py | 8 | 3.0 | ○ open | Samertts |
| TD-3701 | P2 | Cross-Domain Leakage | research_platform.registries:9 bounded context leakage: 'research_platform' impo | backend/app/research_platform/registries.py | 9 | 3.0 | ○ open | Samertts |
| TD-3702 | P2 | Cross-Domain Leakage | research_platform.research:9 bounded context leakage: 'research_platform' import | backend/app/research_platform/research.py | 9 | 3.0 | ○ open | Samertts |
| TD-3703 | P2 | Cross-Domain Leakage | research_platform.routes:11 bounded context leakage: 'research_platform' imports | backend/app/research_platform/routes.py | 11 | 3.0 | ○ open | Samertts |
| TD-3704 | P2 | Cross-Domain Leakage | research_platform.sdk:8 bounded context leakage: 'research_platform' imports fro | backend/app/research_platform/sdk.py | 8 | 3.0 | ○ open | Samertts |
| TD-3705 | P2 | Cross-Domain Leakage | research_platform.sdk:8 bounded context leakage: 'research_platform' imports fro | backend/app/research_platform/sdk.py | 8 | 3.0 | ○ open | Samertts |
| TD-3290 | P2 | Forbidden Imports | routes.admin:22 routes importing from database directly (from ..database import  | backend/app/routes/admin.py | 22 | 1.0 | ○ open | Claude |
| TD-3291 | P2 | Forbidden Imports | routes.ai:49 routes importing from database directly (from app.database import S | backend/app/routes/ai.py | 49 | 1.0 | ○ open | Claude |
| TD-3292 | P2 | Forbidden Imports | routes.ai_telemetry:50 routes importing from database directly (from app.databas | backend/app/routes/ai_telemetry.py | 50 | 1.0 | ○ open | Claude |
| TD-3293 | P2 | Forbidden Imports | routes.batch:7 routes importing from database directly (from ..database import g | backend/app/routes/batch.py | 7 | 1.0 | ○ open | Claude |
| TD-3294 | P2 | Forbidden Imports | routes.canonical_patient:8 routes importing from database directly (from ..datab | backend/app/routes/canonical_patient.py | 8 | 1.0 | ○ open | Samertts |
| TD-3295 | P2 | Forbidden Imports | routes.care_continuum:15 routes importing from database directly (from ..databas | backend/app/routes/care_continuum.py | 15 | 1.0 | ○ open | Samertts |
| TD-3296 | P2 | Forbidden Imports | routes.citizen_portal:41 routes importing from database directly (from ..databas | backend/app/routes/citizen_portal.py | 41 | 1.0 | ○ open | Claude |
| TD-3297 | P2 | Forbidden Imports | routes.claims:19 routes importing from database directly (from ..database import | backend/app/routes/claims.py | 19 | 1.0 | ○ open | Claude |
| TD-3298 | P2 | Forbidden Imports | routes.clinical:14 routes importing from database directly (from app.database im | backend/app/routes/clinical.py | 14 | 1.0 | ○ open | Samertts |
| TD-3299 | P2 | Forbidden Imports | routes.clinical:10 routes importing from models directly (from app.clinical.term | backend/app/routes/clinical.py | 10 | 1.0 | ○ open | Samertts |
| TD-3300 | P2 | Forbidden Imports | routes.clinical_documentation:12 routes importing from database directly (from a | backend/app/routes/clinical_documentation.py | 12 | 1.0 | ○ open | Samertts |
| TD-3301 | P2 | Forbidden Imports | routes.clinical_orders:12 routes importing from database directly (from app.data | backend/app/routes/clinical_orders.py | 12 | 1.0 | ○ open | Samertts |
| TD-3302 | P2 | Forbidden Imports | routes.clinical_quality:9 routes importing from database directly (from app.data | backend/app/routes/clinical_quality.py | 9 | 1.0 | ○ open | Samertts |
| TD-3303 | P2 | Forbidden Imports | routes.compliance:31 routes importing from database directly (from ..database im | backend/app/routes/compliance.py | 31 | 1.0 | ○ open | Claude |
| TD-3304 | P2 | Forbidden Imports | routes.consent:24 routes importing from database directly (from ..database impor | backend/app/routes/consent.py | 24 | 1.0 | ○ open | Claude |
| TD-3305 | P2 | Forbidden Imports | routes.critical_alerts:6 routes importing from database directly (from ..databas | backend/app/routes/critical_alerts.py | 6 | 1.0 | ○ open | Claude |
| TD-3306 | P2 | Forbidden Imports | routes.dashboard:9 routes importing from database directly (from ..database impo | backend/app/routes/dashboard.py | 9 | 1.0 | ○ open | Claude |
| TD-3307 | P2 | Forbidden Imports | routes.device_results:7 routes importing from database directly (from ..database | backend/app/routes/device_results.py | 7 | 1.0 | ○ open | Claude |
| TD-3308 | P2 | Forbidden Imports | routes.edge:46 routes importing from database directly (from ..database import g | backend/app/routes/edge.py | 46 | 1.0 | ○ open | Claude |
| TD-3309 | P2 | Forbidden Imports | routes.ehr:25 routes importing from database directly (from ..database import ge | backend/app/routes/ehr.py | 25 | 1.0 | ○ open | Samertts |
| TD-3310 | P2 | Forbidden Imports | routes.ehr_fhir:9 routes importing from database directly (from ..database impor | backend/app/routes/ehr_fhir.py | 9 | 1.0 | ○ open | Samertts |
| TD-3311 | P2 | Forbidden Imports | routes.ehr_fhir:10 routes importing from models directly (from ..ehr.models impo | backend/app/routes/ehr_fhir.py | 10 | 1.0 | ○ open | Samertts |
| TD-3312 | P2 | Forbidden Imports | routes.hospital:8 routes importing from database directly (from ..database impor | backend/app/routes/hospital.py | 8 | 1.0 | ○ open | Samertts |
| TD-3313 | P2 | Forbidden Imports | routes.hospital:9 routes importing from models directly (from ..hospital.models  | backend/app/routes/hospital.py | 9 | 1.0 | ○ open | Samertts |
| TD-3314 | P2 | Forbidden Imports | routes.id_scan:19 routes importing from database directly (from ..database impor | backend/app/routes/id_scan.py | 19 | 1.0 | ○ open | Claude |
| TD-3315 | P2 | Forbidden Imports | routes.identity:7 routes importing from database directly (from ..database impor | backend/app/routes/identity.py | 7 | 1.0 | ○ open | Claude |
| TD-3316 | P2 | Forbidden Imports | routes.labs:5 routes importing from database directly (from ..database import ge | backend/app/routes/labs.py | 5 | 1.0 | ○ open | Claude |
| TD-3317 | P2 | Forbidden Imports | routes.login:10 routes importing from database directly (from ..database import  | backend/app/routes/login.py | 10 | 1.0 | ○ open | Claude |
| TD-3318 | P2 | Forbidden Imports | routes.metrics:21 routes importing from database directly (from ..database impor | backend/app/routes/metrics.py | 21 | 1.0 | ○ open | Claude |
| TD-3319 | P2 | Forbidden Imports | routes.mfa:7 routes importing from database directly (from app.database import g | backend/app/routes/mfa.py | 7 | 1.0 | ○ open | Samertts |
| TD-3320 | P2 | Forbidden Imports | routes.mobile:23 routes importing from database directly (from ..database import | backend/app/routes/mobile.py | 23 | 1.0 | ○ open | Claude |
| TD-3321 | P2 | Forbidden Imports | routes.national_data:8 routes importing from database directly (from ..database  | backend/app/routes/national_data.py | 8 | 1.0 | ○ open | Samertts |
| TD-3322 | P2 | Forbidden Imports | routes.national_streaming:12 routes importing from database directly (from ..dat | backend/app/routes/national_streaming.py | 12 | 1.0 | ○ open | Samertts |
| TD-3323 | P2 | Forbidden Imports | routes.notifications:10 routes importing from database directly (from ..database | backend/app/routes/notifications.py | 10 | 1.0 | ○ open | Claude |
| TD-3324 | P2 | Forbidden Imports | routes.oauth2:16 routes importing from database directly (from ..database import | backend/app/routes/oauth2.py | 16 | 1.0 | ○ open | Samertts |
| TD-3325 | P2 | Forbidden Imports | routes.password_reset:10 routes importing from database directly (from app.datab | backend/app/routes/password_reset.py | 10 | 1.0 | ○ open | Samertts |
| TD-3326 | P2 | Forbidden Imports | routes.patient_card:26 routes importing from database directly (from ..database  | backend/app/routes/patient_card.py | 26 | 1.0 | ○ open | Claude |
| TD-3327 | P2 | Forbidden Imports | routes.patients:5 routes importing from database directly (from ..database impor | backend/app/routes/patients.py | 5 | 1.0 | ○ open | Claude |
| TD-3328 | P2 | Forbidden Imports | routes.qr:10 routes importing from database directly (from ..database import get | backend/app/routes/qr.py | 10 | 1.0 | ○ open | Claude |
| TD-3329 | P2 | Forbidden Imports | routes.quality_control:12 routes importing from database directly (from ..databa | backend/app/routes/quality_control.py | 12 | 1.0 | ○ open | Claude |
| TD-3330 | P2 | Forbidden Imports | routes.register:9 routes importing from database directly (from ..database impor | backend/app/routes/register.py | 9 | 1.0 | ○ open | Claude |
| TD-3331 | P2 | Forbidden Imports | routes.register:20 routes importing from models directly (from ..services.mpi.mo | backend/app/routes/register.py | 20 | 1.0 | ○ open | Claude |
| TD-3332 | P2 | Forbidden Imports | routes.results:6 routes importing from database directly (from ..database import | backend/app/routes/results.py | 6 | 1.0 | ○ open | Claude |
| TD-3333 | P2 | Forbidden Imports | routes.saml:11 routes importing from database directly (from ..database import g | backend/app/routes/saml.py | 11 | 1.0 | ○ open | Samertts |
| TD-3334 | P2 | Forbidden Imports | routes.samples:7 routes importing from database directly (from ..database import | backend/app/routes/samples.py | 7 | 1.0 | ○ open | Claude |
| TD-3335 | P2 | Forbidden Imports | routes.security:11 routes importing from database directly (from ..database impo | backend/app/routes/security.py | 11 | 1.0 | ○ open | Samertts |
| TD-3336 | P2 | Forbidden Imports | routes.service_accounts:9 routes importing from database directly (from ..databa | backend/app/routes/service_accounts.py | 9 | 1.0 | ○ open | Samertts |
| TD-3337 | P2 | Forbidden Imports | routes.setup:11 routes importing from database directly (from ..database import  | backend/app/routes/setup.py | 11 | 1.0 | ○ open | Claude |
| TD-3338 | P2 | Forbidden Imports | routes.stats:23 routes importing from database directly (from ..database import  | backend/app/routes/stats.py | 23 | 1.0 | ○ open | Claude |
| TD-3339 | P2 | Forbidden Imports | routes.test_results:28 routes importing from database directly (from ..database  | backend/app/routes/test_results.py | 28 | 1.0 | ○ open | Claude |
| TD-3340 | P2 | Forbidden Imports | routes.tiers:34 routes importing from database directly (from ..database import  | backend/app/routes/tiers.py | 34 | 1.0 | ○ open | Claude |
| TD-3256 | P2 | Layer Violations | routes.ai:49 routes imports from database (app.database.SessionLocal) | backend/app/routes/ai.py | 49 | 2.0 | ○ open | Claude |
| TD-3257 | P2 | Layer Violations | routes.ai:49 routes imports from database (app.database.get_db) | backend/app/routes/ai.py | 49 | 2.0 | ○ open | Claude |
| TD-3258 | P2 | Layer Violations | routes.ai:51 routes imports from models (app.models.audit_log.AuditLog) | backend/app/routes/ai.py | 51 | 2.0 | ○ open | Claude |
| TD-3259 | P2 | Layer Violations | routes.ai:52 routes imports from models (app.models.lab_order.LabOrder) | backend/app/routes/ai.py | 52 | 2.0 | ○ open | Claude |
| TD-3260 | P2 | Layer Violations | routes.ai:53 routes imports from models (app.models.lab_result.LabResult) | backend/app/routes/ai.py | 53 | 2.0 | ○ open | Claude |
| TD-3261 | P2 | Layer Violations | routes.ai:54 routes imports from models (app.models.patient.Patient) | backend/app/routes/ai.py | 54 | 2.0 | ○ open | Claude |
| TD-3262 | P2 | Layer Violations | routes.ai_telemetry:45 routes imports from core (app.core.ai_dataset_flags.requi | backend/app/routes/ai_telemetry.py | 45 | 2.0 | ○ open | Claude |
| TD-3263 | P2 | Layer Violations | routes.ai_telemetry:45 routes imports from core (app.core.ai_dataset_flags.requi | backend/app/routes/ai_telemetry.py | 45 | 2.0 | ○ open | Claude |
| TD-3264 | P2 | Layer Violations | routes.ai_telemetry:45 routes imports from core (app.core.ai_dataset_flags.statu | backend/app/routes/ai_telemetry.py | 45 | 2.0 | ○ open | Claude |
| TD-3265 | P2 | Layer Violations | routes.ai_telemetry:50 routes imports from database (app.database.get_db) | backend/app/routes/ai_telemetry.py | 50 | 2.0 | ○ open | Claude |
| TD-3266 | P2 | Layer Violations | routes.ai_telemetry:51 routes imports from models (app.models.ai_interaction.AIF | backend/app/routes/ai_telemetry.py | 51 | 2.0 | ○ open | Claude |
| TD-3267 | P2 | Layer Violations | routes.ai_telemetry:51 routes imports from models (app.models.ai_interaction.AII | backend/app/routes/ai_telemetry.py | 51 | 2.0 | ○ open | Claude |
| TD-3268 | P2 | Layer Violations | routes.ai_telemetry:51 routes imports from models (app.models.ai_interaction.AIR | backend/app/routes/ai_telemetry.py | 51 | 2.0 | ○ open | Claude |
| TD-3269 | P2 | Layer Violations | routes.ai_telemetry:51 routes imports from models (app.models.ai_interaction.AIU | backend/app/routes/ai_telemetry.py | 51 | 2.0 | ○ open | Claude |
| TD-3270 | P2 | Layer Violations | routes.ai_telemetry:57 routes imports from models (app.models.lab_user.LabUser) | backend/app/routes/ai_telemetry.py | 57 | 2.0 | ○ open | Claude |
| TD-3271 | P2 | Layer Violations | routes.clinical:14 routes imports from database (app.database.get_db) | backend/app/routes/clinical.py | 14 | 2.0 | ○ open | Samertts |
| TD-3272 | P2 | Layer Violations | routes.clinical:15 routes imports from models (app.models.lab_user.LabUser) | backend/app/routes/clinical.py | 15 | 2.0 | ○ open | Samertts |
| TD-3273 | P2 | Layer Violations | routes.clinical_documentation:12 routes imports from database (app.database.get_ | backend/app/routes/clinical_documentation.py | 12 | 2.0 | ○ open | Samertts |
| TD-3274 | P2 | Layer Violations | routes.clinical_documentation:13 routes imports from models (app.models.lab_user | backend/app/routes/clinical_documentation.py | 13 | 2.0 | ○ open | Samertts |
| TD-3275 | P2 | Layer Violations | routes.clinical_orders:12 routes imports from database (app.database.get_db) | backend/app/routes/clinical_orders.py | 12 | 2.0 | ○ open | Samertts |
| TD-3276 | P2 | Layer Violations | routes.clinical_orders:13 routes imports from models (app.models.lab_user.LabUse | backend/app/routes/clinical_orders.py | 13 | 2.0 | ○ open | Samertts |
| TD-3277 | P2 | Layer Violations | routes.clinical_quality:9 routes imports from database (app.database.get_db) | backend/app/routes/clinical_quality.py | 9 | 2.0 | ○ open | Samertts |
| TD-3278 | P2 | Layer Violations | routes.clinical_quality:10 routes imports from models (app.models.lab_user.LabUs | backend/app/routes/clinical_quality.py | 10 | 2.0 | ○ open | Samertts |
| TD-3279 | P2 | Layer Violations | routes.mfa:7 routes imports from database (app.database.get_db) | backend/app/routes/mfa.py | 7 | 2.0 | ○ open | Samertts |
| TD-3280 | P2 | Layer Violations | routes.password_reset:10 routes imports from database (app.database.get_db) | backend/app/routes/password_reset.py | 10 | 2.0 | ○ open | Samertts |
| TD-3281 | P2 | Layer Violations | routes.password_reset:11 routes imports from models (app.models.lab_user.LabUser | backend/app/routes/password_reset.py | 11 | 2.0 | ○ open | Samertts |
| TD-3823 | P3 | Documentation Gaps | _compat | — | — | 1.0 | ○ open | unassigned |
| TD-3824 | P3 | Documentation Gaps | ai_fabric.agents.base | — | — | 1.0 | ○ open | unassigned |
| TD-3825 | P3 | Documentation Gaps | ai_fabric.agents.citizen_agent | — | — | 1.0 | ○ open | unassigned |
| TD-3826 | P3 | Documentation Gaps | ai_fabric.agents.clinical_agent | — | — | 1.0 | ○ open | unassigned |
| TD-3827 | P3 | Documentation Gaps | ai_fabric.agents.engineering_agent | — | — | 1.0 | ○ open | unassigned |
| TD-3828 | P3 | Documentation Gaps | ai_fabric.agents.laboratory_agent | — | — | 1.0 | ○ open | unassigned |
| TD-3829 | P3 | Documentation Gaps | ai_fabric.agents.registry | — | — | 1.0 | ○ open | unassigned |
| TD-3830 | P3 | Documentation Gaps | ai_fabric.agents.security_agent | — | — | 1.0 | ○ open | unassigned |
| TD-3831 | P3 | Documentation Gaps | ai_fabric.base | — | — | 1.0 | ○ open | unassigned |
| TD-3832 | P3 | Documentation Gaps | ai_fabric.clinical | — | — | 1.0 | ○ open | unassigned |
| TD-3833 | P3 | Documentation Gaps | ai_fabric.enums | — | — | 1.0 | ○ open | unassigned |
| TD-3834 | P3 | Documentation Gaps | ai_fabric.gateway | — | — | 1.0 | ○ open | unassigned |
| TD-3835 | P3 | Documentation Gaps | ai_fabric.governance | — | — | 1.0 | ○ open | unassigned |
| TD-3836 | P3 | Documentation Gaps | ai_fabric.integration | — | — | 1.0 | ○ open | unassigned |
| TD-3837 | P3 | Documentation Gaps | ai_fabric.knowledge_graph | — | — | 1.0 | ○ open | unassigned |
| TD-3838 | P3 | Documentation Gaps | ai_fabric.laboratory_intelligence | — | — | 1.0 | ○ open | unassigned |
| TD-3839 | P3 | Documentation Gaps | ai_fabric.local_ai | — | — | 1.0 | ○ open | unassigned |
| TD-3840 | P3 | Documentation Gaps | ai_fabric.observability | — | — | 1.0 | ○ open | unassigned |
| TD-3841 | P3 | Documentation Gaps | ai_fabric.public_health | — | — | 1.0 | ○ open | unassigned |
| TD-3842 | P3 | Documentation Gaps | ai_fabric.rag | — | — | 1.0 | ○ open | unassigned |
| TD-3843 | P3 | Documentation Gaps | ai_fabric.routes | — | — | 1.0 | ○ open | unassigned |
| TD-3844 | P3 | Documentation Gaps | ai_fabric.sdk | — | — | 1.0 | ○ open | unassigned |
| TD-3845 | P3 | Documentation Gaps | ai_fabric.security | — | — | 1.0 | ○ open | unassigned |
| TD-3846 | P3 | Documentation Gaps | biomedical.api.routes | — | — | 1.0 | ○ open | unassigned |
| TD-3847 | P3 | Documentation Gaps | biomedical.application.service | — | — | 1.0 | ○ open | unassigned |
| TD-3848 | P3 | Documentation Gaps | biomedical.domain.entities | — | — | 1.0 | ○ open | unassigned |
| TD-3849 | P3 | Documentation Gaps | biomedical.domain.enums | — | — | 1.0 | ○ open | unassigned |
| TD-3850 | P3 | Documentation Gaps | biomedical.domain.events | — | — | 1.0 | ○ open | unassigned |
| TD-3851 | P3 | Documentation Gaps | biomedical.exceptions | — | — | 1.0 | ○ open | unassigned |
| TD-3852 | P3 | Documentation Gaps | biomedical.infrastructure.models | — | — | 1.0 | ○ open | unassigned |
| TD-3853 | P3 | Documentation Gaps | ai_fabric.routes:24 fabric_health | backend/app/ai_fabric/routes.py | 24 | 1.0 | ○ open | Samertts |
| TD-3854 | P3 | Documentation Gaps | ai_fabric.routes:29 fabric_chat | backend/app/ai_fabric/routes.py | 29 | 1.0 | ○ open | Samertts |
| TD-3855 | P3 | Documentation Gaps | ai_fabric.routes:35 fabric_embed | backend/app/ai_fabric/routes.py | 35 | 1.0 | ○ open | Samertts |
| TD-3856 | P3 | Documentation Gaps | ai_fabric.routes:41 list_providers | backend/app/ai_fabric/routes.py | 41 | 1.0 | ○ open | Samertts |
| TD-3857 | P3 | Documentation Gaps | ai_fabric.routes:46 gateway_cost | backend/app/ai_fabric/routes.py | 46 | 1.0 | ○ open | Samertts |
| TD-3858 | P3 | Documentation Gaps | ai_fabric.routes:51 local_ai_status | backend/app/ai_fabric/routes.py | 51 | 1.0 | ○ open | Samertts |
| TD-3859 | P3 | Documentation Gaps | ai_fabric.routes:56 rag_query | backend/app/ai_fabric/routes.py | 56 | 1.0 | ○ open | Samertts |
| TD-3860 | P3 | Documentation Gaps | ai_fabric.routes:62 rag_index | backend/app/ai_fabric/routes.py | 62 | 1.0 | ○ open | Samertts |
| TD-3861 | P3 | Documentation Gaps | ai_fabric.routes:70 kg_entity | backend/app/ai_fabric/routes.py | 70 | 1.0 | ○ open | Samertts |
| TD-3862 | P3 | Documentation Gaps | ai_fabric.routes:78 kg_related | backend/app/ai_fabric/routes.py | 78 | 1.0 | ○ open | Samertts |
| TD-3863 | P3 | Documentation Gaps | ai_fabric.routes:83 kg_search | backend/app/ai_fabric/routes.py | 83 | 1.0 | ○ open | Samertts |
| TD-3864 | P3 | Documentation Gaps | ai_fabric.routes:88 kg_statistics | backend/app/ai_fabric/routes.py | 88 | 1.0 | ○ open | Samertts |
| TD-3865 | P3 | Documentation Gaps | ai_fabric.routes:93 kg_traverse | backend/app/ai_fabric/routes.py | 93 | 1.0 | ○ open | Samertts |
| TD-3866 | P3 | Documentation Gaps | ai_fabric.routes:99 clinical_analyze | backend/app/ai_fabric/routes.py | 99 | 1.0 | ○ open | Samertts |
| TD-3867 | P3 | Documentation Gaps | ai_fabric.routes:110 clinical_summarize | backend/app/ai_fabric/routes.py | 110 | 1.0 | ○ open | Samertts |
| TD-3868 | P3 | Documentation Gaps | ai_fabric.routes:116 drug_interaction | backend/app/ai_fabric/routes.py | 116 | 1.0 | ○ open | Samertts |
| TD-3869 | P3 | Documentation Gaps | ai_fabric.routes:127 lab_delta_check | backend/app/ai_fabric/routes.py | 127 | 1.0 | ○ open | Samertts |
| TD-3870 | P3 | Documentation Gaps | ai_fabric.routes:138 lab_critical_detector | backend/app/ai_fabric/routes.py | 138 | 1.0 | ○ open | Samertts |
| TD-3871 | P3 | Documentation Gaps | ai_fabric.routes:149 lab_qc_analyze | backend/app/ai_fabric/routes.py | 149 | 1.0 | ○ open | Samertts |
| TD-3872 | P3 | Documentation Gaps | ai_fabric.routes:159 lab_workload_predict | backend/app/ai_fabric/routes.py | 159 | 1.0 | ○ open | Samertts |
| TD-3873 | P3 | Documentation Gaps | ai_fabric.routes:164 ph_surveillance | backend/app/ai_fabric/routes.py | 164 | 1.0 | ○ open | Samertts |
| TD-3874 | P3 | Documentation Gaps | ai_fabric.routes:174 ph_alerts | backend/app/ai_fabric/routes.py | 174 | 1.0 | ○ open | Samertts |
| TD-3875 | P3 | Documentation Gaps | ai_fabric.routes:181 ph_outbreak_detect | backend/app/ai_fabric/routes.py | 181 | 1.0 | ○ open | Samertts |
| TD-3876 | P3 | Documentation Gaps | ai_fabric.routes:187 gov_prompt_register | backend/app/ai_fabric/routes.py | 187 | 1.0 | ○ open | Samertts |
| TD-3877 | P3 | Documentation Gaps | ai_fabric.routes:194 gov_prompt_get | backend/app/ai_fabric/routes.py | 194 | 1.0 | ○ open | Samertts |
| TD-3878 | P3 | Documentation Gaps | ai_fabric.routes:202 gov_prompt_promote | backend/app/ai_fabric/routes.py | 202 | 1.0 | ○ open | Samertts |
| TD-3879 | P3 | Documentation Gaps | ai_fabric.routes:211 gov_model_submit | backend/app/ai_fabric/routes.py | 211 | 1.0 | ○ open | Samertts |
| TD-3880 | P3 | Documentation Gaps | ai_fabric.routes:216 gov_model_approve | backend/app/ai_fabric/routes.py | 216 | 1.0 | ○ open | Samertts |
| TD-3881 | P3 | Documentation Gaps | ai_fabric.routes:224 gov_evaluate | backend/app/ai_fabric/routes.py | 224 | 1.0 | ○ open | Samertts |
| TD-3882 | P3 | Documentation Gaps | ai_fabric.routes:231 gov_constitution | backend/app/ai_fabric/routes.py | 231 | 1.0 | ○ open | Samertts |
| TD-3706 | P3 | Large Files/Functions | lims.models: 1368 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3707 | P3 | Large Files/Functions | lims.routes: 1687 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3708 | P3 | Large Files/Functions | main: 1948 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3709 | P3 | Large Files/Functions | nhdw.routes: 1056 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3710 | P3 | Large Files/Functions | nhdw.services: 1024 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3711 | P3 | Large Files/Functions | nursing.routes: 1265 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3712 | P3 | Large Files/Functions | pharmacy.routes: 1205 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3713 | P3 | Large Files/Functions | radiology.routes: 1325 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3714 | P3 | Large Files/Functions | routes.admin: 1131 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3715 | P3 | Large Files/Functions | routes.ai: 1077 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3716 | P3 | Large Files/Functions | routes.care_continuum: 1016 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3717 | P3 | Large Files/Functions | routes.clinical: 1324 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3718 | P3 | Large Files/Functions | routes.compliance: 1227 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3719 | P3 | Large Files/Functions | routes.ehr: 2072 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3720 | P3 | Large Files/Functions | routes.ehr_fhir: 1003 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3721 | P3 | Large Files/Functions | services.care_continuum_service: 1084 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3722 | P3 | Large Files/Functions | services.clinical_service: 1336 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3723 | P3 | Large Files/Functions | services.ehr_service: 1324 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3724 | P3 | Large Files/Functions | services.interpretation: 1276 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3725 | P3 | Large Files/Functions | simulation.engine: 1339 lines | — | — | 2.0 | ○ open | unassigned |
| TD-3726 | P3 | Large Files/Functions | certification.dimensions.accessibility:12 evaluate() = 140 lines | backend/app/certification/dimensions/accessibility | 12 | 2.0 | ○ open | Samertts |
| TD-3727 | P3 | Large Files/Functions | certification.dimensions.db_integrity:9 evaluate() = 115 lines | backend/app/certification/dimensions/db_integrity. | 9 | 2.0 | ○ open | Samertts |
| TD-3728 | P3 | Large Files/Functions | certification.dimensions.documentation:10 evaluate() = 133 lines | backend/app/certification/dimensions/documentation | 10 | 2.0 | ○ open | Samertts |
| TD-3729 | P3 | Large Files/Functions | certification.dimensions.fhir_compliance:21 evaluate() = 102 lines | backend/app/certification/dimensions/fhir_complian | 21 | 2.0 | ○ open | Samertts |
| TD-3730 | P3 | Large Files/Functions | certification.dimensions.maintainability:14 evaluate() = 126 lines | backend/app/certification/dimensions/maintainabili | 14 | 2.0 | ○ open | Samertts |
| TD-3731 | P3 | Large Files/Functions | certification.dimensions.offline:9 evaluate() = 115 lines | backend/app/certification/dimensions/offline.py | 9 | 2.0 | ○ open | Samertts |
| TD-3732 | P3 | Large Files/Functions | certification.dimensions.performance:14 evaluate() = 101 lines | backend/app/certification/dimensions/performance.p | 14 | 2.0 | ○ open | Samertts |
| TD-3733 | P3 | Large Files/Functions | certification.dimensions.reliability:9 evaluate() = 130 lines | backend/app/certification/dimensions/reliability.p | 9 | 2.0 | ○ open | Samertts |
| TD-3734 | P3 | Large Files/Functions | certification.dimensions.test_coverage:16 evaluate() = 108 lines | backend/app/certification/dimensions/test_coverage | 16 | 2.0 | ○ open | Samertts |
| TD-3735 | P3 | Large Files/Functions | contracts.fhir:613 get_capability_statement() = 145 lines | backend/app/contracts/fhir.py | 613 | 2.0 | ○ open | Samertts |
| TD-3736 | P3 | Large Files/Functions | contracts.generator:181 generate_graphql_schema() = 166 lines | backend/app/contracts/generator.py | 181 | 2.0 | ○ open | Samertts |
| TD-3737 | P3 | Large Files/Functions | core.startup_guard:361 _run_seed_test_types() = 195 lines | backend/app/core/startup_guard.py | 361 | 2.0 | ○ open | Claude |
| TD-3738 | P3 | Large Files/Functions | engineering.cqrs.generator:21 generate() = 154 lines | backend/app/engineering/cqrs/generator.py | 21 | 2.0 | ○ open | Samertts |
| TD-3739 | P3 | Large Files/Functions | engineering.deployment.github_actions:246 generate() = 224 lines | backend/app/engineering/deployment/github_actions. | 246 | 2.0 | ○ open | Samertts |
| TD-3740 | P3 | Large Files/Functions | engineering.generators.microservice:27 generate() = 152 lines | backend/app/engineering/generators/microservice.py | 27 | 2.0 | ○ open | Samertts |
| TD-3741 | P3 | Large Files/Functions | engineering.generators.module:22 generate() = 202 lines | backend/app/engineering/generators/module.py | 22 | 2.0 | ○ open | Samertts |
| TD-3742 | P3 | Large Files/Functions | engineering.generators.plugin:20 generate() = 107 lines | backend/app/engineering/generators/plugin.py | 20 | 2.0 | ○ open | Samertts |
| TD-3743 | P3 | Large Files/Functions | engineering.productivity.cli:23 main() = 111 lines | backend/app/engineering/productivity/cli.py | 23 | 2.0 | ○ open | Samertts |
| TD-3744 | P3 | Large Files/Functions | engineering.productivity.cli:809 _handle_capability() = 156 lines | backend/app/engineering/productivity/cli.py | 809 | 2.0 | ○ open | Samertts |
| TD-3745 | P3 | Large Files/Functions | gateways.lab_device_gateway:107 receive_device_result() = 103 lines | backend/app/gateways/lab_device_gateway.py | 107 | 2.0 | ○ open | Claude |
| TD-3746 | P3 | Large Files/Functions | kernel.capabilities_registry_populator:23 _get_all_descriptors() = 657 lines | backend/app/kernel/capabilities_registry_populator | 23 | 2.0 | ○ open | Samertts |
| TD-3747 | P3 | Large Files/Functions | kernel.generate_capabilities:12 generate_all_capabilities() = 154 lines | backend/app/kernel/generate_capabilities.py | 12 | 2.0 | ○ open | Samertts |
| TD-3748 | P3 | Large Files/Functions | knowledge_graph.cross_reference:200 build_knowledge_graph() = 107 lines | backend/app/knowledge_graph/cross_reference.py | 200 | 2.0 | ○ open | Samertts |
| TD-3749 | P3 | Large Files/Functions | knowledge_graph.engine:139 scan_file() = 183 lines | backend/app/knowledge_graph/engine.py | 139 | 2.0 | ○ open | Samertts |
| TD-3750 | P3 | Large Files/Functions | lims.workflows:21 auto_validate_result() = 135 lines | backend/app/lims/workflows.py | 21 | 2.0 | ○ open | Samertts |
| TD-3751 | P3 | Large Files/Functions | main:1296 _health_alert_loop() = 162 lines | backend/app/main.py | 1296 | 2.0 | ○ open | Samertts |
| TD-3752 | P3 | Large Files/Functions | main:1745 health_deep() = 142 lines | backend/app/main.py | 1745 | 2.0 | ○ open | Samertts |
| TD-3753 | P3 | Large Files/Functions | routes.ai:856 interpret_result_public() = 137 lines | backend/app/routes/ai.py | 856 | 2.0 | ○ open | Claude |
| TD-3754 | P3 | Large Files/Functions | routes.ai_telemetry:202 log_interaction() = 115 lines | backend/app/routes/ai_telemetry.py | 202 | 2.0 | ○ open | Claude |
| TD-3755 | P3 | Large Files/Functions | routes.citizen_portal:138 citizen_login() = 102 lines | backend/app/routes/citizen_portal.py | 138 | 2.0 | ○ open | Claude |
| TD-3756 | P3 | Large Files/Functions | routes.compliance:361 get_fhir_diagnostic_report() = 104 lines | backend/app/routes/compliance.py | 361 | 2.0 | ○ open | Claude |
| TD-3757 | P3 | Large Files/Functions | routes.compliance:560 get_dhis2_aggregate() = 111 lines | backend/app/routes/compliance.py | 560 | 2.0 | ○ open | Claude |
| TD-3758 | P3 | Large Files/Functions | routes.compliance:711 security_report() = 109 lines | backend/app/routes/compliance.py | 711 | 2.0 | ○ open | Claude |
| TD-3759 | P3 | Large Files/Functions | routes.compliance:827 time_sync_status() = 103 lines | backend/app/routes/compliance.py | 827 | 2.0 | ○ open | Claude |
| TD-3760 | P3 | Large Files/Functions | routes.compliance:934 system_status() = 203 lines | backend/app/routes/compliance.py | 934 | 2.0 | ○ open | Claude |
| TD-3761 | P3 | Large Files/Functions | routes.dashboard:52 dashboard() = 134 lines | backend/app/routes/dashboard.py | 52 | 2.0 | ○ open | Claude |
| TD-3762 | P3 | Large Files/Functions | routes.login:42 login() = 132 lines | backend/app/routes/login.py | 42 | 2.0 | ○ open | Claude |
| TD-3763 | P3 | Large Files/Functions | routes.metrics:146 prometheus_metrics() = 198 lines | backend/app/routes/metrics.py | 146 | 2.0 | ○ open | Claude |
| TD-3764 | P3 | Large Files/Functions | routes.mobile:52 refresh_access_token() = 105 lines | backend/app/routes/mobile.py | 52 | 2.0 | ○ open | Claude |
| TD-3765 | P3 | Large Files/Functions | routes.register:545 register_doctor() = 107 lines | backend/app/routes/register.py | 545 | 2.0 | ○ open | Claude |
| TD-3766 | P3 | Large Files/Functions | routes.test_results:278 create_test_result() = 153 lines | backend/app/routes/test_results.py | 278 | 2.0 | ○ open | Claude |
| TD-3767 | P3 | Large Files/Functions | security.consent_dep:74 require_consent() = 117 lines | backend/app/security/consent_dep.py | 74 | 2.0 | ○ open | Claude |
| TD-3768 | P3 | Large Files/Functions | services.ehr_service:1180 build_live_timeline() = 142 lines | backend/app/services/ehr_service.py | 1180 | 2.0 | ○ open | Samertts |
| TD-3769 | P3 | Large Files/Functions | services.epidemiology:36 detect_outbreak() = 108 lines | backend/app/services/epidemiology.py | 36 | 2.0 | ○ open | Claude |
| TD-3770 | P3 | Large Files/Functions | services.mpi.resolver:163 resolve_identity() = 171 lines | backend/app/services/mpi/resolver.py | 163 | 2.0 | ○ open | Claude |
| TD-3771 | P3 | Large Files/Functions | services.order_service:318 create_order() = 114 lines | backend/app/services/order_service.py | 318 | 2.0 | ○ open | Samertts |
| TD-3772 | P3 | Large Files/Functions | services.pdf_report:141 generate_result_pdf() = 289 lines | backend/app/services/pdf_report.py | 141 | 2.0 | ○ open | Claude |
| TD-3896 | P3 | Missing ADRs | G1: No ADR for Layer Restructuring | — | — | 2.0 | ○ open | unassigned |
| TD-3897 | P3 | Missing ADRs | G2: No ADR for UUID Migration | — | — | 2.0 | ○ open | unassigned |
| TD-3899 | P3 | Missing ADRs | G4: No ADR for mTLS | — | — | 2.0 | ○ open | unassigned |
| TD-3900 | P3 | Missing ADRs | G5: No ADR for FHIR Strategy | — | — | 2.0 | ○ open | unassigned |
| TD-3901 | P3 | Missing ADRs | G6: No ADR for SBOM | — | — | 1.0 | ○ open | unassigned |
| TD-3773 | P3 | Naming Violations | capabilities.clinical_foundation.capability:11 Class 'Clinical_foundationCapabil | backend/app/capabilities/clinical_foundation/capab | 11 | 0.5 | ○ open | Samertts |
| TD-3774 | P3 | Naming Violations | capabilities.clinical_foundation.commands.add_allergy:8 Class 'Add_allergyComman | backend/app/capabilities/clinical_foundation/comma | 8 | 0.5 | ○ open | Samertts |
| TD-3775 | P3 | Naming Violations | capabilities.clinical_foundation.commands.add_diagnosis:8 Class 'Add_diagnosisCo | backend/app/capabilities/clinical_foundation/comma | 8 | 0.5 | ○ open | Samertts |
| TD-3776 | P3 | Naming Violations | capabilities.clinical_foundation.commands.add_medication:8 Class 'Add_medication | backend/app/capabilities/clinical_foundation/comma | 8 | 0.5 | ○ open | Samertts |
| TD-3777 | P3 | Naming Violations | capabilities.clinical_foundation.commands.record_vitals:8 Class 'Record_vitalsCo | backend/app/capabilities/clinical_foundation/comma | 8 | 0.5 | ○ open | Samertts |
| TD-3778 | P3 | Naming Violations | capabilities.clinical_foundation.contract:10 Class 'Clinical_foundationInput' sh | backend/app/capabilities/clinical_foundation/contr | 10 | 0.5 | ○ open | Samertts |
| TD-3779 | P3 | Naming Violations | capabilities.clinical_foundation.contract:17 Class 'Clinical_foundationOutput' s | backend/app/capabilities/clinical_foundation/contr | 17 | 0.5 | ○ open | Samertts |
| TD-3780 | P3 | Naming Violations | capabilities.clinical_foundation.permissions:6 Class 'Clinical_foundationPermiss | backend/app/capabilities/clinical_foundation/permi | 6 | 0.5 | ○ open | Samertts |
| TD-3781 | P3 | Naming Violations | capabilities.clinical_foundation.policies:4 Class 'Clinical_foundationPolicy' sh | backend/app/capabilities/clinical_foundation/polic | 4 | 0.5 | ○ open | Samertts |
| TD-3782 | P3 | Naming Violations | capabilities.clinical_foundation.queries.get_active_problems:7 Class 'Get_active | backend/app/capabilities/clinical_foundation/queri | 7 | 0.5 | ○ open | Samertts |
| TD-3783 | P3 | Naming Violations | capabilities.clinical_foundation.queries.get_clinical_history:7 Class 'Get_clini | backend/app/capabilities/clinical_foundation/queri | 7 | 0.5 | ○ open | Samertts |
| TD-3784 | P3 | Naming Violations | capabilities.clinical_foundation.queries.get_medication_list:7 Class 'Get_medica | backend/app/capabilities/clinical_foundation/queri | 7 | 0.5 | ○ open | Samertts |
| TD-3785 | P3 | Naming Violations | capabilities.document_management.application.service:7 Class 'Document_managemen | backend/app/capabilities/document_management/appli | 7 | 0.5 | ○ open | Samertts |
| TD-3786 | P3 | Naming Violations | capabilities.document_management.capability:11 Class 'Document_managementCapabil | backend/app/capabilities/document_management/capab | 11 | 0.5 | ○ open | Samertts |
| TD-3787 | P3 | Naming Violations | capabilities.document_management.commands.delete_document:8 Class 'Delete_docume | backend/app/capabilities/document_management/comma | 8 | 0.5 | ○ open | Samertts |
| TD-3788 | P3 | Naming Violations | capabilities.document_management.commands.ocr_document:8 Class 'Ocr_documentComm | backend/app/capabilities/document_management/comma | 8 | 0.5 | ○ open | Samertts |
| TD-3789 | P3 | Naming Violations | capabilities.document_management.commands.sign_document:8 Class 'Sign_documentCo | backend/app/capabilities/document_management/comma | 8 | 0.5 | ○ open | Samertts |
| TD-3790 | P3 | Naming Violations | capabilities.document_management.commands.upload_document:8 Class 'Upload_docume | backend/app/capabilities/document_management/comma | 8 | 0.5 | ○ open | Samertts |
| TD-3791 | P3 | Naming Violations | capabilities.document_management.contract:10 Class 'Document_managementInput' sh | backend/app/capabilities/document_management/contr | 10 | 0.5 | ○ open | Samertts |
| TD-3792 | P3 | Naming Violations | capabilities.document_management.contract:17 Class 'Document_managementOutput' s | backend/app/capabilities/document_management/contr | 17 | 0.5 | ○ open | Samertts |
| TD-3793 | P3 | Naming Violations | capabilities.document_management.domain.entities:9 Class 'Document_management' s | backend/app/capabilities/document_management/domai | 9 | 0.5 | ○ open | Samertts |
| TD-3794 | P3 | Naming Violations | capabilities.document_management.domain.repository:6 Class 'Document_managementR | backend/app/capabilities/document_management/domai | 6 | 0.5 | ○ open | Samertts |
| TD-3795 | P3 | Naming Violations | capabilities.document_management.dto:7 Class 'Document_managementCreateRequest'  | backend/app/capabilities/document_management/dto.p | 7 | 0.5 | ○ open | Samertts |
| TD-3796 | P3 | Naming Violations | capabilities.document_management.dto:15 Class 'Document_managementUpdateRequest' | backend/app/capabilities/document_management/dto.p | 15 | 0.5 | ○ open | Samertts |
| TD-3797 | P3 | Naming Violations | capabilities.document_management.dto:23 Class 'Document_managementResponse' shou | backend/app/capabilities/document_management/dto.p | 23 | 0.5 | ○ open | Samertts |
| TD-3798 | P3 | Naming Violations | capabilities.document_management.infrastructure.repository:11 Class 'SQLAlchemyD | backend/app/capabilities/document_management/infra | 11 | 0.5 | ○ open | Samertts |
| TD-3799 | P3 | Naming Violations | capabilities.document_management.permissions:6 Class 'Document_managementPermiss | backend/app/capabilities/document_management/permi | 6 | 0.5 | ○ open | Samertts |
| TD-3800 | P3 | Naming Violations | capabilities.document_management.policies:4 Class 'Document_managementPolicy' sh | backend/app/capabilities/document_management/polic | 4 | 0.5 | ○ open | Samertts |
| TD-3801 | P3 | Naming Violations | capabilities.document_management.queries.get_document:7 Class 'Get_documentQuery | backend/app/capabilities/document_management/queri | 7 | 0.5 | ○ open | Samertts |
| TD-3802 | P3 | Naming Violations | capabilities.document_management.queries.list_document_versions:7 Class 'List_do | backend/app/capabilities/document_management/queri | 7 | 0.5 | ○ open | Samertts |
| TD-3803 | P3 | Naming Violations | capabilities.document_management.queries.search_documents:7 Class 'Search_docume | backend/app/capabilities/document_management/queri | 7 | 0.5 | ○ open | Samertts |
| TD-3804 | P3 | Naming Violations | capabilities.encounter_management.application.service:7 Class 'Encounter_managem | backend/app/capabilities/encounter_management/appl | 7 | 0.5 | ○ open | Samertts |
| TD-3805 | P3 | Naming Violations | capabilities.encounter_management.capability:11 Class 'Encounter_managementCapab | backend/app/capabilities/encounter_management/capa | 11 | 0.5 | ○ open | Samertts |
| TD-3806 | P3 | Naming Violations | capabilities.encounter_management.commands.add_clinical_note:8 Class 'Add_clinic | backend/app/capabilities/encounter_management/comm | 8 | 0.5 | ○ open | Samertts |
| TD-3807 | P3 | Naming Violations | capabilities.encounter_management.commands.create_encounter:8 Class 'Create_enco | backend/app/capabilities/encounter_management/comm | 8 | 0.5 | ○ open | Samertts |
| TD-3808 | P3 | Naming Violations | capabilities.encounter_management.contract:10 Class 'Encounter_managementInput'  | backend/app/capabilities/encounter_management/cont | 10 | 0.5 | ○ open | Samertts |
| TD-3809 | P3 | Naming Violations | capabilities.encounter_management.contract:17 Class 'Encounter_managementOutput' | backend/app/capabilities/encounter_management/cont | 17 | 0.5 | ○ open | Samertts |
| TD-3810 | P3 | Naming Violations | capabilities.encounter_management.domain.entities:9 Class 'Encounter_management' | backend/app/capabilities/encounter_management/doma | 9 | 0.5 | ○ open | Samertts |
| TD-3811 | P3 | Naming Violations | capabilities.encounter_management.domain.repository:6 Class 'Encounter_managemen | backend/app/capabilities/encounter_management/doma | 6 | 0.5 | ○ open | Samertts |
| TD-3812 | P3 | Naming Violations | capabilities.encounter_management.dto:7 Class 'Encounter_managementCreateRequest | backend/app/capabilities/encounter_management/dto. | 7 | 0.5 | ○ open | Samertts |
| TD-3813 | P3 | Naming Violations | capabilities.encounter_management.dto:14 Class 'Encounter_managementUpdateReques | backend/app/capabilities/encounter_management/dto. | 14 | 0.5 | ○ open | Samertts |
| TD-3814 | P3 | Naming Violations | capabilities.encounter_management.dto:21 Class 'Encounter_managementResponse' sh | backend/app/capabilities/encounter_management/dto. | 21 | 0.5 | ○ open | Samertts |
| TD-3815 | P3 | Naming Violations | capabilities.encounter_management.infrastructure.repository:11 Class 'SQLAlchemy | backend/app/capabilities/encounter_management/infr | 11 | 0.5 | ○ open | Samertts |
| TD-3816 | P3 | Naming Violations | capabilities.encounter_management.permissions:6 Class 'Encounter_managementPermi | backend/app/capabilities/encounter_management/perm | 6 | 0.5 | ○ open | Samertts |
| TD-3817 | P3 | Naming Violations | capabilities.encounter_management.policies:4 Class 'Encounter_managementPolicy'  | backend/app/capabilities/encounter_management/poli | 4 | 0.5 | ○ open | Samertts |
| TD-3818 | P3 | Naming Violations | capabilities.encounter_management.queries.get_encounter:7 Class 'Get_encounterQu | backend/app/capabilities/encounter_management/quer | 7 | 0.5 | ○ open | Samertts |
| TD-3819 | P3 | Naming Violations | capabilities.encounter_management.queries.get_patient_timeline:7 Class 'Get_pati | backend/app/capabilities/encounter_management/quer | 7 | 0.5 | ○ open | Samertts |
| TD-3820 | P3 | Naming Violations | capabilities.encounter_management.queries.list_encounters:7 Class 'List_encounte | backend/app/capabilities/encounter_management/quer | 7 | 0.5 | ○ open | Samertts |
| TD-3821 | P3 | Naming Violations | capabilities.fhir_interoperability.capability:11 Class 'Fhir_interoperabilityCap | backend/app/capabilities/fhir_interoperability/cap | 11 | 0.5 | ○ open | Samertts |
| TD-3822 | P3 | Naming Violations | capabilities.fhir_interoperability.commands.convert_from_hl7:8 Class 'Convert_fr | backend/app/capabilities/fhir_interoperability/com | 8 | 0.5 | ○ open | Samertts |

---
*Registry auto-generated by `scripts/technical_debt_registry.py` at 2026-07-18 12:18 UTC*
