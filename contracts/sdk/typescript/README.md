# @gula-platform/sdk

TypeScript SDK for the **GULA Medical Laboratory Platform** — an Arabic-first healthcare LIMS serving Iraqi medical laboratories.

## Installation

```bash
npm install @gula-platform/sdk
```

## Quick Start

```typescript
import { GulaClient, GulaPlatform } from '@gula-platform/sdk';

const client = new GulaClient({
  baseURL: 'https://api.gula-platform.org/api/v1',
  accessToken: '<your-jwt-token>',
  timeout: 30_000,
  maxRetries: 3,
  enableLogging: false,
});

const gula = new GulaPlatform(client);

// Login
const loginResponse = await gula.auth.login({
  email: 'admin@lab.com',
  password: 'password123',
});

client.setAccessToken(loginResponse.access_token);

// List patients
const patients = await gula.patients.list({ page: 1, limit: 50 });

// Create a lab order
const order = await gula.orders.create({
  patient_id: 123,
  results: [
    { test_name: 'CBC', value: 12.5, unit: 'g/dL' },
  ],
});

// Submit a device result
const deviceResult = await gula.results.deviceSubmit({
  barcode: 'SMP001',
  results: [{ test_name: 'WBC', value: 8.2, unit: 'K/uL' }],
});
```

## Client Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `baseURL` | required | API base URL |
| `accessToken` | `undefined` | JWT access token |
| `refreshToken` | `undefined` | Refresh token |
| `timeout` | `30000` | Request timeout (ms) |
| `maxRetries` | `3` | Max retries on 429/5xx |
| `enableLogging` | `false` | Log requests/responses |
| `onTokenRefresh` | `undefined` | Async callback for silent token refresh |
| `idempotencyKeyProvider` | `undefined` | Function returning an idempotency key |

### Idempotency-Key Header

The client automatically attaches an `Idempotency-Key` header to all POST/PUT/PATCH/DELETE
requests when you provide an `idempotencyKeyProvider` function:

```typescript
const client = new GulaClient({
  baseURL: '...',
  idempotencyKeyProvider: () => crypto.randomUUID(),
});
```

### Silent Token Refresh

```typescript
const client = new GulaClient({
  baseURL: '...',
  accessToken: '...',
  refreshToken: '...',
  onTokenRefresh: async () => {
    const res = await fetch('/auth/refresh', { ... });
    const data = await res.json();
    return data.access_token;
  },
});
```

## API Modules

| Module | Description |
|--------|-------------|
| `gula.auth` | Login, register, password management |
| `gula.patients` | CRUD, search, QR card scan, bulk assign |
| `gula.labs` | Lab profile, employees, departments, work hours, holidays, logo |
| `gula.orders` | Lab orders, batch orders, clinical analysis |
| `gula.results` | Test results, device results, PDF export, amendments, verification |
| `gula.samples` | Sample registration, barcode, transfer, timeline |
| `gula.admin` | User/lab management, KPI stats, system config, kill switch |
| `gula.compliance` | Compliance records, regulations, reports, auditing |
| `gula.claims` | Insurance claims CRUD, submit, approve, reject |
| `gula.consent` | Grant/revoke/check data-sharing consent |
| `gula.edge` | Edge device registration, task scheduling, fleet management, models |
| `gula.mpi` | Master Patient Index — resolve, merge, review |
| `gula.notifications` | In-app, WhatsApp, SMS notifications |
| `gula.qualityControl` | QC submissions, Westgard rules, Levey-Jennings charts |
| `gula.ai` | AI analysis, chat, telemetry logging, feedback |
| `gula.stats` | Dashboards, trends, demographics, revenue, export |
| `gula.governance` | Governance hierarchy, delegations, workforce registry |
| `gula.lims` | LIMS-specific: specimens, instruments, inventory, QC programs |
| `gula.fhir` | FHIR R4 resources (Patient, Observation, DiagnosticReport, etc.) |

## Types

Every API response and request body has a dedicated TypeScript interface exported
from the package:

```typescript
import {
  PatientCreate,
  LoginResponse,
  CreateOrderRequest,
  TestResultRead,
  PaginationMeta,
  ListResponse,
} from '@gula-platform/sdk';
```

Full type reference: `src/types.ts` (77+ schemas across 17 domains).

## Enums

```typescript
import {
  LabTypes,        // PRIVATE | GOVERNMENT | HOSPITAL | CLINIC
  ResultStatus,    // PENDING | COMPLETED | VERIFIED | REJECTED
  SampleStatus,    // COLLECTED | RECEIVED | PROCESSING | ANALYZED | REJECTED
  ClaimStatus,     // DRAFT | VALIDATED | SUBMITTED | APPROVED | REJECTED
  SubscriptionTier,// STARTER | GROWTH | ENTERPRISE
  OrderPriority,   // ROUTINE | URGENT | STAT
  GenderValues,    // MALE | FEMALE | M | F
  // ... 25+ enum types
} from '@gula-platform/sdk';
```

Each enum is provided as both a `const` object and a TypeScript type (e.g. `LabType`,
`ResultStatus`).

## Error Handling

```typescript
import {
  GulaError,
  AuthenticationError,
  NotFoundError,
  ValidationError,
  RateLimitError,
} from '@gula-platform/sdk';

try {
  await gula.patients.get(99999);
} catch (error) {
  if (error instanceof NotFoundError) {
    console.error('Patient not found:', error.statusCode);
  } else if (error instanceof ValidationError) {
    console.error('Validation errors:', error.errors);
  } else if (error instanceof RateLimitError) {
    console.error('Rate limited. Retry after:', error.retryAfter, 's');
  } else if (error instanceof GulaError) {
    console.error('GULA API error:', error.code, error.message);
  }
}
```

| Error Class | HTTP Status | Code |
|-------------|-------------|------|
| `AuthenticationError` | 401 | `UNAUTHORIZED` |
| `PermissionError` | 403 | `FORBIDDEN` |
| `NotFoundError` | 404 | `NOT_FOUND` |
| `ConflictError` | 409 | `CONFLICT` |
| `ValidationError` | 422 | `VALIDATION_ERROR` |
| `RateLimitError` | 429 | `RATE_LIMITED` |
| `ServerError` | 500 | `SERVER_ERROR` |
| `GulaError` | varies | `HTTP_*` |

## Offline Sync

The SDK includes a localStorage/IndexedDB-backed mutation queue for offline scenarios:

```typescript
import { SyncEngine } from '@gula-platform/sdk';

const sync = new SyncEngine({
  maxRetries: 5,
  conflictStrategy: 'remote-wins',
  onProcess: async (mutation) => {
    await api.request({ method: mutation.method, url: mutation.url, data: mutation.data });
  },
  onComplete: (mutation) => console.log('Synced:', mutation.id),
  onError: (mutation, error) => console.error('Sync failed:', mutation.id, error),
});

// Enqueue mutations while offline
sync.enqueue({
  type: 'CREATE_ORDER',
  url: '/orders',
  method: 'POST',
  data: { patient_id: 1, results: [] },
  idempotencyKey: 'uuid-here',
});

// Check queue
console.log('Pending mutations:', sync.getQueueSize());

// Listen for online/offline events
const unsub = sync.onOnlineChange((online) => {
  console.log(online ? 'Back online — syncing...' : 'Offline mode');
});
```

The engine:
- Persists to `localStorage` by default, falls back to IndexedDB, then in-memory
- Auto-processes the queue when coming back online
- Retries with exponential backoff (1s, 2s, 4s, 8s...)
- Handles 409 (Conflict) via configurable strategy: `remote-wins`, `local-wins`, or `manual`
- Drops mutations on 401/403 (auth errors)
- Caps the queue at 1000 entries

## Pagination

All list endpoints return `ListResponse<T>` with pagination metadata:

```typescript
interface ListResponse<T> {
  items: T[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// Paginate through results
let page = 1;
let hasMore = true;

while (hasMore) {
  const response = await gula.patients.list({ page, limit: 50 });
  console.log(`Page ${page}: ${response.items.length} patients`);
  hasMore = response.pagination.has_next;
  page++;
}
```

## File Upload/Download

```typescript
// Upload lab logo
const file = fileInput.files[0];
await gula.labs.uploadLogo(1, file);

// Download patient CSV
const blob = await gula.patients.exportCsv({ lab_id: 1 });

// Download result PDF
const pdf = await gula.results.exportTestResultPdf(42);
```

## Building

```bash
npm run build     # Compile TypeScript → dist/
npm run typecheck # Type-check without emitting
npm run lint      # Lint source files
```

## TypeScript

The SDK targets ES2020 with strict type-checking enabled. See `tsconfig.json` for the
full compiler configuration.

## License

MIT
