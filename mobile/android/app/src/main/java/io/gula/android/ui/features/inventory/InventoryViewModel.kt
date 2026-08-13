package io.gula.android.ui.features.inventory

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.api.InventoryItemDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class InventoryUiState(
    val isLoading: Boolean = false,
    val items: List<InventoryItemDto> = emptyList(),
    val searchQuery: String = "",
    val error: String? = null,
)

@HiltViewModel
class InventoryViewModel @Inject constructor(
    private val gulaApi: GulaApi,
) : ViewModel() {

    private val _uiState = MutableStateFlow(InventoryUiState())
    val uiState: StateFlow<InventoryUiState> = _uiState.asStateFlow()

    init {
        loadInventory()
    }

    fun loadInventory(search: String? = null) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            try {
                val response = gulaApi.getInventory(search = search)
                if (response.isSuccessful) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        items = response.body()?.items ?: emptyList(),
                    )
                } else {
                    _uiState.value = _uiState.value.copy(isLoading = false, error = "Failed to load inventory")
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(isLoading = false, error = e.message)
            }
        }
    }

    fun search(query: String) {
        _uiState.value = _uiState.value.copy(searchQuery = query)
        loadInventory(query.ifBlank { null })
    }

    fun refresh() {
        loadInventory()
    }
}
