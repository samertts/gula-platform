package io.gula.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class IdentityLinkRequest(
    @SerialName("patient_id") val patientId: Int,
    @SerialName("national_id") val nationalId: String,
    @SerialName("confirm_name") val confirmName: String? = null,
)

@Serializable
data class IdentityVerifyResponse(
    val valid: Boolean,
    val name: String? = null,
    @SerialName("birth_date") val birthDate: String? = null,
    val gender: String? = null,
    val message: String? = null,
)

@Serializable
data class CreateUserRequest(
    val name: String,
    val email: String,
    val password: String,
    val role: String,
    @SerialName("lab_id") val labId: Int? = null,
    @SerialName("province_id") val provinceId: Int? = null,
    @SerialName("national_id") val nationalId: String? = null,
)

@Serializable
data class CreateUserResponse(
    val message: String,
    val id: Int,
)

@Serializable
data class ChangeRoleRequest(
    val role: String,
    @SerialName("province_id") val provinceId: Int? = null,
)

@Serializable
data class UserResponse(
    val id: Int,
    val name: String,
    val email: String? = null,
    val phone: String? = null,
    val role: String,
    @SerialName("lab_id") val labId: Int? = null,
    @SerialName("is_active") val isActive: Boolean = true,
    @SerialName("created_at") val createdAt: String? = null,
)

@Serializable
data class UserListResponse(
    val total: Int,
    val users: List<UserResponse>,
)

@Serializable
data class KillSwitchRequest(
    val reason: String? = null,
)

@Serializable
data class KillSwitchResponse(
    val message: String,
    val active: Boolean,
)

@Serializable
data class ProvinceResponse(
    val id: Int,
    val name: String,
    @SerialName("name_ar") val nameAr: String,
    val code: String? = null,
)

@Serializable
data class ComplianceReportResponse(
    @SerialName("report_id") val reportId: String,
    @SerialName("lab_id") val labId: Int,
    val period: String,
    @SerialName("generated_at") val generatedAt: String,
    @SerialName("total_orders") val totalOrders: Int = 0,
    @SerialName("total_patients") val totalPatients: Int = 0,
    @SerialName("critical_alerts") val criticalAlerts: Int = 0,
    val status: String,
    @SerialName("data_url") val dataUrl: String? = null,
)

@Serializable
data class DashboardStatsResponse(
    @SerialName("total_patients") val totalPatients: Int = 0,
    @SerialName("total_orders") val totalOrders: Int = 0,
    @SerialName("total_results") val totalResults: Int = 0,
    @SerialName("pending_orders") val pendingOrders: Int = 0,
    @SerialName("critical_alerts") val criticalAlerts: Int = 0,
    @SerialName("active_staff") val activeStaff: Int = 0,
    @SerialName("orders_today") val ordersToday: Int = 0,
    @SerialName("results_today") val resultsToday: Int = 0,
    @SerialName("samples_pending") val samplesPending: Int = 0,
)
