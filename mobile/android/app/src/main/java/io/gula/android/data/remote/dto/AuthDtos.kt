package io.gula.android.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class LoginRequestDto(
    @Json(name = "email") val email: String,
    @Json(name = "password") val password: String,
)

@JsonClass(generateAdapter = true)
data class LoginResponseDto(
    @Json(name = "access_token") val accessToken: String,
    @Json(name = "refresh_token") val refreshToken: String,
    @Json(name = "token_type") val tokenType: String = "bearer",
    @Json(name = "expires_in") val expiresIn: Long = 3600,
    @Json(name = "user") val user: UserBriefDto,
)

@JsonClass(generateAdapter = true)
data class UserBriefDto(
    @Json(name = "id") val id: Int,
    @Json(name = "email") val email: String,
    @Json(name = "name") val name: String,
    @Json(name = "role") val role: String,
    @Json(name = "lab_id") val labId: Int? = null,
    @Json(name = "lab_name") val labName: String? = null,
    @Json(name = "is_active") val isActive: Boolean = true,
)

@JsonClass(generateAdapter = true)
data class RefreshRequestDto(
    @Json(name = "refresh_token") val refreshToken: String,
)

@JsonClass(generateAdapter = true)
data class RefreshResponseDto(
    @Json(name = "access_token") val accessToken: String,
    @Json(name = "expires_in") val expiresIn: Long,
)

@JsonClass(generateAdapter = true)
data class MfaVerifyRequestDto(
    @Json(name = "code") val code: String,
    @Json(name = "session_id") val sessionId: String,
)

@JsonClass(generateAdapter = true)
data class MfaVerifyResponseDto(
    @Json(name = "access_token") val accessToken: String,
    @Json(name = "refresh_token") val refreshToken: String,
    @Json(name = "token_type") val tokenType: String,
    @Json(name = "expires_in") val expiresIn: Long,
)

@JsonClass(generateAdapter = true)
data class ChangePasswordRequestDto(
    @Json(name = "current_password") val currentPassword: String,
    @Json(name = "new_password") val newPassword: String,
)

@JsonClass(generateAdapter = true)
data class PasswordResetRequestDto(
    @Json(name = "email") val email: String,
)

@JsonClass(generateAdapter = true)
data class PasswordResetConfirmDto(
    @Json(name = "token") val token: String,
    @Json(name = "new_password") val newPassword: String,
)

@JsonClass(generateAdapter = true)
data class DeviceTokenRequestDto(
    @Json(name = "device_token") val deviceToken: String,
    @Json(name = "platform") val platform: String,
    @Json(name = "app_version") val appVersion: String? = null,
)

@JsonClass(generateAdapter = true)
data class LabRegisterRequestDto(
    @Json(name = "lab_name") val labName: String,
    @Json(name = "license_number") val licenseNumber: String? = null,
    @Json(name = "lab_type") val labType: String? = null,
    @Json(name = "director_name") val directorName: String? = null,
    @Json(name = "city") val city: String? = null,
    @Json(name = "address") val address: String? = null,
    @Json(name = "phone") val phone: String? = null,
    @Json(name = "website") val website: String? = null,
    @Json(name = "admin_name") val adminName: String,
    @Json(name = "email") val email: String,
    @Json(name = "password") val password: String,
)

@JsonClass(generateAdapter = true)
data class StaffRegisterRequestDto(
    @Json(name = "name") val name: String,
    @Json(name = "email") val email: String,
    @Json(name = "password") val password: String,
    @Json(name = "role") val role: String? = null,
)

@JsonClass(generateAdapter = true)
data class MessageResponseDto(
    @Json(name = "message") val message: String,
)

@JsonClass(generateAdapter = true)
data class ApiErrorDto(
    @Json(name = "detail") val detail: String? = null,
    @Json(name = "errors") val errors: Map<String, List<String>>? = null,
    @Json(name = "code") val code: String? = null,
)
