package io.gula.sdk.models

import io.gula.sdk.LabType
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class LabResponse(
    val id: Int,
    val name: String,
    @SerialName("license_number") val licenseNumber: String? = null,
    @SerialName("lab_type") val labType: LabType? = null,
    @SerialName("director_name") val directorName: String? = null,
    val website: String? = null,
    val city: String? = null,
    val address: String? = null,
    val phone: String? = null,
    @SerialName("is_active") val isActive: Boolean? = null,
    @SerialName("created_at") val createdAt: String? = null,
)

@Serializable
data class LabUpdate(
    val name: String? = null,
    val city: String? = null,
    val address: String? = null,
    val phone: String? = null,
    @SerialName("license_number") val licenseNumber: String? = null,
    @SerialName("lab_type") val labType: String? = null,
    @SerialName("director_name") val directorName: String? = null,
    val website: String? = null,
)

@Serializable
data class EmployeeResponse(
    val id: Int,
    val name: String,
    val email: String,
    val role: String,
    @SerialName("is_active") val isActive: Boolean,
    @SerialName("created_at") val createdAt: String? = null,
)

@Serializable
data class EmployeeListResponse(
    val employees: List<EmployeeResponse>,
)

@Serializable
data class CreateEmployeeRequest(
    val name: String,
    val email: String,
    val password: String,
    val role: String = "staff",
)

@Serializable
data class UpdateEmployeeRequest(
    @SerialName("is_active") val isActive: Boolean? = null,
    val role: String? = null,
)

@Serializable
data class EmployeeCreateResponse(
    val message: String,
    val id: Int,
)

@Serializable
data class LabUpdateResponse(
    val message: String,
    val lab: LabResponse,
)

@Serializable
data class CreateLabRequest(
    val name: String,
    val city: String? = null,
    val phone: String? = null,
    @SerialName("admin_email") val adminEmail: String,
    @SerialName("admin_password") val adminPassword: String,
    @SerialName("admin_name") val adminName: String,
    @SerialName("province_id") val provinceId: Int? = null,
)
