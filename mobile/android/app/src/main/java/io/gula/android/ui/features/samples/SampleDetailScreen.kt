package io.gula.android.ui.features.samples

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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SampleDetailScreen(
    barcode: String,
    onBack: () -> Unit,
    viewModel: SamplesViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    var showStatusMenu by remember { mutableStateOf(false) }

    LaunchedEffect(barcode) {
        viewModel.loadSample(barcode)
    }

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Sample Details",
                onBackClick = onBack,
            )
        },
    ) { padding ->
        when {
            uiState.isLoading -> GulaLoadingIndicator(modifier = Modifier.padding(padding))
            uiState.selectedSample == null -> GulaErrorView(message = uiState.error ?: "Sample not found", modifier = Modifier.padding(padding))
            else -> {
                val sample = uiState.selectedSample!!
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    GulaCard {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.QrCodeScanner, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(32.dp))
                                Spacer(Modifier.width(12.dp))
                                Column {
                                    Text(sample.barcode, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                                    Text(sample.sampleType, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                }
                            }
                        }
                    }

                    GulaCard {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text("Status", style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(8.dp))
                            GulaStatusBadge(
                                text = sample.status,
                                color = when (sample.status) {
                                    "collected" -> MaterialTheme.colorScheme.tertiary
                                    "received" -> MaterialTheme.colorScheme.secondary
                                    "processing" -> MaterialTheme.colorScheme.primary
                                    "analyzed" -> MaterialTheme.colorScheme.primary
                                    "rejected" -> MaterialTheme.colorScheme.error
                                    else -> MaterialTheme.colorScheme.onSurfaceVariant
                                },
                            )
                        }
                    }

                    GulaCard {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text("Details", style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(8.dp))
                            if (sample.collectedBy != null) DetailRow("Collected By", sample.collectedBy)
                            if (sample.collectionTime != null) DetailRow("Collection Time", sample.collectionTime)
                            if (sample.storageLocation != null) DetailRow("Storage Location", sample.storageLocation)
                            if (sample.notes != null) DetailRow("Notes", sample.notes)
                        }
                    }

                    Spacer(Modifier.weight(1f))

                    if (sample.status != "rejected") {
                        ExposedDropdownMenuBox(
                            expanded = showStatusMenu,
                            onExpandedChange = { showStatusMenu = !showStatusMenu },
                        ) {
                            GulaButton(
                                onClick = { showStatusMenu = true },
                                text = "Update Status",
                                icon = Icons.Default.Edit,
                                modifier = Modifier.fillMaxWidth(),
                            )
                            ExposedDropdownMenu(
                                expanded = showStatusMenu,
                                onDismissRequest = { showStatusMenu = false },
                            ) {
                                DropdownMenuItem(text = { Text("Received") }, onClick = { viewModel.updateSample(barcode, "received"); showStatusMenu = false })
                                DropdownMenuItem(text = { Text("Processing") }, onClick = { viewModel.updateSample(barcode, "processing"); showStatusMenu = false })
                                DropdownMenuItem(text = { Text("Analyzed") }, onClick = { viewModel.updateSample(barcode, "analyzed"); showStatusMenu = false })
                                DropdownMenuItem(text = { Text("Rejected") }, onClick = { viewModel.updateSample(barcode, "rejected"); showStatusMenu = false })
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun DetailRow(label: String, value: String) {
    Row(modifier = Modifier.padding(vertical = 4.dp)) {
        Text("$label: ", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value, style = MaterialTheme.typography.bodyMedium)
    }
}
