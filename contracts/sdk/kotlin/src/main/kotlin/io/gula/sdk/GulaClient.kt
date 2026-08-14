package io.gula.sdk

import io.gula.sdk.models.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.auth.*
import io.ktor.client.plugins.auth.providers.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.plugins.logging.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.delay
import kotlinx.serialization.json.Json
import org.slf4j.LoggerFactory
import java.util.*

class GulaClient private constructor(
    private val config: GulaConfig,
) : AutoCloseable {
    private val log = LoggerFactory.getLogger(GulaClient::class.java)

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
        coerceInputValues = true
    }

    private val httpClient: HttpClient = HttpClient {
        install(ContentNegotiation) {
            json(this@GulaClient.json)
        }

        install(Logging) {
            logger = object : Logger {
                override fun log(message: String) {
                    log.debug(message)
                }
            }
            level = LogLevel.HEADERS
        }

        install(HttpTimeout) {
            requestTimeoutMillis = config.requestTimeoutMs
            connectTimeoutMillis = config.connectTimeoutMs
            socketTimeoutMillis = config.socketTimeoutMs
        }

        defaultRequest {
            url(config.baseUrl)
            contentType(ContentType.Application.Json)
            accept(ContentType.Application.Json)
            config.idempotencyKey?.let { header("Idempotency-Key", it) }
        }

        install(HttpRequestRetry) {
            maxRetries = config.maxRetries
            retryOnExceptionIf { _, cause ->
                cause is kotlinx.coroutines.TimeoutCancellationException ||
                    cause is java.net.ConnectException ||
                    cause is java.net.SocketTimeoutException
            }
            exponentialDelay()
            modifyRequest { request ->
                log.warn("Retrying request to ${request.url.build()}")
            }
        }
    }

    private var accessToken: String? = null
    private var refreshToken: String? = null
    private val tokenLock = Any()

    fun setTokens(access: String, refresh: String?) {
        synchronized(tokenLock) {
            accessToken = access
            refreshToken = refresh
        }
    }

    fun clearTokens() {
        synchronized(tokenLock) {
            accessToken = null
            refreshToken = null
        }
    }

    private suspend fun refreshAccessToken(): String? {
        val rt = synchronized(tokenLock) { refreshToken } ?: return null
        return try {
            val response = httpClient.post("${config.baseUrl}/auth/refresh") {
                setBody(RefreshRequest(refreshToken = rt))
            }
            if (response.status == HttpStatusCode.OK) {
                val body = response.body<RefreshResponse>()
                synchronized(tokenLock) {
                    accessToken = body.token
                    refreshToken = body.refreshToken
                }
                body.token
            } else {
                synchronized(tokenLock) { accessToken = null; refreshToken = null }
                null
            }
        } catch (e: Exception) {
            log.error("Token refresh failed", e)
            synchronized(tokenLock) { accessToken = null; refreshToken = null }
            null
        }
    }

    private suspend fun HttpRequestBuilder.authenticate() {
        val token = synchronized(tokenLock) { accessToken }
        if (token != null) {
            bearerAuth(token)
        }
    }

    private suspend inline fun <reified T> request(
        method: HttpMethod,
        path: String,
        body: Any? = null,
        queryParams: Map<String, String> = emptyMap(),
        retryOnAuth: Boolean = true,
    ): T {
        val fullUrl = "${config.baseUrl}$path"
        var attempt = 0
        val maxAttempts = if (retryOnAuth) 2 else 1

        while (attempt < maxAttempts) {
            try {
                val response = httpClient.request(fullUrl) {
                    this.method = method
                    authenticate()
                    if (body != null) {
                        if (body is String) setBody(body) else setBody(body)
                    }
                    queryParams.forEach { (k, v) -> parameter(k, v) }
                    config.idempotencyKey?.let { header("Idempotency-Key", it) }
                }

                when {
                    response.status == HttpStatusCode.Unauthorized && retryOnAuth -> {
                        val refreshed = refreshAccessToken()
                        if (refreshed != null) {
                            attempt++
                            continue
                        }
                        throw GulaAuthException("Unauthorized and token refresh failed")
                    }
                    response.status == HttpStatusCode.Forbidden -> {
                        throw GulaPermissionException()
                    }
                    response.status == HttpStatusCode.NotFound -> {
                        throw GulaNotFoundException("resource", message = response.bodyAsText())
                    }
                    response.status == HttpStatusCode.Conflict -> {
                        throw GulaConflictException("resource", message = response.bodyAsText())
                    }
                    response.status == HttpStatusCode.UnprocessableEntity -> {
                        throw GulaValidationException(message = response.bodyAsText())
                    }
                    response.status == HttpStatusCode.TooManyRequests -> {
                        val retryAfter = response.headers[HttpHeaders.RetryAfter]?.toIntOrNull() ?: 60
                        throw GulaRateLimitException(retryAfterSeconds = retryAfter)
                    }
                    response.status == HttpStatusCode.Locked -> {
                        throw GulaLockedException("resource", message = response.bodyAsText())
                    }
                    response.status.value == 402 -> {
                        throw GulaSubscriptionLimitException("unknown", 0, 0, message = response.bodyAsText())
                    }
                    response.status.value == 423 -> {
                        throw GulaLockedException("resource", message = response.bodyAsText())
                    }
                    !response.status.isSuccess() -> {
                        val errorBody = response.bodyAsText()
                        throw GulaServerException(
                            statusCode = response.status.value,
                            responseBody = errorBody,
                        )
                    }
                }

                return response.body<T>()
            } catch (e: GulaException) {
                throw e
            } catch (e: Exception) {
                if (attempt == maxAttempts - 1) {
                    throw GulaNetworkException("Request failed after $maxAttempts attempts", e)
                }
                attempt++
                val backoffMs = (100L shl attempt.coerceAtMost(6)) +
                    kotlin.random.Random.nextLong(0, 100)
                delay(backoffMs)
            }
        }
        throw GulaNetworkException("Request failed after $maxAttempts attempts")
    }

    // ── Auth ──────────────────────────────────────────────────────────────────

    suspend fun login(request: LoginRequest): LoginResponse {
        val resp = request<LoginResponse>(HttpMethod.Post, "/login", body = request)
        setTokens(resp.token, resp.refreshToken)
        return resp
    }

    suspend fun citizenLogin(request: CitizenLoginRequest): LoginResponse {
        val resp = request<LoginResponse>(HttpMethod.Post, "/citizen/login", body = request)
        setTokens(resp.token, resp.refreshToken)
        return resp
    }

    suspend fun logout() {
        try {
            request<LogoutResponse>(HttpMethod.Post, "/logout")
        } finally {
            clearTokens()
        }
    }

    suspend fun changePassword(request: ChangePasswordRequest): Map<String, String> =
        request(HttpMethod.Post, "/auth/change-password", body = request)

    suspend fun refreshToken(): RefreshResponse? {
        val rt = synchronized(tokenLock) { refreshToken } ?: return null
        val resp = request<RefreshResponse>(HttpMethod.Post, "/auth/refresh", body = RefreshRequest(refreshToken = rt), retryOnAuth = false)
        setTokens(resp.token, resp.refreshToken)
        return resp
    }

    // ── Patients ──────────────────────────────────────────────────────────────

    suspend fun listPatients(
        search: String? = null,
        skip: Int = 0,
        limit: Int = 50,
    ): PatientListResponse {
        val params = mutableMapOf("skip" to skip.toString(), "limit" to limit.toString())
        search?.let { params["search"] = it }
        return request(HttpMethod.Get, "/patients", queryParams = params)
    }

    suspend fun createPatient(request: PatientCreate): PatientResponse =
        request(HttpMethod.Post, "/patients", body = request)

    suspend fun getPatient(patientId: Int): PatientResponse =
        request(HttpMethod.Get, "/patients/$patientId")

    suspend fun updatePatient(patientId: Int, request: PatientUpdate): PatientResponse =
        request(HttpMethod.Put, "/patients/$patientId", body = request)

    suspend fun getFamilyMembers(familyId: String): List<PatientResponse> =
        request(HttpMethod.Get, "/patients/family/$familyId")

    suspend fun getPatientChildren(patientId: Int): List<PatientResponse> =
        request(HttpMethod.Get, "/patients/$patientId/children")

    // ── Patient Card ──────────────────────────────────────────────────────────

    suspend fun generatePatientCard(patientId: Int): PatientCardResponse =
        request(HttpMethod.Post, "/patient-card/generate/$patientId")

    suspend fun scanPatientCard(token: String): ScanResponse =
        request(HttpMethod.Post, "/patient-card/scan", body = ScanRequest(token = token))

    // ── Labs ──────────────────────────────────────────────────────────────────

    suspend fun getMyLab(): LabResponse =
        request(HttpMethod.Get, "/labs/me")

    suspend fun updateMyLab(request: LabUpdate): LabUpdateResponse =
        request(HttpMethod.Put, "/labs/me", body = request)

    suspend fun listEmployees(): EmployeeListResponse =
        request(HttpMethod.Get, "/labs/me/employees")

    suspend fun createEmployee(request: CreateEmployeeRequest): EmployeeCreateResponse =
        request(HttpMethod.Post, "/labs/me/employees", body = request)

    suspend fun updateEmployee(employeeId: Int, request: UpdateEmployeeRequest): Map<String, String> =
        request(HttpMethod.Put, "/labs/me/employees/$employeeId", body = request)

    // ── Orders & Results ─────────────────────────────────────────────────────

    suspend fun listTestProfiles(): Map<String, List<TestProfile>> =
        request(HttpMethod.Get, "/test-profiles")

    suspend fun createOrder(request: CreateOrderRequest): OrderResponse =
        request(HttpMethod.Post, "/orders", body = request)

    suspend fun listOrders(
        skip: Int = 0,
        limit: Int = 50,
        search: String? = null,
    ): OrderListResponse {
        val params = mutableMapOf("skip" to skip.toString(), "limit" to limit.toString())
        search?.let { params["search"] = it }
        return request(HttpMethod.Get, "/orders", queryParams = params)
    }

    suspend fun getOrder(orderId: Int): OrderResponse =
        request(HttpMethod.Get, "/orders/$orderId")

    suspend fun validateOrder(orderId: Int): ValidateOrderResponse =
        request(HttpMethod.Post, "/orders/$orderId/validate")

    suspend fun cancelOrder(orderId: Int): Map<String, String> =
        request(HttpMethod.Post, "/orders/$orderId/cancel")

    suspend fun getPublicResult(token: String): PublicResultResponse =
        request(HttpMethod.Get, "/r/$token")

    suspend fun getPatientHistoryByPhone(phone: String, name: String? = null): List<OrderResponse> {
        val params = mutableMapOf<String, String>()
        name?.let { params["name"] = it }
        return request(HttpMethod.Get, "/history/$phone", queryParams = params)
    }

    suspend fun getPatientHistoryById(patientId: Int): List<OrderResponse> =
        request(HttpMethod.Get, "/patient-history/$patientId")

    suspend fun analyzeResults(request: AnalyzeRequest): AnalyzeResponse =
        request(HttpMethod.Post, "/analyze", body = request)

    suspend fun getOrderIntelligence(orderId: Int): OrderIntelligenceResponse =
        request(HttpMethod.Get, "/orders/$orderId/intelligence")

    suspend fun createBatchOrders(request: BatchOrderRequest): BatchOrderResponse =
        request(HttpMethod.Post, "/batch/orders", body = request)

    // ── Device Results ────────────────────────────────────────────────────────

    suspend fun submitDeviceResult(request: DeviceSubmission): DeviceSubmissionResponse =
        request(HttpMethod.Post, "/device/results", body = request)

    // ── Samples ───────────────────────────────────────────────────────────────

    suspend fun createSample(request: SampleCreate): SampleCreateResponse =
        request(HttpMethod.Post, "/samples", body = request)

    suspend fun listSamples(
        status: String? = null,
        skip: Int = 0,
        limit: Int = 50,
    ): SampleListResponse {
        val params = mutableMapOf("skip" to skip.toString(), "limit" to limit.toString())
        status?.let { params["status"] = it }
        return request(HttpMethod.Get, "/samples", queryParams = params)
    }

    suspend fun getSample(barcode: String): SampleResponse =
        request(HttpMethod.Get, "/samples/$barcode")

    suspend fun updateSample(barcode: String, request: SampleUpdate): SampleUpdateResponse =
        request(HttpMethod.Put, "/samples/$barcode", body = request)

    // ── Consent ───────────────────────────────────────────────────────────────

    suspend fun grantConsent(request: GrantRequest): GrantResponse =
        request(HttpMethod.Post, "/consent/grant", body = request)

    suspend fun revokeConsent(request: RevokeRequest): RevokeResponse =
        request(HttpMethod.Post, "/consent/revoke", body = request)

    suspend fun checkConsent(gpid: String, granteeId: String, scope: String): CheckResponse =
        request(HttpMethod.Post, "/consent/check", body = CheckRequest(gpid = gpid, granteeId = granteeId, scope = scope))

    // ── Claims ────────────────────────────────────────────────────────────────

    suspend fun createClaim(request: ClaimCreate): ClaimResponse =
        request(HttpMethod.Post, "/claims", body = request)

    suspend fun getClaim(claimId: Int): ClaimResponse =
        request(HttpMethod.Get, "/claims/$claimId")

    suspend fun validateClaim(claimId: Int): ClaimValidateResponse =
        request(HttpMethod.Post, "/claims/$claimId/validate")

    suspend fun submitClaim(claimId: Int): ClaimSubmitResponse =
        request(HttpMethod.Post, "/claims/$claimId/submit")

    // ── Edge ──────────────────────────────────────────────────────────────────

    suspend fun registerDevice(request: RegisterDeviceRequest): RegisterDeviceResponse =
        request(HttpMethod.Post, "/edge/devices/register", body = request)

    suspend fun listDevices(): DeviceListResponse =
        request(HttpMethod.Get, "/edge/devices")

    suspend fun getDevice(deviceId: String): DeviceDetail =
        request(HttpMethod.Get, "/edge/devices/$deviceId")

    suspend fun quarantineDevice(deviceId: String): Map<String, String> =
        request(HttpMethod.Post, "/edge/devices/$deviceId/quarantine")

    suspend fun revokeDevice(deviceId: String): Map<String, String> =
        request(HttpMethod.Post, "/edge/devices/$deviceId/revoke")

    suspend fun reinstateDevice(deviceId: String): Map<String, String> =
        request(HttpMethod.Post, "/edge/devices/$deviceId/reinstate")

    suspend fun killSwitchDevice(deviceId: String): Map<String, String> =
        request(HttpMethod.Post, "/edge/devices/$deviceId/kill_switch")

    suspend fun submitTask(request: TaskSubmitRequest): TaskResponse =
        request(HttpMethod.Post, "/edge/tasks", body = request)

    suspend fun listTasks(): TaskListResponse =
        request(HttpMethod.Get, "/edge/tasks")

    suspend fun getTask(taskUid: String): TaskResponse =
        request(HttpMethod.Get, "/edge/tasks/$taskUid")

    suspend fun cancelTask(taskUid: String): Map<String, String> =
        request(HttpMethod.Post, "/edge/tasks/$taskUid/cancel")

    suspend fun getEdgePolicy(): EdgePolicyResponse =
        request(HttpMethod.Get, "/edge/policy")

    suspend fun updateEdgePolicy(request: EdgePolicyUpdate): EdgePolicyResponse =
        request(HttpMethod.Put, "/edge/policy", body = request)

    suspend fun getFleetSummary(): FleetSummaryResponse =
        request(HttpMethod.Get, "/edge/fleet/summary")

    suspend fun registerModel(request: ModelRegisterRequest): ModelResponse =
        request(HttpMethod.Post, "/edge/models", body = request)

    suspend fun listModels(): List<ModelResponse> =
        request(HttpMethod.Get, "/edge/models")

    suspend fun updateModelStatus(modelUid: String, request: ModelStatusUpdate): ModelResponse =
        request(HttpMethod.Post, "/edge/models/$modelUid/status", body = request)

    suspend fun assignModel(modelUid: String, request: ModelAssignRequest): Map<String, String> =
        request(HttpMethod.Post, "/edge/models/$modelUid/assign", body = request)

    // ── AI ────────────────────────────────────────────────────────────────────

    suspend fun aiSuggest(request: AISuggestRequest): AISuggestResponse =
        request(HttpMethod.Post, "/api/ai/suggest", body = request)

    suspend fun aiPending(): AIPendingResponse =
        request(HttpMethod.Get, "/api/ai/pending")

    suspend fun aiApprove(suggestionId: String): AIApproveResponse =
        request(HttpMethod.Post, "/api/ai/approve/$suggestionId")

    suspend fun aiReject(suggestionId: String, request: AIRejectRequest = AIRejectRequest()): AIRejectResponse =
        request(HttpMethod.Post, "/api/ai/reject/$suggestionId", body = request)

    suspend fun aiExecute(suggestionId: String): AIExecuteResponse =
        request(HttpMethod.Post, "/api/ai/execute/$suggestionId")

    suspend fun aiAnalyzeOrder(orderId: Int): OrderIntelligenceResponse =
        request(HttpMethod.Post, "/api/ai/analyze-order/$orderId")

    suspend fun aiInterpret(token: String): AIInterpretResponse =
        request(HttpMethod.Get, "/api/ai/interpret/$token")

    suspend fun aiChat(request: AIChatRequest): AIChatResponse =
        request(HttpMethod.Post, "/api/ai/chat", body = request)

    // ── Subscription / Tiers ──────────────────────────────────────────────────

    suspend fun listTiers(): TierListResponse =
        request(HttpMethod.Get, "/tiers")

    suspend fun getMySubscription(): SubscriptionInfoResponse =
        request(HttpMethod.Get, "/tiers/my")

    suspend fun requestUpgrade(request: UpgradeRequest): UpgradeResponse =
        request(HttpMethod.Post, "/tiers/upgrade", body = request)

    suspend fun listUpgradeRequests(): List<UpgradeRequestResponse> =
        request(HttpMethod.Get, "/tiers/upgrade-requests")

    suspend fun requestUpgradeDemand(request: UpgradeDemandRequest): UpgradeResponse =
        request(HttpMethod.Post, "/tiers/upgrade-demand", body = request)

    suspend fun listUpgradeDemands(): UpgradeDemandResponse =
        request(HttpMethod.Get, "/admin/tiers/demands")

    suspend fun adminSetTier(labId: Int, request: AdminSetTierRequest): Map<String, String> =
        request(HttpMethod.Put, "/admin/tiers/$labId", body = request)

    suspend fun adminSetFeatureFlag(labId: Int, request: FeatureFlagRequest): FeatureFlagResponse =
        request(HttpMethod.Post, "/admin/tiers/flags/$labId", body = request)

    // ── Admin ─────────────────────────────────────────────────────────────────

    suspend fun adminListLabs(): List<LabResponse> =
        request(HttpMethod.Get, "/admin/labs")

    suspend fun adminCreateLab(request: CreateLabRequest): LabResponse =
        request(HttpMethod.Post, "/admin/labs", body = request)

    suspend fun adminListUsers(): UserListResponse =
        request(HttpMethod.Get, "/admin/users")

    suspend fun adminCreateUser(request: CreateUserRequest): CreateUserResponse =
        request(HttpMethod.Post, "/admin/users", body = request)

    suspend fun adminChangeUserRole(userId: Int, request: ChangeRoleRequest): Map<String, String> =
        request(HttpMethod.Put, "/admin/users/$userId/role", body = request)

    suspend fun adminKillSwitch(request: KillSwitchRequest = KillSwitchRequest()): KillSwitchResponse =
        request(HttpMethod.Post, "/admin/kill-switch", body = request)

    // ── Dashboard / Stats ─────────────────────────────────────────────────────

    suspend fun getDashboardStats(): DashboardStatsResponse =
        request(HttpMethod.Get, "/dashboard/stats")

    // ── Identity ──────────────────────────────────────────────────────────────

    suspend fun verifyNationalId(request: NationalIdRequest): IdentityVerifyResponse =
        request(HttpMethod.Post, "/national-id/verify", body = request)

    suspend fun linkIdentity(request: LinkIdentityRequest): Map<String, String> =
        request(HttpMethod.Post, "/identity/link", body = request)

    // ── MPI ───────────────────────────────────────────────────────────────────

    suspend fun mpiCheckDuplicates(request: MPIDuplicateCheckRequest): MPIDuplicateCheckResponse =
        request(HttpMethod.Post, "/mpi/check-duplicates", body = request)

    suspend fun mpiMatch(request: MPIMatchRequest): MPIMatchResponse =
        request(HttpMethod.Post, "/mpi/match", body = request)

    suspend fun mpiMerge(request: MPIMergeRequest): MPIMergeResponse =
        request(HttpMethod.Post, "/mpi/merge", body = request)

    // ── Mobile ────────────────────────────────────────────────────────────────

    suspend fun registerDeviceToken(request: DeviceTokenRequest): Map<String, String> =
        request(HttpMethod.Post, "/mobile/register-device", body = request)

    // ── Registration ──────────────────────────────────────────────────────────

    suspend fun registerLab(request: LabRegisterRequest): Map<String, Any> =
        request(HttpMethod.Post, "/register", body = request)

    suspend fun registerCitizen(request: CitizenRegisterRequest): Map<String, Any> =
        request(HttpMethod.Post, "/register/citizen", body = request)

    suspend fun registerStaff(request: StaffRegisterRequest): Map<String, Any> =
        request(HttpMethod.Post, "/register/staff", body = request)

    suspend fun registerDoctor(request: DoctorRegisterRequest): Map<String, Any> =
        request(HttpMethod.Post, "/register/doctor", body = request)

    // ── Health ────────────────────────────────────────────────────────────────

    suspend fun healthCheck(): Map<String, Any> =
        request(HttpMethod.Get, "/health")

    suspend fun healthReady(): Map<String, Any> =
        request(HttpMethod.Get, "/health/ready")

    suspend fun healthDeep(): Map<String, Any> =
        request(HttpMethod.Get, "/health/deep")

    override fun close() {
        httpClient.close()
    }
}

data class GulaConfig(
    val baseUrl: String,
    val maxRetries: Int = 3,
    val requestTimeoutMs: Long = 30_000L,
    val connectTimeoutMs: Long = 10_000L,
    val socketTimeoutMs: Long = 30_000L,
    val idempotencyKey: String? = null,
) {
    companion object {
        fun production(): GulaConfig = GulaConfig(baseUrl = "https://api.gulaplatform.com")
        fun staging(): GulaConfig = GulaConfig(baseUrl = "https://staging.api.gulaplatform.com")
        fun local(): GulaConfig = GulaConfig(baseUrl = "http://localhost:8000")
    }
}
