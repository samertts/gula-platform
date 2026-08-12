package io.gula.sdk.models

import io.gula.sdk.LabUserRole
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class LoginRequest(
    val email: String,
    val password: String,
)

@Serializable
data class LoginResponse(
    val token: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("token_type") val tokenType: String,
    val user: UserInfo,
)

@Serializable
data class UserInfo(
    val id: Int,
    val name: String,
    val email: String,
    val role: LabUserRole,
    @SerialName("lab_id") val labId: Int? = null,
    @SerialName("lab_name") val labName: String? = null,
)

@Serializable
data class RefreshRequest(
    @SerialName("refresh_token") val refreshToken: String? = null,
)

@Serializable
data class RefreshResponse(
    val token: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("token_type") val tokenType: String,
)

@Serializable
data class ChangePasswordRequest(
    @SerialName("current_password") val currentPassword: String,
    @SerialName("new_password") val newPassword: String,
)

@Serializable
data class LogoutResponse(
    val message: String,
)

@Serializable
data class LabRegisterRequest(
    @SerialName("lab_name") val labName: String,
    @SerialName("license_number") val licenseNumber: String? = null,
    @SerialName("lab_type") val labType: String? = null,
    @SerialName("director_name") val directorName: String? = null,
    val city: String? = null,
    val address: String? = null,
    val phone: String? = null,
    val website: String? = null,
    @SerialName("admin_name") val adminName: String,
    val email: String,
    val password: String,
)

@Serializable
data class CitizenRegisterRequest(
    @SerialName("full_name") val fullName: String,
    val phone: String,
    val email: String? = null,
    val password: String,
    val gender: String? = null,
    @SerialName("birth_date") val birthDate: String? = null,
    @SerialName("national_id") val nationalId: String? = null,
)

@Serializable
data class StaffRegisterRequest(
    val name: String,
    val email: String,
    val password: String,
    val role: String? = null,
)

@Serializable
data class DoctorRegisterRequest(
    @SerialName("full_name") val fullName: String,
    val email: String,
    val phone: String,
    val password: String,
    @SerialName("license_number") val licenseNumber: String,
    val specialty: String? = null,
    val workplace: String? = null,
    @SerialName("national_id") val nationalId: String? = null,
)

@Serializable
data class DeviceTokenRequest(
    @SerialName("device_token") val deviceToken: String,
    val platform: String,
    @SerialName("app_version") val appVersion: String? = null,
)

@Serializable
data class CitizenLoginRequest(
    val identifier: String? = null,
    val email: String? = null,
    val password: String,
)

@Serializable
data class NationalIdRequest(
    @SerialName("national_id") val nationalId: String,
)

@Serializable
data class LinkIdentityRequest(
    @SerialName("patient_id") val patientId: Int,
    @SerialName("national_id") val nationalId: String,
    @SerialName("confirm_name") val confirmName: String? = null,
)
