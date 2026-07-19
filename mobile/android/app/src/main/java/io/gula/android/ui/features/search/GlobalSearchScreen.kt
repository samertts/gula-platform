package io.gula.android.ui.features.search

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.*
import io.gula.android.ui.components.order.OrderCard
import io.gula.android.ui.components.patient.PatientCard
import io.gula.android.ui.features.patients.PatientsViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GlobalSearchScreen(
    onBack: () -> Unit,
    onPatientClick: (Int) -> Unit,
    onOrderClick: (Int) -> Unit,
    viewModel: PatientsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Search",
                onBackClick = onBack,
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            GulaSearchBar(
                query = uiState.searchQuery,
                onQueryChange = { viewModel.searchPatients(it) },
                placeholder = "Search patients, orders, results...",
                modifier = Modifier.padding(16.dp),
            )

            if (uiState.isLoading) {
                GulaLoadingIndicator()
            } else if (uiState.searchQuery.isBlank()) {
                GulaEmptyState(
                    title = "Search",
                    message = "Type to search patients by name or phone",
                    modifier = Modifier.weight(1f),
                )
            } else if (uiState.patients.isEmpty()) {
                GulaEmptyState(
                    title = "No Results",
                    message = "No patients found matching '${uiState.searchQuery}'",
                    modifier = Modifier.weight(1f),
                )
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    item {
                        Text("Patients (${uiState.patients.size})", style = MaterialTheme.typography.titleSmall)
                        Spacer(Modifier.height(8.dp))
                    }
                    items(uiState.patients, key = { it.id }) { patient ->
                        PatientCard(
                            patient = patient,
                            onClick = { onPatientClick(patient.id) },
                        )
                    }
                }
            }
        }
    }
}
