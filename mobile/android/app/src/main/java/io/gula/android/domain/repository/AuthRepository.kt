package io.gula.android.domain.repository

import io.gula.android.domain.model.AuthTokens
import io.gula.android.domain.model.User
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow

interface AuthRepository {
    val currentUser: Flow<User?>
    val isLoggedIn: Flow<Boolean>
    val authTokens: Flow<AuthTokens?>

    suspend fun login(email: String, password: String): Resource<AuthTokens>
    suspend fun loginWithBiometric(): Resource<AuthTokens>
    suspend fun registerLab(
        labName: String,
        adminName: String,
        email: String,
        password: String,
    ): Resource<Unit>
    suspend fun registerStaff(
        name: String,
        email: String,
        password: String,
        role: String? = null,
    ): Resource<Unit>
    suspend fun verifyMfa(code: String, sessionId: String): Resource<AuthTokens>
    suspend fun refreshToken(): Resource<AuthTokens>
    suspend fun logout()
    suspend fun changePassword(currentPassword: String, newPassword: String): Resource<Unit>
    suspend fun requestPasswordReset(email: String): Resource<Unit>
    suspend fun confirmPasswordReset(token: String, newPassword: String): Resource<Unit>
    suspend fun getCurrentUser(): Resource<User>
    suspend fun registerDeviceToken(token: String, platform: String = "android")
    suspend fun setBiometricEnabled(enabled: Boolean)
    suspend fun isBiometricEnabled(): Boolean
    suspend fun clearSession()
}
