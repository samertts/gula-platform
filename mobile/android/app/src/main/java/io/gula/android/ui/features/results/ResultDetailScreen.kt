package io.gula.android.ui.features.results

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultDetailScreen(
    resultId: Int,
    onBack: () -> Unit,
    viewModel: ResultsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(resultId) {
        viewModel.loadResult(resultId)
    }

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Result Details",
                onBackClick = onBack,
            )
        },
    ) { padding ->
        when {
            uiState.isLoading -> GulaLoadingIndicator(modifier = Modifier.padding(padding))
            uiState.selectedResult == null -> GulaErrorView(message = uiState.error ?: "Result not found", modifier = Modifier.padding(padding))
            else -> {
                val result = uiState.selectedResult!!
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .verticalScroll(rememberScrollState())
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    GulaCard(
                        colors = CardDefaults.cardColors(
                            containerColor = when {
                                result.isCritical -> Color(0xFFFFF0F0)
                                result.isAbnormal -> Color(0xFFFFF8E1)
                                else -> MaterialTheme.colorScheme.surface
                            }
                        ),
                    ) {
                        Column(modifier = Modifier.padding(20.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(result.testNameEn, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                            if (result.testNameAr.isNotBlank()) {
                                Text(result.testNameAr, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            Spacer(Modifier.height(12.dp))
                            Text(
                                text = buildString {
                                    append(result.resultValue?.toString() ?: result.resultText ?: "—")
                                    if (result.unit != null) append(" ${result.unit}")
                                },
                                style = MaterialTheme.typography.displayMedium,
                                fontWeight = FontWeight.Bold,
                                color = when {
                                    result.isCritical -> Color(0xFFD32F2F)
                                    result.isAbnormal -> Color(0xFFF57C00)
                                    else -> MaterialTheme.colorScheme.primary
                                },
                            )
                            if (result.referenceMin != null || result.referenceMax != null) {
                                Spacer(Modifier.height(8.dp))
                                Text(
                                    text = "Reference Range: ${result.referenceMin ?: "—"} — ${result.referenceMax ?: "—"}",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                    }

                    GulaCard {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text("Status", style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(8.dp))
                            GulaStatusBadge(
                                text = result.status,
                                color = when (result.status) {
                                    "pending" -> MaterialTheme.colorScheme.tertiary
                                    "completed" -> MaterialTheme.colorScheme.primary
                                    "validated" -> MaterialTheme.colorScheme.primary
                                    "rejected" -> MaterialTheme.colorScheme.error
                                    else -> MaterialTheme.colorScheme.onSurfaceVariant
                                },
                            )
                            if (result.isCritical) {
                                Spacer(Modifier.height(4.dp))
                                GulaStatusBadge(text = "CRITICAL", color = Color(0xFFD32F2F))
                            } else if (result.isAbnormal) {
                                Spacer(Modifier.height(4.dp))
                                GulaStatusBadge(text = "ABNORMAL", color = Color(0xFFF57C00))
                            }
                        }
                    }

                    GulaCard {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text("Details", style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(8.dp))
                            if (result.testCode.isNotBlank()) DetailRow("Test Code", result.testCode)
                            if (result.category != null) DetailRow("Category", result.category)
                            if (result.sampleBarcode != null) DetailRow("Sample Barcode", result.sampleBarcode)
                            if (result.orderingPhysician != null) DetailRow("Ordering Physician", result.orderingPhysician)
                            if (result.verifiedBy != null) DetailRow("Verified By", result.verifiedBy)
                            if (result.sampleCollectedAt.isNotBlank()) DetailRow("Collected At", result.sampleCollectedAt)
                            if (result.resultCompletedAt != null) DetailRow("Completed At", result.resultCompletedAt)
                            if (result.verifiedAt != null) DetailRow("Verified At", result.verifiedAt)
                        }
                    }

                    if (result.clinicalNotes != null) {
                        GulaCard {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text("Clinical Notes", style = MaterialTheme.typography.titleMedium)
                                Spacer(Modifier.height(4.dp))
                                Text(result.clinicalNotes, style = MaterialTheme.typography.bodyMedium)
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
    Row(modifier = Modifier.padding(vertical = 2.dp)) {
        Text("$label: ", style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Medium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value, style = MaterialTheme.typography.bodyMedium)
    }
}
