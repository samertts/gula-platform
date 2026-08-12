package io.gula.android.ui.features.patients

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.*
import io.gula.android.ui.components.patient.PatientCard

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PatientListScreen(
    onPatientClick: (Int) -> Unit,
    onAddPatient: () -> Unit,
    onSearch: () -> Unit,
    viewModel: PatientsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    val scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior()

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Patients",
                scrollBehavior = scrollBehavior,
                actions = {
                    IconButton(onClick = { viewModel.loadPatients(refresh = true) }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                },
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = onAddPatient,
                icon = { Icon(Icons.Default.PersonAdd, contentDescription = null) },
                text = { Text("Add Patient") },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .nestedScroll(scrollBehavior.nestedScrollConnection),
        ) {
            Spacer(Modifier.height(8.dp))
            GulaSearchBar(
                query = uiState.searchQuery,
                onQueryChange = { viewModel.searchPatients(it) },
                placeholder = "Search patients by name or phone...",
                modifier = Modifier.padding(horizontal = 16.dp),
            )
            Spacer(Modifier.height(8.dp))

            if (uiState.isLoading) {
                GulaLoadingIndicator()
            } else if (uiState.patients.isEmpty()) {
                GulaEmptyState(
                    title = "No Patients Found",
                    message = "Add your first patient to get started",
                    action = {
                        GulaButton(
                            onClick = onAddPatient,
                            text = "Add Patient",
                            icon = Icons.Default.PersonAdd,
                        )
                    },
                )
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
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
