package io.gula.android.ui.features.results

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import io.gula.android.domain.model.*
import io.gula.android.domain.repository.ResultRepository
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ResultsUiState(
    val isLoading: Boolean = false,
    val results: List<TestResult> = emptyList(),
    val selectedResult: TestResult? = null,
    val criticalAlerts: List<CriticalAlert> = emptyList(),
    val error: String? = null,
    val isSaving: Boolean = false,
    val saveSuccess: Boolean = false,
    val validationMessage: String? = null,
)

@HiltViewModel
class ResultsViewModel @Inject constructor(
    private val resultRepository: ResultRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(ResultsUiState())
    val uiState: StateFlow<ResultsUiState> = _uiState.asStateFlow()

    init {
        loadResults()
        loadCriticalAlerts()
    }

    fun loadResults() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            resultRepository.getResults().collect { resource ->
                when (resource) {
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            results = resource.data,
                            error = null,
                        )
                    }
                    is Resource.Error -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = resource.message,
                        )
                    }
                    else -> {}
                }
            }
        }
    }

    fun loadResult(id: Int) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            resultRepository.getResultById(id).collect { resource ->
                when (resource) {
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            selectedResult = resource.data,
                        )
                    }
                    is Resource.Error -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = resource.message,
                        )
                    }
                    else -> {}
                }
            }
        }
    }

    fun loadCriticalAlerts() {
        viewModelScope.launch {
            resultRepository.getCriticalAlerts().collect { resource ->
                if (resource is Resource.Success) {
                    _uiState.value = _uiState.value.copy(criticalAlerts = resource.data)
                }
            }
        }
    }

    fun createResult(
        testCode: String,
        testNameEn: String,
        testNameAr: String,
        resultValue: Double?,
        resultText: String?,
        unit: String?,
        orderId: Int?,
    ) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSaving = true, error = null)
            val result = TestResult(
                id = 0,
                testCode = testCode,
                testNameEn = testNameEn,
                testNameAr = testNameAr,
                resultValue = resultValue,
                resultText = resultText,
                unit = unit,
                status = "pending",
                sampleCollectedAt = "",
                orderId = orderId,
            )
            when (val res = resultRepository.createResult(result)) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, saveSuccess = true)
                    loadResults()
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, error = res.message)
                }
                else -> {}
            }
        }
    }

    fun validateResult(id: Int, validation: ResultValidation) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSaving = true, error = null)
            when (val result = resultRepository.validateResult(id, validation)) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isSaving = false,
                        saveSuccess = true,
                        validationMessage = "Result validated successfully",
                    )
                    loadResult(id)
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, error = result.message)
                }
                else -> {}
            }
        }
    }

    fun acknowledgeCriticalAlert(alertId: Int) {
        viewModelScope.launch {
            resultRepository.acknowledgeCriticalAlert(alertId)
            loadCriticalAlerts()
        }
    }

    fun refresh() {
        loadResults()
        loadCriticalAlerts()
    }
}
