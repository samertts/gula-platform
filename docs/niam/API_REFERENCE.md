# NIAM — API Reference

Base URL: `/niam`

All routes are mounted under the `identity_router` with prefix `/niam` and available at both development and production API gateways.

---

## Health

### GET /niam/health

NIAM domain health check. Returns domain status and version.

**Response:**
```json
{
  "status": "healthy",
  "domain": "niam",
  "version": "1.0.0"
}
```

---

## Persons

### POST /niam/persons/

Create a new person record.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `given_name` | string | yes | — | First name |
| `family_name` | string | yes | — | Family name |
| `middle_name` | string | no | null | Middle name |
| `full_name_ar` | string | no | null | Full name in Arabic |
| `gender` | string | no | null | Gender |
| `birth_date` | date | no | null | Date of birth (ISO 8601) |
| `nationality` | string | no | "IRQ" | ISO 3166-1 alpha-3 |
| `email` | string | no | null | Email address |
| `phone` | string | no | null | Phone number |
| `national_id_hash` | string | no | null | HMAC-SHA256 of National ID |
| `health_id` | string | no | null | SNDHS health identifier |

**Response (201):**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "id": "01ARZ3NDEKTSV4RRFFQ69G5FAV"
}
```

### GET /niam/persons/{person_uuid}

Retrieve a person by UUID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `person_uuid` | string | yes | Person UUID |

**Response (200):**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "given_name": "Ali",
  "family_name": "Al-Mansour"
}
```

**Response (404):**
```json
{
  "error": "not_found"
}
```

---

## Accounts

### POST /niam/accounts/

Create a new account linked to an identity.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `identity_id` | string | yes | — | Identity record ID (ULID) |
| `account_type` | string | no | "human" | human, machine, service, system |
| `email` | string | no | null | Email (must be unique if provided) |
| `phone` | string | no | null | Phone (must be unique if provided) |
| `username` | string | no | null | Username (must be unique if provided) |
| `password` | string | no | null | Password (will be bcrypt-hashed) |

**Response (201):**
```json
{
  "uuid": "660e8400-e29b-41d4-a716-446655440001",
  "id": "01ARZ3NDEKTSV4RRFFQ69G5FAW"
}
```

### POST /niam/accounts/{account_uuid}/lock

Lock an account.

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account_uuid` | string | yes | Account UUID |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `reason` | string | no | "manual" | Lock reason |

**Response (200):**
```json
{
  "success": true
}
```

### POST /niam/accounts/{account_uuid}/unlock

Unlock an account. Resets `failed_login_attempts` to 0.

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account_uuid` | string | yes | Account UUID |

**Response (200):**
```json
{
  "success": true
}
```

---

## Authentication

### POST /niam/auth/login

Authenticate with email/username and password.

**Request Body:**
```json
{
  "login": "user@example.com",
  "password": "securePassword123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "session_uuid": "a1b2c3d4-...",
  "account_uuid": "e5f6g7h8-..."
}
```

**Response (401):**
```json
{
  "detail": "Invalid credentials"
}
```

### POST /niam/auth/refresh

Refresh an expired access token using a valid refresh token.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `refresh_token` | string | yes | Refresh token JWT string |

**Response (200):**
Same format as login response (new tokens, new session).

**Response (401):**
```json
{
  "detail": "Invalid or expired refresh token"
}
```

### POST /niam/auth/logout

Terminate a session.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `session_uuid` | string | yes | Session UUID to terminate |

**Response (200):**
```json
{
  "success": true
}
```

---

## Sessions

### GET /niam/sessions/account/{account_uuid}

List all sessions for an account.

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account_uuid` | string | yes | Account UUID |

**Response (200):**
```json
{
  "sessions": [
    {
      "uuid": "...",
      "session_type": "web",
      "is_active": true,
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "started_at": "2026-01-15T10:00:00Z",
      "last_activity_at": "2026-01-15T10:30:00Z",
      "expires_at": "2026-01-22T10:00:00Z"
    }
  ]
}
```

### POST /niam/sessions/{session_uuid}/terminate

Terminate a specific session.

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `session_uuid` | string | yes | Session UUID |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `reason` | string | no | "manual" | Termination reason |

**Response (200):**
```json
{
  "success": true
}
```

### POST /niam/sessions/account/{account_uuid}/terminate-all

Terminate all active sessions for an account.

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account_uuid` | string | yes | Account UUID |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `reason` | string | no | "manual" | Termination reason |

**Response (200):**
```json
{
  "success": true
}
```

---

## Devices

### POST /niam/devices/register

Register a device for a person. If a device with the same fingerprint exists, it updates the existing record.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `person_uuid` | string | yes | — | Person UUID |
| `device_fingerprint` | string | yes | — | Unique device fingerprint |
| `device_name` | string | no | null | Human-readable device name |
| `device_type` | string | no | null | desktop, mobile, tablet, server |
| `ip_address` | string | no | null | Client IP address |

**Response (201):**
```json
{
  "uuid": "770e8400-e29b-41d4-a716-446655440002",
  "id": "01ARZ3NDEKTSV4RRFFQ69G5FAX"
}
```

### POST /niam/devices/{device_uuid}/trust

Mark a device as trusted.

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `device_uuid` | string | yes | Device UUID |

**Response (200):**
```json
{
  "success": true
}
```

### POST /niam/devices/{device_uuid}/revoke

Revoke a device (deactivate).

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `device_uuid` | string | yes | Device UUID |

**Response (200):**
```json
{
  "success": true
}
```

---

## Error Codes

| HTTP Status | Meaning | Typical Cause |
|---|---|---|
| 200 | Success | Request completed |
| 201 | Created | Resource created |
| 400 | Bad Request | Missing required parameters |
| 401 | Unauthorized | Invalid credentials, expired token |
| 403 | Forbidden | Valid auth but insufficient permissions |
| 404 | Not Found | Resource UUID not found |
| 409 | Conflict | Duplicate unique field (email, username) |
| 422 | Validation Error | Invalid parameter format |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side failure |

---

## Common Patterns

### Authentication Header

All authenticated requests must include the access token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### ULID Format

Primary key IDs are 26-character uppercase hex strings:

```
01ARZ3NDEKTSV4RRFFQ69G5FAV
```

### UUID Format

Model UUIDs are standard UUID v4:

```
550e8400-e29b-41d4-a716-446655440000
```

### Date Format

All dates use ISO 8601:

```
2026-01-15
```

### DateTime Format

All timestamps use ISO 8601 with timezone:

```
2026-01-15T10:30:00Z
```
