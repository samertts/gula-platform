# Identity API — PROGRAM-05

Base prefix: `/niam` (mounted from `app/identity/api/router.py`).

| Endpoint | Purpose |
|---|---|
| `POST /niam/auth/login` | password login; enforces lifecycle status + session policy; returns access/refresh + session_uuid |
| `POST /niam/auth/refresh` | refresh-token rotation |
| `POST /niam/auth/logout` | terminate session (audited) |
| `GET /niam/accounts/{id}` | account record incl. lifecycle status |
| `GET /niam/sessions/account/{id}` | active sessions |
| `POST /niam/sessions/{id}/terminate` | remote logout |
| `POST /niam/adaptive-auth/enforce-session-policy` | session policy evaluation (Rule 8) |
| `POST /niam/adaptive-auth/mfa/challenge` · `/verify` | adaptive MFA challenge/verify |
| `POST /niam/persons` · `GET /niam/persons/{id}` | person registry |
| `POST /niam/devices` · trust/revoke | device management |
| `POST /niam/identities/{id}/verify` | identity verification |
| `POST /niam/licenses` · verify | professional license management |

All identity mutations are written to the immutable audit chain.
