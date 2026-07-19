package io.gula.android.ui.features.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import io.gula.android.domain.repository.AuthRepository
import io.gula.android.domain.repository.SyncRepository
import io.gula.android.security.EncryptedPrefs
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SettingsUiState(
    val locale: String = "ar",
    val darkMode: String = "system",
    val biometricEnabled: Boolean = false,
    val isSyncing: Boolean = false,
    val pendingSync: Int = 0,
    val failedSync: Int = 0,
    val lastSyncTime: String? = null,
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val encryptedPrefs: EncryptedPrefs,
    private val authRepository: AuthRepository,
    private val syncRepository: SyncRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        loadSettings()
        loadSyncStatus()
    }

    private fun loadSettings() {
        _uiState.value = _uiState.value.copy(
            locale = encryptedPrefs.locale,
            darkMode = encryptedPrefs.darkMode,
            biometricEnabled = encryptedPrefs.biometricEnabled,
        )
    }

    private fun loadSyncStatus() {
        viewModelScope.launch {
            syncRepository.syncStatus.collect { status ->
                _uiState.value = _uiState.value.copy(
                    isSyncing = status.isSyncing,
                    pendingSync = status.pendingCount,
                    failedSync = status.failedCount,
                    lastSyncTime = status.lastSyncTime,
                )
            }
        }
    }

    fun setLocale(locale: String) {
        encryptedPrefs.locale = locale
        _uiState.value = _uiState.value.copy(locale = locale)
    }

    fun setDarkMode(mode: String) {
        encryptedPrefs.darkMode = mode
        _uiState.value = _uiState.value.copy(darkMode = mode)
    }

    fun setBiometricEnabled(enabled: Boolean) {
        viewModelScope.launch {
            authRepository.setBiometricEnabled(enabled)
            _uiState.value = _uiState.value.copy(biometricEnabled = enabled)
        }
    }

    fun syncNow() {
        viewModelScope.launch {
            syncRepository.processQueue()
            loadSyncStatus()
        }
    }

    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
        }
    }
}
