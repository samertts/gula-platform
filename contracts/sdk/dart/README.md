# GULA SDK for Flutter

Official Dart/Flutter SDK for the [GULA Platform](https://github.com/samertts/gula-platform) — a medical laboratory information management system (LIMS) designed for Iraqi healthcare.

## Features

- **Full API coverage** — Auth, Patients, Orders, Results, Samples, QC, AI, Edge, MPI, Claims, Consent, FHIR, Subscriptions, Notifications
- **JWT Bearer auth** with automatic token refresh
- **Idempotency-Key** support for safe retries on mutations
- **Retry interceptor** — 3 automatic retries on transient failures (timeout, 5xx)
- **Offline sync** — queue mutations when offline, replay on reconnect
- **Connectivity detection** via `connectivity_plus`
- **json_serializable** models — all DTOs are fully typed Dart classes
- **Comprehensive error handling** — typed exceptions for every HTTP status code

## Installation

Add to your `pubspec.yaml`:

```yaml
dependencies:
  gula_sdk:
    path: ./contracts/sdk/dart
```

Then run:

```bash
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

## Quick Start

```dart
import 'package:gula_sdk/gula_client.dart';

final client = GulaClient(baseUrl: 'https://api.gula.iq');

// Login
final login = await client.login(
  email: 'admin@lab.iq',
  password: 'secure-password',
);

// Fetch patients
final patients = await client.getPatients(labId: login.user.labId);

// Create an order
final order = await client.createOrder(OrderCreateRequest(
  patientId: patients.first.id,
  labId: login.user.labId!,
));

// Enable offline sync
final client = GulaClient(
  baseUrl: 'https://api.gula.iq',
  enableOfflineSync: true,
);
```

## Client Configuration

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `baseUrl` | `String` | — | GULA API base URL (required) |
| `token` | `String?` | `null` | Existing JWT token |
| `refreshToken` | `String?` | `null` | Existing refresh token |
| `dio` | `Dio?` | `null` | Custom Dio instance |
| `enableOfflineSync` | `bool` | `false` | Enable offline queue |

### Token Management

```dart
// Set after login
client.setTokens(token: jwt, refreshToken: refresh);

// Update token after refresh
client.setToken(newJwt);

// Clear on logout
client.clearToken();
```

## API Methods

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `login(email, password)` | `POST /login` | Authenticate user |
| `logout()` | `POST /logout` | Revoke session |
| `register(request)` | `POST /register` | Register new user |
| `refreshToken(refreshToken)` | `POST /auth/refresh` | Refresh JWT |

### Labs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `getMyLab()` | `GET /labs/me` | Current user's lab |
| `updateLab(id, request)` | `PUT /labs/:id` | Update lab settings |
| `getLabUsers(labId)` | `GET /labs/:id/users` | List lab staff |
| `createStaff(request)` | `POST /register/staff` | Create staff account |

### Patients

| Method | Endpoint | Description |
|--------|----------|-------------|
| `getPatients(labId, search, page, perPage)` | `GET /patients` | List/search patients |
| `getPatient(id)` | `GET /patients/:id` | Get patient details |
| `createPatient(request)` | `POST /patients` | Register new patient |
| `updatePatient(id, request)` | `PUT /patients/:id` | Update patient |
| `getFamily(familyId)` | `GET /patients/family/:id` | Get family members |
| `getPatientChildren(id)` | `GET /patients/:id/children` | Get dependents |

### Patient Card (QR)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `getPatientCard(patientId)` | `GET /patient-card/:id` | Get card data |
| `getPatientCardQr(patientId)` | `GET /patient-card/:id/qr.png` | Download QR PNG |
| `scanPatientCard(token)` | `POST /patient-card/scan` | Scan QR token |
| `getPatientHistory(patientId)` | `GET /patient-card/:id/history` | Full history |

### Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| `getOrders(labId, patientId, status, page, perPage)` | `GET /results/orders` | List orders |
| `getOrder(id)` | `GET /results/orders/:id` | Get order detail |
| `createOrder(request)` | `POST /results/orders` | Create order |
| `batchCreateOrders(request)` | `POST /batch/orders` | Batch create orders |
| `validateOrder(id, request)` | `POST /results/orders/:id/validate` | Validate with version |
| `cancelOrder(id)` | `POST /results/orders/:id/cancel` | Cancel order |

### Results

| Method | Endpoint | Description |
|--------|----------|-------------|
| `createResult(request)` | `POST /device-results/results` | Add result |
| `getResultByToken(token)` | `GET /results/r/:token` | Lookup by token |
| `getResultPdf(token)` | `GET /results/r/:token/pdf` | Download PDF |
| `getTestProfiles()` | `GET /results/test-profiles` | Available test types |
| `createTestResult(payload)` | `POST /test-results` | CMD-008 test result |

### Analytics & AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| `analyzeOrder(orderId)` | `POST /results/analyze` | Clinical interpretation |
| `getOrderIntelligence(orderId)` | `GET /results/orders/:id/intelligence` | Full AI analysis |
| `getAiSuggestion(request)` | `POST /ai/suggest` | Get AI suggestion |
| `getAiPendingApprovals()` | `GET /ai/pending` | Pending approvals |
| `approveAiSuggestion(id)` | `POST /ai/approve/:id` | Approve suggestion |
| `rejectAiSuggestion(id)` | `POST /ai/reject/:id` | Reject suggestion |
| `getCriticalAlerts()` | `GET /ai/critical-alerts` | Critical results |

### Consent

| Method | Endpoint | Description |
|--------|----------|-------------|
| `grantConsent(request)` | `POST /consent/grant` | Grant consent |
| `revokeConsent(request)` | `POST /consent/revoke` | Revoke consent |
| `checkConsent(request)` | `GET /consent/check` | Check consent |

### Claims

| Method | Endpoint | Description |
|--------|----------|-------------|
| `createClaim(request)` | `POST /claims` | Create claim |
| `getClaim(id)` | `GET /claims/:id` | Get claim |
| `getClaims(labId, patientId, status, page, perPage)` | `GET /claims` | List claims |

### Edge Platform

| Method | Endpoint | Description |
|--------|----------|-------------|
| `getEdgeDevices()` | `GET /edge/devices` | List devices |
| `getEdgeDevice(deviceId)` | `GET /edge/devices/:id` | Device detail |
| `quarantineEdgeDevice(deviceId)` | `POST /edge/devices/:id/quarantine` | Quarantine |
| `revokeEdgeDevice(deviceId)` | `POST /edge/devices/:id/revoke` | Revoke |
| `reinstateEdgeDevice(deviceId)` | `POST /edge/devices/:id/reinstate` | Reinstate |
| `toggleEdgeKillSwitch(deviceId)` | `POST /edge/devices/:id/kill_switch` | Kill switch |
| `createEdgeTask(request)` | `POST /edge/tasks` | Create task |
| `getEdgeTasks()` | `GET /edge/tasks` | List tasks |
| `getEdgeTask(taskUid)` | `GET /edge/tasks/:uid` | Task detail |
| `cancelEdgeTask(taskUid)` | `POST /edge/tasks/:uid/cancel` | Cancel task |
| `getEdgePolicy()` | `GET /edge/policy` | Get policy |
| `updateEdgePolicy(policy)` | `PUT /edge/policy` | Update policy |
| `getEdgeFleetSummary()` | `GET /edge/fleet/summary` | Fleet summary |
| `createEdgeModel(payload)` | `POST /edge/models` | Register model |
| `getEdgeModels()` | `GET /edge/models` | List models |
| `updateEdgeModelStatus(modelUid, status)` | `POST /edge/models/:uid/status` | Update status |
| `assignEdgeModel(modelUid, assignment)` | `POST /edge/models/:uid/assign` | Assign to device |
| `agentHeartbeat(request)` | `POST /edge/agent/heartbeat` | Agent heartbeat |
| `agentSubmitResult(taskUid, result)` | `POST /edge/agent/tasks/:uid/result` | Submit result |
| `agentSubmitTelemetry(telemetry)` | `POST /edge/agent/telemetry` | Submit telemetry |

### MPI (Master Patient Index)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `resolveIdentity(request)` | `POST /mpi/resolve` | Resolve patient identity |
| `getCitizen(citizenUlid)` | `GET /mpi/citizens/:ulid` | Get citizen record |
| `mergeIdentities(request)` | `POST /mpi/merge` | Merge duplicate identities |
| `getPendingReviews()` | `GET /mpi/review/pending` | Pending reviews |
| `decideReview(claimId, decision)` | `POST /mpi/review/:id/decide` | Adjudicate |

### Quality Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `createQcRecord(request)` | `POST /quality-control` | Create QC record |
| `getQcRecords(labId, testCode)` | `GET /quality-control` | List QC records |
| `getQcStatistics(labId, testCode)` | `GET /quality-control/statistics` | QC statistics |
| `getLeveyJenningsChart(labId, testCode, days)` | `GET /quality-control/levey-jennings` | LJ chart data |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| `sendNotification(request)` | `POST /notifications/send` | Send notification |
| `getNotificationHistory(orderId)` | `GET /notifications/history/:id` | History |

### Subscriptions / Tiers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `getTierMatrix()` | `GET /tiers` | Available tiers |
| `getMySubscription()` | `GET /tiers/my` | Current subscription |
| `requestUpgrade(request)` | `POST /tiers/upgrade` | Request upgrade |
| `getFeatureFlags(labId)` | `GET /tiers/flags` | Feature flags |

### Dashboard & Stats

| Method | Endpoint | Description |
|--------|----------|-------------|
| `getDashboard()` | `GET /dashboard` | Dashboard summary |
| `getStats(labId, from, to)` | `GET /stats` | Statistics |

### Compliance & FHIR

| Method | Endpoint | Description |
|--------|----------|-------------|
| `getComplianceInfo()` | `GET /compliance/info` | Compliance info |
| `getSecurityReport()` | `GET /compliance/security-report` | Security report |
| `getAuditSummary()` | `GET /compliance/audit-summary` | Audit log |
| `getFhirPatient(patientId)` | `GET /compliance/fhir/patient/:id` | FHIR Patient |
| `getFhirDiagnosticReport(orderId)` | `GET /compliance/fhir/diagnostic-report/:id` | FHIR DiagnosticReport |

### National Identity

| Method | Endpoint | Description |
|--------|----------|-------------|
| `verifyNationalId(nationalId)` | `POST /national-id/verify` | Verify NID |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `getIntegrationStatuses()` | `GET /integrations/status` | Integration statuses |
| `probeIntegration(name)` | `POST /integrations/:name/probe` | Probe integration |
| `health()` | `GET /health` | Health check |
| `healthDeep()` | `GET /health/deep` | Deep health |

## Offline Sync

Enable with `enableOfflineSync: true`:

```dart
final client = GulaClient(
  baseUrl: 'https://api.gula.iq',
  enableOfflineSync: true,
);

// Monitor connectivity
client.isOnline.addListener(() {
  if (client.isOnline.value) {
    print('Back online — processing queue');
  }
});

// Get sync status
client.offlineSync.syncStatus.addListener(() {
  print('Sync status: ${client.offlineSync.syncStatus.value}');
});

// Manual retry of failed entries
await client.offlineSync.retryFailed();

// Clear queue
await client.offlineSync.clearAll();
```

The offline queue uses `SharedPreferences` for persistence with a max of 1000 entries. Failed entries are retried up to 5 times then marked as failed.

## Error Handling

```dart
try {
  final order = await client.getOrder(999);
} on GulaAuthException catch (e) {
  // Redirect to login
} on GulaNotFoundException catch (e) {
  // Handle 404
} on GulaConflictException catch (e) {
  // Handle 409 (optimistic locking)
} on GulaLockedException catch (e) {
  // Handle 423 (validated orders)
} on GulaValidationException catch (e) {
  // Handle 422 (field-level errors)
  for (final error in e.errors) {
    print('${error.loc}: ${error.msg}');
  }
} on GulaRateLimitException catch (e) {
  // Back off
} on GulaNetworkException catch (e) {
  // Queue for offline
} on GulaException catch (e) {
  // Generic
}
```

### Exception Hierarchy

| Exception | Status | When |
|-----------|--------|------|
| `GulaAuthException` | 401 | Invalid/missing token |
| `GulaUnauthorizedException` | 403 | Insufficient permissions |
| `GulaNotFoundException` | 404 | Resource not found |
| `GulaConflictException` | 409 | Version conflict / state conflict |
| `GulaLockedException` | 423 | Validated order is immutable |
| `GulaValidationException` | 422 | Field validation errors |
| `GulaRateLimitException` | 429 | Too many requests |
| `GulaServerException` | 500+ | Server error |
| `GulaNetworkException` | — | Connectivity error |
| `GulaOfflineException` | — | Device offline |
| `GulaException` | any | Fallback |

## Models

All DTOs are in `lib/src/models/` and use `json_serializable`. Run `build_runner` to generate `.g.dart` files:

```bash
flutter pub run build_runner build
```

### Available Models

- **auth.dart** — `LoginRequest`, `LoginResponse`, `LoginUser`, `RegisterRequest`, `RefreshTokenRequest`, `RefreshTokenResponse`
- **patient.dart** — `Patient`, `PatientCreateRequest`, `PatientUpdateRequest`, `PatientCardResponse`
- **lab.dart** — `Lab`, `LabUpdateRequest`, `LabUser`, `StaffCreateRequest`
- **order.dart** — `LabOrder`, `OrderCreateRequest`, `BatchOrderRequest`, `OrderValidateRequest`
- **result.dart** — `LabResult`, `ResultCreateRequest`, `TestType`, `TestResult`
- **sample.dart** — `Sample`
- **consent.dart** — `Consent`, `ConsentGrantRequest`, `GrantResponse`, `RevokeRequest`, `RevokeResponse`, `CheckRequest`, `CheckResponse`
- **claim.dart** — `Claim`, `ClaimItem`, `ClaimCreateRequest`, `ClaimItemCreateRequest`
- **edge.dart** — `EdgeDevice`, `EdgeDeviceSummary`, `EdgeDeviceDetail`, `EdgeTask`, `EdgeTaskCreateRequest`, `EdgeTaskSummary`, `EdgeTelemetry`, `EdgeModel`, `EdgePolicy`, `FleetSummary`, `EdgeEvent`, `HeartbeatRequest`, `HeartbeatResponse`
- **mpi.dart** — `MpiResolveRequest`, `MpiResolveResponse`, `CitizenResponse`, `MpiMergeRequest`, `MpiMergeResponse`, `PendingReviewItem`, `PendingReviewPage`, `ResolveDecision`
- **ai.dart** — `AiSuggestionRequest`, `AiSuggestionResponse`, `AiPendingApproval`, `AiInteraction`, `AiRetrievalRef`, `AiFeedback`, `AiCriticalAlert`, `OrderIntelligence`, `AnalyzeRequest`, `AnalyzeResponse`
- **lims.dart** — `DashboardResponse`, `StatsResponse`, `AuditLogEntry`, `Organization`, `Facility`, `Appointment`, `CriticalAlert`, `DeviceResultPayload`, `IntegrationStatus`
- **governance.dart** — `GovernanceNode`, `Delegation`, `ComplianceReport`, `SecurityReport`, `PolicyDocument`, `License`
- **fhir.dart** — `FhirPatient`, `FhirHumanName`, `FhirObservation`, `FhirQuantity`, `FhirCodeableConcept`, `FhirCoding`, `FhirReferenceRange`, `FhirSimpleQuantity`, `FhirDiagnosticReport`, `FhirServiceRequest`
- **subscription.dart** — `LabSubscription`, `TierMatrix`, `UpgradeRequest`, `UpgradeDemandScore`, `FeatureFlag`, `TierUpgradeRequest`
- **notification.dart** — `NotificationSendRequest`, `NotificationSendResponse`, `NotificationHistoryItem`
- **qc.dart** — `QualityControl`, `QcCreateRequest`, `QcStatistics`, `LeveyJenningsPoint`

## Enums

All enums are in `lib/src/enums.dart`:

| Enum | Values |
|------|--------|
| `Gender` | `m`, `f` |
| `LabType` | `private`, `government`, `hospital`, `clinic` |
| `OrderStatus` | `pending`, `completed`, `validated`, `cancelled` |
| `ResultFlag` | `h`, `l`, `normal`, `critical` |
| `SampleStatus` | `collected`, `received`, `processing`, `analyzed`, `rejected` |
| `SampleType` | `blood`, `urine`, `stool`, `swab`, `serum`, `plasma` |
| `ClaimStatus` | `draft`, `validated`, `submitted`, `accepted`, `rejected`, `paid` |
| `ConsentStatus` | `active`, `revoked`, `expired`, `pending`, `enteredInError` |
| `EdgeDeviceStatus` | `pending`, `active`, `quarantined`, `revoked`, `offline` |
| `EdgeTaskStatus` | `pending`, `dispatched`, `running`, `completed`, `failed`, `cancelled`, `expired` |
| `EdgeModelStatus` | `draft`, `canary`, `active`, `retired`, `blocked` |
| `QcStatus` | `pass`, `warning`, `fail` |
| `WestgardRule` | `one2s`, `one3s`, `two2s`, `r4s`, `four1s`, `tenX` |
| `UserRole` | `masterAdmin`, `labAdmin`, `labStaff`, `doctor`, `citizen` |
| `SubscriptionTier` | `starter`, `growth`, `enterprise` |
| `DeploymentMode` | `single`, `multiBranch`, `government` |
| `SecurityLevel` | `standard`, `highSecurity`, `airGapped` |
| `BillingCycle` | `monthly`, `yearly` |
| + full national enum set (IdentityType, IdentityStatus, GovernanceNodeType, InteropProtocolType, etc.) |

## Development

### Generate Code

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

### Run Tests

```bash
flutter test
```

## Architecture

```
lib/
├── gula_client.dart          # Main HTTP client with all API methods
├── src/
│   ├── enums.dart            # All enumerations
│   ├── exceptions.dart       # Typed exception hierarchy
│   ├── models/               # Data transfer objects (json_serializable)
│   │   ├── auth.dart
│   │   ├── patient.dart
│   │   ├── lab.dart
│   │   ├── order.dart
│   │   ├── result.dart
│   │   ├── sample.dart
│   │   ├── consent.dart
│   │   ├── claim.dart
│   │   ├── edge.dart
│   │   ├── mpi.dart
│   │   ├── ai.dart
│   │   ├── lims.dart
│   │   ├── governance.dart
│   │   ├── fhir.dart
│   │   ├── subscription.dart
│   │   ├── notification.dart
│   │   └── qc.dart
│   └── sync/
│       └── offline_sync.dart # Offline queue + connectivity
```

## License

This SDK is part of the GULA Platform. See the repository license.
