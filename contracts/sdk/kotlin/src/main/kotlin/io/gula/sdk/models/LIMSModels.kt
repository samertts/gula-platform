package io.gula.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class OrganizationResponse(
    val id: Int,
    val name: String,
    @SerialName("name_ar") val nameAr: String? = null,
    @SerialName("org_type") val orgType: String,
    @SerialName("license_number") val licenseNumber: String? = null,
    @SerialName("tax_id") val taxId: String? = null,
    val phone: String? = null,
    val email: String? = null,
    val website: String? = null,
    val address: String? = null,
    val city: String? = null,
    val province: String? = null,
    val country: String = "IQ",
    @SerialName("is_active") val isActive: Boolean = true,
    @SerialName("created_at") val createdAt: String? = null,
)

@Serializable
data class FacilityResponse(
    val id: Int,
    @SerialName("organization_id") val organizationId: Int,
    val name: String,
    @SerialName("name_ar") val nameAr: String? = null,
    @SerialName("facility_type") val facilityType: String,
    val phone: String? = null,
    val email: String? = null,
    val address: String? = null,
    val city: String? = null,
    val province: String? = null,
    @SerialName("is_active") val isActive: Boolean = true,
    @SerialName("created_at") val createdAt: String? = null,
)

@Serializable
data class AppointmentResponse(
    val id: Int,
    @SerialName("patient_id") val patientId: Int,
    @SerialName("provider_id") val providerId: Int? = null,
    @SerialName("facility_id") val facilityId: Int? = null,
    @SerialName("lab_id") val labId: Int,
    @SerialName("appointment_type") val appointmentType: String,
    val status: String,
    @SerialName("scheduled_date") val scheduledDate: String,
    @SerialName("duration_minutes") val durationMinutes: Int = 30,
    val reason: String? = null,
    val notes: String? = null,
    @SerialName("created_at") val createdAt: String? = null,
)

@Serializable
data class AppointmentCreate(
    @SerialName("patient_id") val patientId: Int,
    @SerialName("provider_id") val providerId: Int? = null,
    @SerialName("facility_id") val facilityId: Int? = null,
    @SerialName("appointment_type") val appointmentType: String,
    @SerialName("scheduled_date") val scheduledDate: String,
    @SerialName("duration_minutes") val durationMinutes: Int = 30,
    val reason: String? = null,
    val notes: String? = null,
)

@Serializable
data class QualityControlResponse(
    val id: Int,
    @SerialName("lab_id") val labId: Int,
    @SerialName("test_name") val testName: String,
    val level: String,
    val value: Double,
    @SerialName("mean") val mean: Double? = null,
    @SerialName("std_dev") val stdDev: Double? = null,
    val status: String,
    @SerialName("measured_at") val measuredAt: String,
    val operator: String? = null,
    val notes: String? = null,
)

@Serializable
data class QualityControlCreate(
    @SerialName("test_name") val testName: String,
    val level: String,
    val value: Double,
    val operator: String? = null,
    val notes: String? = null,
)

@Serializable
data class QualityControlListResponse(
    val total: Int,
    val controls: List<QualityControlResponse>,
)

@Serializable
data class TestTypeResponse(
    val id: Int,
    @SerialName("test_code") val testCode: String? = null,
    @SerialName("test_name") val testName: String,
    @SerialName("test_name_ar") val testNameAr: String? = null,
    val category: String? = null,
    val unit: String? = null,
    @SerialName("normal_range_low") val normalRangeLow: Double? = null,
    @SerialName("normal_range_high") val normalRangeHigh: Double? = null,
    @SerialName("is_active") val isActive: Boolean = true,
)

@Serializable
data class AuditLogResponse(
    val id: Int,
    @SerialName("user_id") val userId: Int? = null,
    @SerialName("user_role") val userRole: String? = null,
    val action: String,
    @SerialName("resource_type") val resourceType: String,
    @SerialName("resource_id") val resourceId: Int? = null,
    val details: String? = null,
    @SerialName("ip_address") val ipAddress: String? = null,
    @SerialName("created_at") val createdAt: String? = null,
)

@Serializable
data class AuditLogListResponse(
    val total: Int,
    val logs: List<AuditLogResponse>,
)
