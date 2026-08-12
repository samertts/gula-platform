package io.gula.android.ui.features.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.DashboardStatsDto
import io.gula.android.domain.model.DashboardStats
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DashboardUiState(
    val isLoading: Boolean = false,
    val stats: DashboardStats = DashboardStats(),
    val error: String? = null,
    val isOffline: Boolean = false,
)

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val gulaApi: GulaApi,
) : ViewModel() {

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        loadDashboard()
    }

    fun loadDashboard() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            try {
                val response = gulaApi.getDashboardStats()
                if (response.isSuccessful) {
                    val dto = response.body() ?: DashboardStatsDto()
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        stats = DashboardStats(
                            patientsCount = dto.patientsCount,
                            ordersToday = dto.ordersToday,
                            pendingResults = dto.pendingResults,
                            criticalAlerts = dto.criticalAlerts,
                            samplesToday = dto.samplesToday,
                            revenueToday = dto.revenueToday,
                        ),
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = "Failed to load dashboard",
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message,
                    isOffline = true,
                )
            }
        }
    }

    fun refresh() {
        loadDashboard()
    }
}
