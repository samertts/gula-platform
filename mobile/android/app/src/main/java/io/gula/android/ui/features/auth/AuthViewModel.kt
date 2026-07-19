package io.gula.android.ui.features.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import io.gula.android.domain.model.AuthTokens
import io.gula.android.domain.repository.AuthRepository
import io.gula.android.security.BiometricAuth
import io.gula.android.security.EncryptedPrefs
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AuthUiState(
    val isLoading: Boolean = false,
    val isLoggedIn: Boolean = false,
    val userEmail: String = "",
    val userName: String = "",
    val userRole: String = "",
    val error: String? = null,
    val mfaRequired: Boolean = false,
    val mfaSessionId: String = "",
    val biometricAvailable: Boolean = false,
)

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val biometricAuth: BiometricAuth,
    private val encryptedPrefs: EncryptedPrefs,
) : ViewModel() {

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    init {
        checkSession()
        _uiState.value = _uiState.value.copy(
            biometricAvailable = biometricAuth.isAvailable()
        )
    }

    fun login(email: String, password: String) {
        if (email.isBlank() || password.isBlank()) {
            _uiState.value = _uiState.value.copy(error = "Please fill in all fields")
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = authRepository.login(email, password)) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        isLoggedIn = true,
                        userEmail = email,
                    )
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = result.message,
                    )
                }
                else -> {}
            }
        }
    }

    fun loginWithBiometric() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = authRepository.loginWithBiometric()) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(isLoading = false, isLoggedIn = true)
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(isLoading = false, error = result.message)
                }
                else -> {}
            }
        }
    }

    fun verifyMfa(code: String, sessionId: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = authRepository.verifyMfa(code, sessionId)) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(isLoading = false, mfaRequired = false, isLoggedIn = true)
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(isLoading = false, error = result.message)
                }
                else -> {}
            }
        }
    }

    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
            _uiState.value = AuthUiState(biometricAvailable = biometricAuth.isAvailable())
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun registerLab(labName: String, adminName: String, email: String, password: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = authRepository.registerLab(labName, adminName, email, password)) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(isLoading = false)
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(isLoading = false, error = result.message)
                }
                else -> {}
            }
        }
    }

    fun registerStaff(name: String, email: String, password: String, role: String?) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = authRepository.registerStaff(name, email, password, role)) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(isLoading = false)
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(isLoading = false, error = result.message)
                }
                else -> {}
            }
        }
    }

    private fun checkSession() {
        viewModelScope.launch {
            authRepository.isLoggedIn.collect { loggedIn ->
                if (loggedIn) {
                    val tokens = encryptedPrefs.accessToken
                    _uiState.value = _uiState.value.copy(
                        isLoggedIn = true,
                        userEmail = encryptedPrefs.userEmail ?: "",
                        userName = encryptedPrefs.userName ?: "",
                        userRole = encryptedPrefs.userRole ?: "",
                    )
                }
            }
        }
    }
}
