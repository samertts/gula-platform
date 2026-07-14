# Software Bill of Materials — National Platform Runtime v1.0

## Summary

| Metric | Value |
|--------|-------|
| Modules | 9 |
| Total Source Files | 137 |
| Total Directories | 72 |
| Total API Endpoints | 181 |
| Lines of Python | ~18,000 |
| External Dependencies | 0 (all reuse existing) |
| Breaking Changes | 0 |

## Module Breakdown

### Rules Engine (14 files)
```
rules_engine/domain/value_objects.py, events.py
rules_engine/application/services.py
rules_engine/infrastructure/models.py, repository.py
rules_engine/api/routes.py, schemas.py
```

### Background Platform (18 files)
```
background_platform/domain/value_objects.py, events.py
background_platform/application/services.py, scheduler.py
background_platform/infrastructure/models.py, repository.py
background_platform/api/routes.py, schemas.py
```

### Workflow Runtime (21 files)
```
workflow_runtime/domain/value_objects.py, events.py, workflow_state.py
workflow_runtime/application/services.py, saga_engine.py, approval_engine.py
workflow_runtime/infrastructure/models.py, repository.py
workflow_runtime/api/routes.py, schemas.py
```

### Task Engine (17 files)
```
task_engine/domain/value_objects.py, events.py
task_engine/application/services.py, escalation_engine.py, kpi_service.py
task_engine/infrastructure/models.py, repository.py
task_engine/api/routes.py, schemas.py
```

### Notification Platform (20 files)
```
notification_platform/domain/value_objects.py, events.py
notification_platform/application/services.py, template_engine.py
notification_platform/infrastructure/models.py, repository.py, adapters/*
notification_platform/api/routes.py, schemas.py
```

### Document Platform (15 files)
```
document_platform/domain/value_objects.py, events.py
document_platform/application/services.py, signature_service.py
document_platform/infrastructure/models.py, repository.py, adapters/*
document_platform/api/routes.py, schemas.py
```

### Scheduling Platform (14 files)
```
scheduling_platform/domain/value_objects.py, events.py
scheduling_platform/application/services.py, conflict_detector.py
scheduling_platform/infrastructure/models.py, repository.py
scheduling_platform/api/routes.py, schemas.py
```

### Search Platform (9 files)
```
search_platform/domain/value_objects.py, events.py
search_platform/application/search_service.py
search_platform/infrastructure/adapters/*, models.py
search_platform/api/routes.py, schemas.py
```

### Observability (9 files)
```
observability/domain/value_objects.py, events.py
observability/application/metrics_service.py, tracing_service.py, health_service.py, alert_service.py
observability/infrastructure/models.py, repository.py
observability/api/routes.py, schemas.py
```

## Infrastructure Reuse

| Existing Module | Files Imported |
|----------------|----------------|
| kernel/event_bus.py | 9 modules (event imports) |
| tasks/ | 2 modules (task enqueue) |
| notifications/ | 1 module (Telegram adapter) |
| shared/models/base.py | All infrastructure models |
| database.py | All repositories |
| national/base.py | All 9 modules |
| national/enums.py | All 9 modules |
| national/exceptions.py | All 9 modules |

## License

Same as GULA Platform — proprietary. All new files in `backend/app/national/`.
