package io.gula.android.data.repository

import io.gula.android.data.local.dao.UserDao
import io.gula.android.data.local.entity.UserEntity
import io.gula.android.data.remote.api.AuthApi
import io.gula.android.data.remote.dto.*
import io.gula.android.domain.model.AuthTokens
import io.gula.android.domain.model.User
import io.gula.android.domain.repository.AuthRepository
import io.gula.android.BuildConfig
import io.gula.android.security.EncryptedPrefs
import io.gula.android.util.Resource
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val authApi: AuthApi,
    private val userDao: UserDao,
    private val encryptedPrefs: EncryptedPrefs,
) : AuthRepository {

    private val _currentUser = MutableStateFlow<User?>(null)
    override val currentUser: Flow<User?> = _currentUser.asStateFlow()

    private val _isLoggedIn = MutableStateFlow(encryptedPrefs.isLoggedIn)
    override val isLoggedIn: Flow<Boolean> = _isLoggedIn.asStateFlow()

    private val _authTokens = MutableStateFlow<AuthTokens?>(null)
    override val authTokens: Flow<AuthTokens?> = _authTokens.asStateFlow()
    private val repositoryScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    init {
        if (encryptedPrefs.isLoggedIn) {
            repositoryScope.launch { loadUserFromCache() }
        }
    }

    override suspend fun login(email: String, password: String): Resource<AuthTokens> {
        return try {
            val response = authApi.login(LoginRequestDto(email, password))
            if (response.isSuccessful) {
                val body = response.body()!!
                val tokens = AuthTokens(
                    accessToken = body.accessToken,
                    refreshToken = body.refreshToken,
                    tokenType = body.tokenType,
                    expiresIn = body.expiresIn,
                )
                saveTokens(tokens)
                saveUser(body.user)
                Resource.success(tokens)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun loginWithBiometric(): Resource<AuthTokens> {
        val refreshToken = encryptedPrefs.refreshToken ?: return Resource.error("No saved session")
        return try {
            val response = authApi.refreshToken(RefreshRequestDto(refreshToken))
            if (response.isSuccessful) {
                val body = response.body()!!
                val tokens = AuthTokens(
                    accessToken = body.accessToken,
                    refreshToken = body.refreshToken ?: refreshToken,
                    expiresIn = body.expiresIn,
                )
                saveTokens(tokens)
                Resource.success(tokens)
            } else {
                Resource.error("Session expired. Please login again.")
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun registerLab(
        labName: String,
        adminName: String,
        email: String,
        password: String,
    ): Resource<Unit> {
        return try {
            val response = authApi.registerLab(
                LabRegisterRequestDto(
                    labName = labName,
                    adminName = adminName,
                    email = email,
                    password = password,
                )
            )
            if (response.isSuccessful) {
                Resource.success(Unit)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun registerStaff(
        name: String,
        email: String,
        password: String,
        role: String?,
    ): Resource<Unit> {
        return try {
            val response = authApi.registerStaff(
                StaffRegisterRequestDto(name, email, password, role)
            )
            if (response.isSuccessful) {
                Resource.success(Unit)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun verifyMfa(code: String, sessionId: String): Resource<AuthTokens> {
        return try {
            val response = authApi.verifyMfa(MfaVerifyRequestDto(code, sessionId))
            if (response.isSuccessful) {
                val body = response.body()!!
                val tokens = AuthTokens(
                    accessToken = body.accessToken,
                    refreshToken = body.refreshToken,
                    tokenType = body.tokenType,
                    expiresIn = body.expiresIn,
                )
                saveTokens(tokens)
                encryptedPrefs.mfaVerified = true
                Resource.success(tokens)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun refreshToken(): Resource<AuthTokens> {
        val rt = encryptedPrefs.refreshToken ?: return Resource.error("No refresh token")
        return try {
            val response = authApi.refreshToken(RefreshRequestDto(rt))
            if (response.isSuccessful) {
                val body = response.body()!!
                val tokens = AuthTokens(
                    accessToken = body.accessToken,
                    refreshToken = body.refreshToken ?: rt,
                    expiresIn = body.expiresIn,
                )
                saveTokens(tokens)
                Resource.success(tokens)
            } else {
                clearSession()
                Resource.error("Session expired")
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun logout() {
        try {
            authApi.logout()
        } catch (_: Exception) { }
        clearSession()
    }

    override suspend fun changePassword(currentPassword: String, newPassword: String): Resource<Unit> {
        return try {
            val response = authApi.changePassword(
                ChangePasswordRequestDto(currentPassword, newPassword)
            )
            if (response.isSuccessful) Resource.success(Unit)
            else Resource.error(parseError(response.code(), response.errorBody()?.string()))
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun requestPasswordReset(email: String): Resource<Unit> {
        return try {
            val response = authApi.requestPasswordReset(PasswordResetRequestDto(email))
            if (response.isSuccessful) Resource.success(Unit)
            else Resource.error(parseError(response.code(), response.errorBody()?.string()))
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun confirmPasswordReset(token: String, newPassword: String): Resource<Unit> {
        return try {
            val response = authApi.confirmPasswordReset(
                PasswordResetConfirmDto(token, newPassword)
            )
            if (response.isSuccessful) Resource.success(Unit)
            else Resource.error(parseError(response.code(), response.errorBody()?.string()))
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun getCurrentUser(): Resource<User> {
        return try {
            val cached = userDao.getUserByIdOnce(encryptedPrefs.userId)
            if (cached != null) return Resource.success(cached.toDomain())

            val response = authApi.getCurrentUser()
            if (response.isSuccessful) {
                val body = response.body()!!
                saveUser(body)
                Resource.success(body.toDomain())
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun registerDeviceToken(token: String, platform: String) {
        try {
            authApi.registerDeviceToken(
                DeviceTokenRequestDto(
                    deviceToken = token,
                    platform = platform,
                    appVersion = BuildConfig.VERSION_NAME,
                )
            )
            encryptedPrefs.deviceToken = token
        } catch (_: Exception) { }
    }

    override suspend fun setBiometricEnabled(enabled: Boolean) {
        encryptedPrefs.biometricEnabled = enabled
    }

    override suspend fun isBiometricEnabled(): Boolean = encryptedPrefs.biometricEnabled

    override suspend fun clearSession() {
        encryptedPrefs.clearAll()
        _currentUser.value = null
        _isLoggedIn.value = false
        _authTokens.value = null
        userDao.deleteAll()
    }

    private fun saveTokens(tokens: AuthTokens) {
        encryptedPrefs.accessToken = tokens.accessToken
        encryptedPrefs.refreshToken = tokens.refreshToken
        encryptedPrefs.isLoggedIn = true
        _isLoggedIn.value = true
        _authTokens.value = tokens
    }

    private suspend fun saveUser(userDto: UserBriefDto) {
        encryptedPrefs.userId = userDto.id
        encryptedPrefs.userEmail = userDto.email
        encryptedPrefs.userName = userDto.name
        encryptedPrefs.userRole = userDto.role
        userDto.labId?.let { encryptedPrefs.labId = it }

        val user = userDto.toDomain()
        _currentUser.value = user

        runCatching {
            userDao.insert(user.toEntity())
        }
    }

    private suspend fun loadUserFromCache() {
        runCatching {
            val cached = userDao.getUserByIdOnce(encryptedPrefs.userId)
            if (cached != null) {
                _currentUser.value = cached.toDomain()
            }
        }
    }

    private fun parseError(code: Int, errorBody: String?): String {
        return when (code) {
            400 -> "Invalid request"
            401 -> "Invalid email or password"
            403 -> "Access denied"
            404 -> "Resource not found"
            409 -> "Resource already exists"
            422 -> "Validation error"
            429 -> "Too many requests. Please try again later."
            500 -> "Server error. Please try again later."
            else -> errorBody ?: "Unknown error"
        }
    }
}

private fun UserBriefDto.toDomain() = User(
    id = id,
    email = email,
    name = name,
    role = role,
    labId = labId,
    labName = labName,
    isActive = isActive,
)

private fun User.toEntity() = UserEntity(
    id = id,
    email = email,
    name = name,
    role = role,
    labId = labId,
    labName = labName,
    isActive = isActive,
)

private fun UserEntity.toDomain() = User(
    id = id,
    email = email,
    name = name,
    role = role,
    labId = labId,
    labName = labName,
    isActive = isActive,
    phone = phone,
)
