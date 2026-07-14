# GULA Platform Kotlin SDK

Official Kotlin SDK for the [GULA Platform](https://github.com/samertts/gula-platform) — an Arabic-first healthcare LIMS platform for Iraqi medical laboratories.

## Features

- **Full API coverage** — Auth, Patients, Labs, Orders, Results, Samples, Claims, Consent, Edge AI, MPI, AI, Subscriptions, Admin, and more
- **JWT Bearer auth** with automatic token refresh
- **Retry with exponential backoff** (3 attempts by default)
- **Idempotency-Key support** for safe retries of mutations
- **Structured logging** via SLF4J
- **Offline sync** — queue operations when disconnected, replay when online
- **kotlinx.serialization** for all DTOs — zero-reflection JSON

## Installation

Add the dependency to your `build.gradle.kts`:

```kotlin
repositories {
    mavenCentral()
}

dependencies {
    implementation("io.gula.sdk:gula-sdk:1.0.0")
}
```

## Quick Start

```kotlin
import io.gula.sdk.GulaClient
import io.gula.sdk.GulaConfig
import io.gula.sdk.models.*

suspend fun main() {
    val client = GulaClient(GulaConfig.production())

    // Login
    val loginResp = client.login(LoginRequest(
        email = "admin@example.com",
        password = "your-password"
    ))
    println("Logged in as ${loginResp.user.name}")

    // List patients
    val patients = client.listPatients(limit = 10)
    println("Found ${patients.total} patients")

    // Create an order
    val order = client.createOrder(CreateOrderRequest(
        patientId = 1,
        doctorName = "د. أحمد",
        results = listOf(
            ResultItem(
                testName = "CBC",
                value = 5.2,
                unit = "x10^9/L",
                normalRangeLow = 4.0,
                normalRangeHigh = 11.0,
            )
        )
    ))
    println("Order #${order.id} created")

    client.close()
}
```

## Configuration

```kotlin
// Production
val client = GulaClient(GulaConfig.production())

// Staging
val client = GulaClient(GulaConfig.staging())

// Local development
val client = GulaClient(GulaConfig.local())

// Custom
val client = GulaClient(GulaConfig(
    baseUrl = "https://custom.instance.com",
    maxRetries = 5,
    requestTimeoutMs = 60_000L,
    idempotencyKey = "my-idem-key",
))
```

## Authentication

```kotlin
// Login sets tokens automatically
val resp = client.login(LoginRequest("user@lab.com", "password"))

// Or set tokens directly (e.g. from saved session)
client.setTokens("eyJhbG...", "refresh-token-here")

// Clear on logout
client.logout()
// Or manually:
client.clearTokens()
```

## Offline Sync

The offline sync module queues write operations when the network is unavailable and replays them when connectivity is restored.

```kotlin
import io.gula.sdk.sync.OfflineSync

val offSync = OfflineSync(client)
offSync.startAutoSync()  // Replays every 30s

// Queue operations while offline:
offSync.enqueueCreatePatient(PatientCreate(
    fullName = "Ali",
    phone = "07701234567",
))

// Manual flush when ready:
offSync.syncNow()

// Check queue depth:
println("Pending: ${offSync.getQueueDepth()}")

offSync.stopAutoSync()
```

## Idempotency

Set an `Idempotency-Key` header to make mutation requests safe for retry. The server deduplicates based on this key — if the same key is sent again for the same resource, the original response is returned and no duplicate is created.

```kotlin
val client = GulaClient(GulaConfig(
    baseUrl = "https://api.gulaplatform.com",
    idempotencyKey = UUID.randomUUID().toString(),
))
```

## Error Handling

```kotlin
try {
    val patient = client.getPatient(999)
} catch (e: io.gula.sdk.GulaNotFoundException) {
    println("Patient not found: ${e.resourceType}")
} catch (e: io.gula.sdk.GulaAuthException) {
    println("Auth failed, re-login required")
} catch (e: io.gula.sdk.GulaRateLimitException) {
    println("Rate limited, retry after ${e.retryAfterSeconds}s")
} catch (e: io.gula.sdk.GulaValidationException) {
    println("Validation errors: ${e.errors}")
} catch (e: io.gula.sdk.GulaNetworkException) {
    println("Network error, check connectivity")
}
```

## Exception Hierarchy

```
GulaException
├── GulaAuthException
│   ├── GulaTokenExpiredException
│   └── GulaRefreshFailedException
├── GulaNotFoundException
├── GulaConflictException
│   └── GulaIdempotencyConflictException
├── GulaValidationException
├── GulaRateLimitException
├── GulaPermissionException
├── GulaFeatureNotAvailableException
├── GulaSubscriptionLimitException
├── GulaLockedException
├── GulaNetworkException
└── GulaServerException
```

## API Coverage

| Domain | Methods |
|--------|---------|
| Auth | login, citizenLogin, logout, changePassword, refreshToken |
| Patients | list, create, get, update, getFamilyMembers, getPatientChildren |
| Patient Card | generate, scan |
| Labs | getMyLab, updateMyLab, listEmployees, createEmployee, updateEmployee |
| Orders | create, list, get, validate, cancel, batchCreate |
| Results | getPublicResult, getPatientHistory, analyze, submitDeviceResult |
| Samples | create, list, get, update |
| Consent | grant, revoke, check |
| Claims | create, get, validate, submit |
| Edge | registerDevice, listDevices, getDevice, quarantine, revoke, reinstate, killSwitch, tasks, policy, fleet, models |
| AI | suggest, pending, approve, reject, execute, analyzeOrder, interpret, chat |
| Subscription | listTiers, getMySubscription, requestUpgrade, listUpgradeRequests, upgradeDemand, admin |
| Admin | listLabs, createLab, listUsers, createUser, changeUserRole, killSwitch |
| Dashboard | getDashboardStats |
| Identity | verifyNationalId, linkIdentity |
| MPI | checkDuplicates, match, merge |
| Mobile | registerDeviceToken |
| Registration | registerLab, registerCitizen, registerStaff, registerDoctor |
| Health | healthCheck, healthReady, healthDeep |

## Requirements

- Kotlin 1.9+
- JVM 17+
- Kotlinx Serialization 1.6+
- Ktor Client 2.3+

## License

MIT
