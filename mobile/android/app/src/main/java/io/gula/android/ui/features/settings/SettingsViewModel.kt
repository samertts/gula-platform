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
    val deferredSync: Int = 0,
    val lastSyncTime: String? = null,
    val textScale: Float = 1.0f,
    val highContrast: Boolean = false,
    val reducedMotion: Boolean = false,
    val screenReaderOptimized: Boolean = false,
    val largerTouchTargets: Boolean = false,
    val colorBlindMode: String = "none",
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
            textScale = encryptedPrefs.accessibilityTextScale,
            highContrast = encryptedPrefs.accessibilityHighContrast,
            reducedMotion = encryptedPrefs.accessibilityReducedMotion,
            screenReaderOptimized = encryptedPrefs.accessibilityScreenReader,
            largerTouchTargets = encryptedPrefs.accessibilityLargerTouchTargets,
            colorBlindMode = encryptedPrefs.accessibilityColorBlindMode,
        )
    }

    private fun loadSyncStatus() {
        viewModelScope.launch {
            syncRepository.syncStatus.collect { status ->
                _uiState.value = _uiState.value.copy(
                    isSyncing = status.isSyncing,
                    pendingSync = status.pendingCount,
                    failedSync = status.failedCount,
                    deferredSync = status.deferredCount,
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

    fun setTextScale(scale: Float) {
        val safeScale = scale.coerceIn(0.85f, 2.0f)
        encryptedPrefs.accessibilityTextScale = safeScale
        _uiState.value = _uiState.value.copy(textScale = safeScale)
    }

    fun setHighContrast(enabled: Boolean) {
        encryptedPrefs.accessibilityHighContrast = enabled
        _uiState.value = _uiState.value.copy(highContrast = enabled)
    }

    fun setReducedMotion(enabled: Boolean) {
        encryptedPrefs.accessibilityReducedMotion = enabled
        _uiState.value = _uiState.value.copy(reducedMotion = enabled)
    }

    fun setScreenReaderOptimized(enabled: Boolean) {
        encryptedPrefs.accessibilityScreenReader = enabled
        _uiState.value = _uiState.value.copy(screenReaderOptimized = enabled)
    }

    fun setLargerTouchTargets(enabled: Boolean) {
        encryptedPrefs.accessibilityLargerTouchTargets = enabled
        _uiState.value = _uiState.value.copy(largerTouchTargets = enabled)
    }

    fun setColorBlindMode(mode: String) {
        val safeMode = mode.takeIf { it in setOf("none", "protanopia", "deuteranopia", "tritanopia", "monochrome") } ?: "none"
        encryptedPrefs.accessibilityColorBlindMode = safeMode
        _uiState.value = _uiState.value.copy(colorBlindMode = safeMode)
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
