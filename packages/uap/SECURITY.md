# UAP Security Guide

## Authentication
- Use `useAuth` from `@gula/uap/runtime` for all auth
- Session tokens stored in localStorage (encrypted in production)
- Role-based access control via permissions array
- Biometric authentication via WebAuthn API

## Data Protection
- Offline database encrypted with XOR cipher (key from app config)
- All API calls go through the config's `apiUrl`
- Telemetry privacy mode enabled by default (PII not collected)

## Best Practices
1. Never store secrets in the offline DB encryption key
2. Always check `hasPermission` before rendering protected UI
3. Use `ErrorBoundary` at every route segment
4. Enable `privacyMode` in telemetry for production
5. Validate all user input with Zod schemas

## Audit
- All auth mutations logged to telemetry events
- Device registry tracks all connected device actions
- Sync queue provides full operation history
