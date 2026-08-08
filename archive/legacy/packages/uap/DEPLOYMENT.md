# UAP Deployment Guide

## Prerequisites
- Node.js >= 20
- pnpm >= 8

## Build
```bash
cd packages/uap
pnpm install
pnpm build          # Outputs to dist/
```

## Integration with Existing Apps

### frontend-v2 (React 19 + Tailwind 4)
```json
// frontend-v2/package.json
{
  "dependencies": {
    "@gula/uap": "workspace:*"
  }
}
```

### client (React 18 + Tailwind 3)
```json
// client/package.json
{
  "dependencies": {
    "@gula/uap": "workspace:*"
  }
}
```

## Version Management
- Package version: 1.0.0 (frozen after mission)
- Update channel: stable/beta/canary/nightly
- Rollback supported via version compatibility check

## Quality Gates
Run before every release:
```bash
pnpm --filter @gula/uap test      # Unit tests
pnpm --filter @gula/uap lint      # Linting
pnpm --filter @gula/uap typecheck # TypeScript check
```

## Monitoring
- UAP telemetry automatically initializes on app boot
- Track metrics: `useTelemetry.getState().trackMetric()`
- Track events: `useTelemetry.getState().trackEvent()`
- Crash reports automatically captured
