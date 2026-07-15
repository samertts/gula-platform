# GULA Platform — Zero-Downtime Upgrade Procedures

## Overview
Zero-downtime upgrades ensure the platform remains available during deployments,
database migrations, and configuration changes.

## 1. Rolling Update Strategy

### Backend Deployment
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### Procedure
1. Deploy new version alongside existing (maxSurge: 1)
2. New pod starts and passes health checks
3. Old pod is terminated gracefully (SIGTERM + 15s drain)
4. Repeat until all pods are updated

### PreStop Hook
All containers must implement a preStop hook:
```yaml
lifecycle:
  preStop:
    exec:
      command: ["sh", "-c", "sleep 15"]
```
This allows in-flight requests to complete before termination.

## 2. Database Migration During Rolling Update

### Safe Migration Patterns
- **Add column**: ALTER TABLE ... ADD COLUMN (nullable or with DEFAULT)
- **Add index**: CREATE INDEX CONCURRENTLY (non-blocking)
- **Remove column**: Defer removal to next release (dual-read)
- **Rename column**: Add new column → dual-write → migrate → remove old

### Procedure
1. Run migration (non-blocking operations only)
2. Migrations run in a separate job before deploy
3. Old pods continue working with backward-compatible schema
4. New pods use new schema features
5. After all pods updated, run cleanup migration

### Rollback
```bash
alembic downgrade -1
```

## 3. Blue-Green Deployment

### Procedure
1. Deploy to inactive slot (green if blue is active)
2. Run smoke tests against green slot
3. Switch traffic: update service selector to green
4. Monitor for 5 minutes
5. If healthy, keep green; if not, switch back to blue

### Rollback
```bash
kubectl patch svc gula-backend-active -p '{"spec":{"selector":{"slot":"blue"}}}'
```

## 4. Canary Deployment

### Procedure
1. Deploy canary with 10% traffic
2. Monitor error rate and latency for 10 minutes
3. If healthy, increase to 25% for 10 minutes
4. Increase to 50% for 10 minutes
5. Promote to 100%

### Rollback
```bash
kubectl patch trafficsplit gula-backend-split -p '{"spec":{"backends":[{"service":"gula-backend-blue","weight":100},{"service":"gula-backend-green","weight":0}]}}'
```

## 5. Health Check Verification

### Between Pod Updates
```bash
# Wait for new pod to be ready
kubectl rollout status deployment/gula-backend --timeout=5m

# Verify health endpoint
curl -f http://localhost:8080/health

# Check database connectivity
curl -f http://localhost:8080/health/ready
```

## 6. Configuration Changes

### Env Var Changes
- Add new variables: safe at any time
- Remove variables: ensure no running code references them
- Change values: requires restart (rolling update)

### Feature Flags
- Use in-process toggles (feature_flags.py, sndhs_flags.py)
- Runtime toggle without restart
- Enable/disable via env var reload

## 7. Emergency Rollback

```bash
# 1. Deploy previous image tag
kubectl set image deployment/gula-backend gula-backend=ghcr.io/samertts/gula-platform/backend:previous-tag

# 2. Rollback database migration
alembic downgrade -1

# 3. Verify health
kubectl rollout status deployment/gula-backend
curl -f http://localhost:8080/health
```
