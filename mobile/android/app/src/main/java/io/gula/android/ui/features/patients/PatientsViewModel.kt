package io.gula.android.ui.features.patients

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import io.gula.android.domain.model.Patient
import io.gula.android.domain.model.PatientCreateRequest
import io.gula.android.domain.model.PatientUpdateRequest
import io.gula.android.domain.repository.PatientRepository
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class PatientsUiState(
    val isLoading: Boolean = false,
    val patients: List<Patient> = emptyList(),
    val selectedPatient: Patient? = null,
    val searchQuery: String = "",
    val error: String? = null,
    val isOffline: Boolean = false,
    val currentPage: Int = 1,
    val hasMore: Boolean = true,
    val isSaving: Boolean = false,
    val saveSuccess: Boolean = false,
)

@HiltViewModel
class PatientsViewModel @Inject constructor(
    private val patientRepository: PatientRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(PatientsUiState())
    val uiState: StateFlow<PatientsUiState> = _uiState.asStateFlow()

    init {
        loadPatients()
    }

    fun loadPatients(search: String? = null, refresh: Boolean = false) {
        viewModelScope.launch {
            if (refresh) _uiState.value = _uiState.value.copy(isLoading = true)
            patientRepository.getPatients(
                search = search ?: _uiState.value.searchQuery,
                page = 1,
                limit = 20,
            ).collect { resource ->
                when (resource) {
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            patients = resource.data,
                            error = null,
                        )
                    }
                    is Resource.Error -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = resource.message,
                            isOffline = true,
                        )
                    }
                    is Resource.Loading -> {
                        if (resource.data != null) {
                            _uiState.value = _uiState.value.copy(patients = resource.data)
                        }
                    }
                }
            }
        }
    }

    fun loadPatient(id: Int) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            patientRepository.getPatientById(id).collect { resource ->
                when (resource) {
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            selectedPatient = resource.data,
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

    fun searchPatients(query: String) {
        _uiState.value = _uiState.value.copy(searchQuery = query)
        if (query.isBlank()) {
            loadPatients()
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            when (val result = patientRepository.searchPatients(query)) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        patients = result.data,
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

    fun createPatient(
        fullName: String,
        phone: String,
        birthDate: String?,
        gender: String?,
        email: String?,
        nationalId: String?,
    ) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSaving = true, error = null)
            when (val result = patientRepository.createPatient(
                PatientCreateRequest(
                    fullName = fullName,
                    phone = phone,
                    birthDate = birthDate,
                    gender = gender,
                    email = email,
                    nationalId = nationalId,
                )
            )) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, saveSuccess = true)
                    loadPatients(refresh = true)
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, error = result.message)
                }
                else -> {}
            }
        }
    }

    fun updatePatient(id: Int, fullName: String, phone: String, email: String?) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSaving = true, error = null)
            when (val result = patientRepository.updatePatient(
                id,
                PatientUpdateRequest(fullName = fullName, phone = phone, email = email),
            )) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, saveSuccess = true)
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, error = result.message)
                }
                else -> {}
            }
        }
    }

    fun deletePatient(id: Int) {
        viewModelScope.launch {
            when (val result = patientRepository.deletePatient(id)) {
                is Resource.Success -> {
                    loadPatients(refresh = true)
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(error = result.message)
                }
                else -> {}
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun resetSaveState() {
        _uiState.value = _uiState.value.copy(saveSuccess = false)
    }
}
