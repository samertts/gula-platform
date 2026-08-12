package io.gula.android.ui.features.samples

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import io.gula.android.domain.model.CreateSampleRequest
import io.gula.android.domain.model.Sample
import io.gula.android.domain.model.UpdateSampleRequest
import io.gula.android.domain.repository.SampleRepository
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SamplesUiState(
    val isLoading: Boolean = false,
    val samples: List<Sample> = emptyList(),
    val selectedSample: Sample? = null,
    val error: String? = null,
    val isSaving: Boolean = false,
    val saveSuccess: Boolean = false,
    val scannedBarcode: String = "",
)

@HiltViewModel
class SamplesViewModel @Inject constructor(
    private val sampleRepository: SampleRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(SamplesUiState())
    val uiState: StateFlow<SamplesUiState> = _uiState.asStateFlow()

    init {
        loadSamples()
    }

    fun loadSamples(status: String? = null) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            sampleRepository.getSamples(status).collect { resource ->
                when (resource) {
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            samples = resource.data,
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

    fun loadSample(barcode: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            sampleRepository.getSampleByBarcode(barcode).collect { resource ->
                when (resource) {
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            selectedSample = resource.data,
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

    fun createSample(orderId: Int, sampleType: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSaving = true, error = null)
            when (val result = sampleRepository.createSample(
                CreateSampleRequest(orderId = orderId, sampleType = sampleType)
            )) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, saveSuccess = true)
                    loadSamples()
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, error = result.message)
                }
                else -> {}
            }
        }
    }

    fun updateSample(barcode: String, status: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSaving = true, error = null)
            when (val result = sampleRepository.updateSample(
                barcode, UpdateSampleRequest(status = status)
            )) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, saveSuccess = true)
                    loadSample(barcode)
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, error = result.message)
                }
                else -> {}
            }
        }
    }

    fun setBarcode(barcode: String) {
        _uiState.value = _uiState.value.copy(scannedBarcode = barcode)
    }

    fun refresh() {
        loadSamples()
    }
}
