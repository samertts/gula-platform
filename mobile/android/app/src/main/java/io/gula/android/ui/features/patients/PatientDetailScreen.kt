package io.gula.android.ui.features.patients

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.*
import io.gula.android.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PatientDetailScreen(
    patientId: Int,
    onBack: () -> Unit,
    onEdit: () -> Unit,
    onCreateOrder: () -> Unit,
    viewModel: PatientsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(patientId) {
        viewModel.loadPatient(patientId)
    }

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Patient Details",
                onBackClick = onBack,
                actions = {
                    IconButton(onClick = onEdit) {
                        Icon(Icons.Default.Edit, contentDescription = "Edit")
                    }
                },
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = onCreateOrder,
                icon = { Icon(Icons.Default.PostAdd, contentDescription = null) },
                text = { Text("New Order") },
            )
        },
    ) { padding ->
        when {
            uiState.isLoading -> {
                GulaLoadingIndicator(modifier = Modifier.padding(padding))
            }
            uiState.selectedPatient == null -> {
                GulaErrorView(
                    message = uiState.error ?: "Patient not found",
                    onRetry = { viewModel.loadPatient(patientId) },
                    modifier = Modifier.padding(padding),
                )
            }
            else -> {
                val patient = uiState.selectedPatient!!
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    item {
                        GulaCard {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(
                                        imageVector = if (patient.gender == "M") Icons.Default.Male else Icons.Default.Female,
                                        contentDescription = null,
                                        tint = MaterialTheme.colorScheme.primary,
                                        modifier = Modifier.size(32.dp),
                                    )
                                    Spacer(Modifier.width(12.dp))
                                    Column {
                                        Text(patient.fullName, style = MaterialTheme.typography.headlineSmall)
                                        if (patient.age != null) {
                                            Text("${patient.age} years old", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                        }
                                    }
                                }
                            }
                        }

                        GulaCard {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text("Contact Information", style = MaterialTheme.typography.titleMedium)
                                Spacer(Modifier.height(8.dp))
                                DetailRow(icon = Icons.Default.Phone, label = "Phone", value = patient.phone)
                                if (patient.email != null) DetailRow(icon = Icons.Default.Email, label = "Email", value = patient.email)
                                if (patient.nationalId != null) DetailRow(icon = Icons.Default.Badge, label = "National ID", value = patient.nationalId)
                                if (patient.healthId != null) DetailRow(icon = Icons.Default.HealthAndSafety, label = "Health ID", value = patient.healthId)
                            }
                        }

                        GulaCard {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text("Demographics", style = MaterialTheme.typography.titleMedium)
                                Spacer(Modifier.height(8.dp))
                                if (patient.gender != null) DetailRow(icon = Icons.Default.Wc, label = "Gender", value = if (patient.gender == "M") "Male" else "Female")
                                if (patient.birthDate != null) DetailRow(icon = Icons.Default.CalendarMonth, label = "Birth Date", value = patient.birthDate)
                                if (patient.familyId != null) DetailRow(icon = Icons.Default.FamilyRestroom, label = "Family ID", value = patient.familyId)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun DetailRow(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    value: String,
) {
    Row(
        modifier = Modifier.padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(icon, contentDescription = null, modifier = Modifier.size(18.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.width(12.dp))
        Column {
            Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
