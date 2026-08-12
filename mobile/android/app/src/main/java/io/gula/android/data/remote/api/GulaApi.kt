package io.gula.android.data.remote.api

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
import io.gula.android.data.remote.dto.*
import retrofit2.Response
import retrofit2.http.*

interface GulaApi {
    // ── Patients ───────────────────────────────────────────────
    @GET("patients")
    suspend fun getPatients(
        @Query("search") search: String? = null,
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("sort_by") sortBy: String? = null,
        @Query("sort_order") sortOrder: String? = null,
    ): Response<PatientListResponseDto>

    @GET("patients/{id}")
    suspend fun getPatientById(@Path("id") id: Int): Response<PatientResponseDto>

    @POST("patients")
    suspend fun createPatient(@Body request: PatientCreateRequestDto): Response<PatientResponseDto>

    @PUT("patients/{id}")
    suspend fun updatePatient(
        @Path("id") id: Int,
        @Body request: PatientUpdateRequestDto,
    ): Response<PatientResponseDto>

    @DELETE("patients/{id}")
    suspend fun deletePatient(@Path("id") id: Int): Response<MessageResponseDto>

    @GET("patients/family/{familyId}")
    suspend fun getFamilyMembers(@Path("familyId") familyId: String): Response<List<PatientResponseDto>>

    @GET("patients/{id}/history")
    suspend fun getPatientHistory(@Path("id") id: Int): Response<Map<String, Any>>

    // ── Patient Cards ──────────────────────────────────────────
    @POST("patient-card/generate/{patientId}")
    suspend fun generatePatientCard(@Path("patientId") patientId: Int): Response<PatientCardResponseDto>

    @POST("patient-card/scan")
    suspend fun scanPatientCard(@Body request: ScanRequestDto): Response<ScanResponseDto>

    // ── Orders ─────────────────────────────────────────────────
    @GET("orders")
    suspend fun getOrders(
        @Query("search") search: String? = null,
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("status") status: String? = null,
        @Query("patient_id") patientId: Int? = null,
    ): Response<OrderListResponseDto>

    @GET("orders/{id}")
    suspend fun getOrderById(@Path("id") id: Int): Response<OrderResponseDto>

    @POST("orders")
    suspend fun createOrder(@Body request: CreateOrderRequestDto): Response<OrderResponseDto>

    @POST("orders/{id}/cancel")
    suspend fun cancelOrder(@Path("id") id: Int): Response<MessageResponseDto>

    @POST("orders/{id}/validate")
    suspend fun validateOrder(@Path("id") id: Int): Response<MessageResponseDto>

    @POST("batch/orders")
    suspend fun createBatchOrders(@Body request: BatchOrderRequestDto): Response<BatchOrderResponseDto>

    @POST("analyze")
    suspend fun analyzeResults(@Body request: AnalyzeRequestDto): Response<AnalyzeResponseDto>

    @GET("orders/{id}/intelligence")
    suspend fun getOrderIntelligence(@Path("id") id: Int): Response<OrderIntelligenceResponseDto>

    @GET("test-profiles")
    suspend fun getTestProfiles(): Response<Map<String, List<TestProfileDto>>>

    // ── Samples ────────────────────────────────────────────────
    @GET("samples")
    suspend fun getSamples(
        @Query("status") status: String? = null,
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("order_id") orderId: Int? = null,
    ): Response<SampleListResponseDto>

    @GET("samples/{barcode}")
    suspend fun getSampleByBarcode(@Path("barcode") barcode: String): Response<SampleResponseDto>

    @POST("samples")
    suspend fun createSample(@Body request: SampleCreateRequestDto): Response<SampleResponseDto>

    @PUT("samples/{barcode}")
    suspend fun updateSample(
        @Path("barcode") barcode: String,
        @Body request: SampleUpdateRequestDto,
    ): Response<SampleResponseDto>

    // ── Results ────────────────────────────────────────────────
    @GET("results")
    suspend fun getResults(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("status") status: String? = null,
        @Query("order_id") orderId: Int? = null,
    ): Response<ResultListResponseDto>

    @GET("results/{id}")
    suspend fun getResultById(@Path("id") id: Int): Response<TestResultResponseDto>

    @POST("results")
    suspend fun createResult(@Body request: TestResultCreateDto): Response<TestResultResponseDto>

    @PUT("results/{id}")
    suspend fun updateResult(
        @Path("id") id: Int,
        @Body request: TestResultCreateDto,
    ): Response<TestResultResponseDto>

    @POST("results/{id}/validate")
    suspend fun validateResult(
        @Path("id") id: Int,
        @Body request: ValidateResultRequestDto,
    ): Response<MessageResponseDto>

    @GET("critical-alerts")
    suspend fun getCriticalAlerts(): Response<CriticalAlertListDto>

    @POST("critical-alerts/{id}/acknowledge")
    suspend fun acknowledgeCriticalAlert(@Path("id") id: Int): Response<MessageResponseDto>

    // ── Notifications ──────────────────────────────────────────
    @GET("notifications")
    suspend fun getNotifications(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
    ): Response<NotificationListResponseDto>

    @POST("notifications/{id}/read")
    suspend fun markNotificationRead(@Path("id") id: Int): Response<MessageResponseDto>

    @POST("notifications/read-all")
    suspend fun markAllNotificationsRead(): Response<MessageResponseDto>

    @DELETE("notifications/{id}")
    suspend fun deleteNotification(@Path("id") id: Int): Response<MessageResponseDto>

    @GET("notifications/preferences")
    suspend fun getNotificationPreferences(): Response<NotificationPreferencesDto>

    @PUT("notifications/preferences")
    suspend fun updateNotificationPreferences(@Body prefs: NotificationPreferencesDto): Response<NotificationPreferencesDto>

    @GET("notifications/unread-count")
    suspend fun getUnreadCount(): Response<Map<String, Int>>

    // ── Dashboard ──────────────────────────────────────────────
    @GET("dashboard/stats")
    suspend fun getDashboardStats(): Response<DashboardStatsDto>

    // ── Labs ───────────────────────────────────────────────────
    @GET("labs/me")
    suspend fun getMyLab(): Response<LabResponseDto>

    @PUT("labs/me")
    suspend fun updateMyLab(@Body request: LabUpdateDto): Response<LabResponseDto>

    @GET("labs/me/employees")
    suspend fun getEmployees(): Response<List<LabUserResponseDto>>

    @POST("labs/me/employees")
    suspend fun createEmployee(@Body request: CreateEmployeeDto): Response<LabUserResponseDto>

    @PUT("labs/me/employees/{id}")
    suspend fun updateEmployee(
        @Path("id") id: Int,
        @Body request: UpdateEmployeeDto,
    ): Response<MessageResponseDto>

    // ── Inventory ──────────────────────────────────────────────
    @GET("inventory")
    suspend fun getInventory(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("search") search: String? = null,
    ): Response<InventoryListDto>

    @GET("inventory/{id}")
    suspend fun getInventoryItem(@Path("id") id: Int): Response<InventoryItemDto>

    @POST("inventory")
    suspend fun createInventoryItem(@Body request: InventoryRequestDto): Response<InventoryItemDto>

    @PUT("inventory/{id}")
    suspend fun updateInventoryItem(
        @Path("id") id: Int,
        @Body request: InventoryRequestDto,
    ): Response<InventoryItemDto>

    // ── Reports ────────────────────────────────────────────────
    @GET("reports")
    suspend fun getReports(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
    ): Response<ReportListDto>

    @POST("reports/generate")
    suspend fun generateReport(@Body request: ReportGenerateDto): Response<ReportDto>

    @GET("reports/{id}")
    suspend fun getReport(@Path("id") id: Int): Response<ReportDto>

    @GET("reports/{id}/download")
    suspend fun downloadReport(@Path("id") id: Int): Response<okhttp3.ResponseBody>

    // ── Stats ──────────────────────────────────────────────────
    @GET("stats/revenue")
    suspend fun getRevenueStats(): Response<Map<String, Any>>

    @GET("stats/patients/demographics")
    suspend fun getPatientDemographics(): Response<Map<String, Any>>

    @GET("stats/tests/popularity")
    suspend fun getTestPopularity(): Response<List<Map<String, Any>>>

    // ── Admin ──────────────────────────────────────────────────
    @GET("admin/labs")
    suspend fun adminListLabs(): Response<List<LabResponseDto>>

    @POST("admin/labs")
    suspend fun adminCreateLab(@Body request: CreateLabDto): Response<LabResponseDto>

    @GET("admin/users")
    suspend fun adminListUsers(): Response<List<LabUserResponseDto>>

    @POST("admin/users")
    suspend fun adminCreateUser(@Body request: CreateUserDto): Response<LabUserResponseDto>

    @PUT("admin/users/{id}/role")
    suspend fun adminChangeUserRole(
        @Path("id") id: Int,
        @Body request: ChangeRoleDto,
    ): Response<MessageResponseDto>

    // ── Identity ───────────────────────────────────────────────
    @POST("national-id/verify")
    suspend fun verifyNationalId(@Body request: NationalIdDto): Response<Map<String, Any>>

    // ── Device Results ─────────────────────────────────────────
    @POST("device/results")
    suspend fun submitDeviceResult(@Body request: DeviceSubmissionDto): Response<DeviceSubmissionResponseDto>

    // ── Health ─────────────────────────────────────────────────
    @GET("health")
    suspend fun healthCheck(): Response<Map<String, Any>>

    @GET("health/ready")
    suspend fun healthReady(): Response<Map<String, Any>>

    @GET("health/deep")
    suspend fun healthDeep(): Response<Map<String, Any>>
}

@JsonClass(generateAdapter = true)
data class TestProfileDto(
    @Json(name = "test_name") val testName: String,
    @Json(name = "unit") val unit: String? = null,
    @Json(name = "normal_range_low") val normalRangeLow: Double? = null,
    @Json(name = "normal_range_high") val normalRangeHigh: Double? = null,
)

@JsonClass(generateAdapter = true)
data class LabResponseDto(
    @Json(name = "id") val id: Int,
    @Json(name = "name") val name: String,
    @Json(name = "city") val city: String? = null,
    @Json(name = "address") val address: String? = null,
    @Json(name = "phone") val phone: String? = null,
    @Json(name = "license_number") val licenseNumber: String? = null,
    @Json(name = "lab_type") val labType: String? = null,
    @Json(name = "director_name") val directorName: String? = null,
    @Json(name = "website") val website: String? = null,
    @Json(name = "status") val status: String? = null,
    @Json(name = "tier") val tier: String? = null,
    @Json(name = "created_at") val createdAt: String? = null,
    @Json(name = "updated_at") val updatedAt: String? = null,
)

@JsonClass(generateAdapter = true)
data class LabUpdateDto(
    @Json(name = "name") val name: String? = null,
    @Json(name = "city") val city: String? = null,
    @Json(name = "address") val address: String? = null,
    @Json(name = "phone") val phone: String? = null,
    @Json(name = "license_number") val licenseNumber: String? = null,
    @Json(name = "lab_type") val labType: String? = null,
    @Json(name = "director_name") val directorName: String? = null,
    @Json(name = "website") val website: String? = null,
)

@JsonClass(generateAdapter = true)
data class LabUserResponseDto(
    @Json(name = "id") val id: Int,
    @Json(name = "name") val name: String,
    @Json(name = "email") val email: String,
    @Json(name = "role") val role: String,
    @Json(name = "is_active") val isActive: Boolean = true,
    @Json(name = "created_at") val createdAt: String? = null,
)

@JsonClass(generateAdapter = true)
data class CreateEmployeeDto(
    @Json(name = "name") val name: String,
    @Json(name = "email") val email: String,
    @Json(name = "password") val password: String,
    @Json(name = "role") val role: String? = null,
)

@JsonClass(generateAdapter = true)
data class UpdateEmployeeDto(
    @Json(name = "is_active") val isActive: Boolean? = null,
    @Json(name = "role") val role: String? = null,
)

@JsonClass(generateAdapter = true)
data class InventoryItemDto(
    @Json(name = "id") val id: Int,
    @Json(name = "code") val code: String,
    @Json(name = "name") val name: String,
    @Json(name = "name_ar") val nameAr: String? = null,
    @Json(name = "current_quantity") val currentQuantity: Int,
    @Json(name = "unit") val unit: String,
    @Json(name = "minimum_quantity") val minimumQuantity: Int? = null,
    @Json(name = "supplier_id") val supplierId: Int? = null,
    @Json(name = "storage_location") val storageLocation: String? = null,
)

@JsonClass(generateAdapter = true)
data class InventoryListDto(
    @Json(name = "items") val items: List<InventoryItemDto>,
    @Json(name = "total") val total: Int,
    @Json(name = "page") val page: Int = 1,
    @Json(name = "limit") val limit: Int = 20,
)

@JsonClass(generateAdapter = true)
data class InventoryRequestDto(
    @Json(name = "code") val code: String,
    @Json(name = "name") val name: String,
    @Json(name = "name_ar") val nameAr: String? = null,
    @Json(name = "current_quantity") val currentQuantity: Int,
    @Json(name = "unit") val unit: String,
    @Json(name = "minimum_quantity") val minimumQuantity: Int? = null,
    @Json(name = "supplier_id") val supplierId: Int? = null,
    @Json(name = "storage_location") val storageLocation: String? = null,
)

@JsonClass(generateAdapter = true)
data class ReportDto(
    @Json(name = "id") val id: Int,
    @Json(name = "order_id") val orderId: Int? = null,
    @Json(name = "report_number") val reportNumber: String,
    @Json(name = "title") val title: String? = null,
    @Json(name = "title_ar") val titleAr: String? = null,
    @Json(name = "locale") val locale: String? = null,
    @Json(name = "status") val status: String? = null,
    @Json(name = "created_at") val createdAt: String? = null,
)

@JsonClass(generateAdapter = true)
data class ReportListDto(
    @Json(name = "items") val items: List<ReportDto>,
    @Json(name = "total") val total: Int,
    @Json(name = "page") val page: Int = 1,
    @Json(name = "limit") val limit: Int = 20,
)

@JsonClass(generateAdapter = true)
data class ReportGenerateDto(
    @Json(name = "order_id") val orderId: Int,
    @Json(name = "report_number") val reportNumber: String,
    @Json(name = "locale") val locale: String? = null,
    @Json(name = "title") val title: String? = null,
    @Json(name = "title_ar") val titleAr: String? = null,
)

@JsonClass(generateAdapter = true)
data class CreateLabDto(
    @Json(name = "name") val name: String,
    @Json(name = "city") val city: String? = null,
    @Json(name = "phone") val phone: String? = null,
    @Json(name = "admin_email") val adminEmail: String,
    @Json(name = "admin_password") val adminPassword: String,
    @Json(name = "admin_name") val adminName: String,
)

@JsonClass(generateAdapter = true)
data class CreateUserDto(
    @Json(name = "name") val name: String,
    @Json(name = "email") val email: String,
    @Json(name = "password") val password: String,
    @Json(name = "role") val role: String,
    @Json(name = "lab_id") val labId: Int? = null,
)

@JsonClass(generateAdapter = true)
data class ChangeRoleDto(
    @Json(name = "role") val role: String,
)

@JsonClass(generateAdapter = true)
data class NationalIdDto(
    @Json(name = "national_id") val nationalId: String,
)

@JsonClass(generateAdapter = true)
data class DeviceSubmissionDto(
    @Json(name = "barcode") val barcode: String,
    @Json(name = "device_id") val deviceId: String? = null,
    @Json(name = "results") val results: List<DeviceResultDto>,
)

@JsonClass(generateAdapter = true)
data class DeviceResultDto(
    @Json(name = "test_name") val testName: String,
    @Json(name = "value") val value: Double? = null,
    @Json(name = "value_text") val valueText: String? = null,
    @Json(name = "unit") val unit: String? = null,
    @Json(name = "normal_range_low") val normalRangeLow: Double? = null,
    @Json(name = "normal_range_high") val normalRangeHigh: Double? = null,
)

@JsonClass(generateAdapter = true)
data class DeviceSubmissionResponseDto(
    @Json(name = "matched_order_id") val matchedOrderId: Int,
    @Json(name = "results_created") val resultsCreated: Int,
    @Json(name = "errors") val errors: List<String>? = null,
)
