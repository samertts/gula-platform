package io.gula.android.domain.model

data class User(
    val id: Int,
    val email: String,
    val name: String,
    val role: String,
    val labId: Int? = null,
    val labName: String? = null,
    val isActive: Boolean = true,
    val phone: String? = null,
)

data class AuthTokens(
    val accessToken: String,
    val refreshToken: String,
    val tokenType: String = "bearer",
    val expiresIn: Long = 3600,
)

data class LoginCredentials(
    val email: String,
    val password: String,
)

data class MfaVerification(
    val code: String,
    val sessionId: String,
)

data class PasswordResetRequest(
    val email: String,
)

data class PasswordResetConfirm(
    val token: String,
    val newPassword: String,
)

data class DeviceToken(
    val token: String,
    val platform: String = "android",
    val appVersion: String? = null,
)
