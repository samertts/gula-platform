package io.gula.android.ui.features.admin

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.*
import io.gula.android.domain.repository.AuthRepository
import io.gula.android.security.EncryptedPrefs
import javax.inject.Inject
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.LabResponseDto
import io.gula.android.data.remote.dto.LabUserResponseDto

data class AdminUiState(
    val isLoading: Boolean = false,
    val labs: List<LabResponseDto> = emptyList(),
    val users: List<LabUserResponseDto> = emptyList(),
    val error: String? = null,
    val isAdmin: Boolean = false,
)

@HiltViewModel
class AdminViewModel @Inject constructor(
    private val gulaApi: GulaApi,
    private val encryptedPrefs: EncryptedPrefs,
) : ViewModel() {

    private val _uiState = MutableStateFlow(AdminUiState())
    val uiState: StateFlow<AdminUiState> = _uiState.asStateFlow()

    init {
        checkAccess()
    }

    private fun checkAccess() {
        val role = encryptedPrefs.userRole
        if (role == "master_admin" || role == "admin" || role == "ministry_admin") {
            _uiState.value = _uiState.value.copy(isAdmin = true)
            loadData()
        }
    }

    private fun loadData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            try {
                val labsResponse = gulaApi.adminListLabs()
                val usersResponse = gulaApi.adminListUsers()
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    labs = labsResponse.body() ?: emptyList(),
                    users = usersResponse.body() ?: emptyList(),
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(isLoading = false, error = e.message)
            }
        }
    }

    fun refresh() { loadData() }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdminPanelScreen(
    onBack: () -> Unit,
    viewModel: AdminViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Admin Panel",
                onBackClick = onBack,
                actions = {
                    IconButton(onClick = { viewModel.refresh() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                },
            )
        },
    ) { padding ->
        if (!uiState.isAdmin) {
            GulaEmptyState(
                title = "Access Denied",
                message = "You do not have admin privileges",
                modifier = Modifier.padding(padding),
            )
        } else if (uiState.isLoading) {
            GulaLoadingIndicator(modifier = Modifier.padding(padding))
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text("Admin Dashboard", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)

                GulaCard {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Labs (${uiState.labs.size})", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(8.dp))
                        uiState.labs.take(5).forEach { lab ->
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Text(lab.name, style = MaterialTheme.typography.bodyMedium)
                                Text(lab.city ?: "", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            HorizontalDivider()
                        }
                    }
                }

                GulaCard {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Users (${uiState.users.size})", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(8.dp))
                        uiState.users.take(5).forEach { user ->
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Text(user.name, style = MaterialTheme.typography.bodyMedium)
                                GulaStatusBadge(text = user.role, color = MaterialTheme.colorScheme.secondary)
                            }
                            HorizontalDivider()
                        }
                    }
                }
            }
        }
    }
}
