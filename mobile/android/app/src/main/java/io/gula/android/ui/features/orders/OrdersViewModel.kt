package io.gula.android.ui.features.orders

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import io.gula.android.domain.model.*
import io.gula.android.domain.repository.OrderRepository
import io.gula.android.domain.repository.PatientRepository
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class OrdersUiState(
    val isLoading: Boolean = false,
    val orders: List<Order> = emptyList(),
    val selectedOrder: Order? = null,
    val searchQuery: String = "",
    val error: String? = null,
    val isSaving: Boolean = false,
    val saveSuccess: Boolean = false,
    val availablePatients: List<Patient> = emptyList(),
    val selectedPatient: Patient? = null,
    val testItems: List<ResultItemInput> = emptyList(),
)

@HiltViewModel
class OrdersViewModel @Inject constructor(
    private val orderRepository: OrderRepository,
    private val patientRepository: PatientRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(OrdersUiState())
    val uiState: StateFlow<OrdersUiState> = _uiState.asStateFlow()

    init {
        loadOrders()
    }

    fun loadOrders() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            orderRepository.getOrders().collect { resource ->
                when (resource) {
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            orders = resource.data,
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

    fun loadOrder(id: Int) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            orderRepository.getOrderById(id).collect { resource ->
                when (resource) {
                    is Resource.Success -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            selectedOrder = resource.data,
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

    fun loadPatients() {
        viewModelScope.launch {
            patientRepository.getPatients().collect { resource ->
                if (resource is Resource.Success) {
                    _uiState.value = _uiState.value.copy(availablePatients = resource.data)
                }
            }
        }
    }

    fun createOrder(
        patientId: Int,
        doctorName: String?,
        testItems: List<ResultItemInput>,
    ) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSaving = true, error = null)
            when (val result = orderRepository.createOrder(
                CreateOrderRequest(
                    patientId = patientId,
                    doctorName = doctorName,
                    results = testItems,
                )
            )) {
                is Resource.Success -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, saveSuccess = true)
                    loadOrders()
                }
                is Resource.Error -> {
                    _uiState.value = _uiState.value.copy(isSaving = false, error = result.message)
                }
                else -> {}
            }
        }
    }

    fun cancelOrder(id: Int) {
        viewModelScope.launch {
            when (val result = orderRepository.cancelOrder(id)) {
                is Resource.Success -> loadOrders()
                is Resource.Error -> _uiState.value = _uiState.value.copy(error = result.message)
                else -> {}
            }
        }
    }

    fun validateOrder(id: Int) {
        viewModelScope.launch {
            when (val result = orderRepository.validateOrder(id)) {
                is Resource.Success -> loadOrder(id)
                is Resource.Error -> _uiState.value = _uiState.value.copy(error = result.message)
                else -> {}
            }
        }
    }

    fun refresh() {
        loadOrders()
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun resetSaveState() {
        _uiState.value = _uiState.value.copy(saveSuccess = false)
    }
}
