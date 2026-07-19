package io.gula.android.ui.features.results

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
import io.gula.android.ui.components.result.CriticalValueBanner
import io.gula.android.ui.components.result.ResultCard

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultListScreen(
    onResultClick: (Int) -> Unit,
    onEntry: () -> Unit,
    viewModel: ResultsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Results",
                actions = {
                    IconButton(onClick = { viewModel.refresh() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                },
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = onEntry,
                icon = { Icon(Icons.Default.EditNote, contentDescription = null) },
                text = { Text("Enter Results") },
            )
        },
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            if (uiState.criticalAlerts.isNotEmpty()) {
                item {
                    Text("Critical Alerts", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.error)
                    Spacer(Modifier.height(8.dp))
                }
                items(uiState.criticalAlerts.take(3)) { alert ->
                    CriticalValueBanner(
                        alert = alert,
                        onAcknowledge = { viewModel.acknowledgeCriticalAlert(alert.id) },
                    )
                    Spacer(Modifier.height(4.dp))
                }
                item { Spacer(Modifier.height(8.dp)) }
            }

            if (uiState.isLoading && uiState.results.isEmpty()) {
                item { GulaLoadingIndicator() }
            } else if (uiState.results.isEmpty()) {
                item {
                    GulaEmptyState(
                        title = "No Results",
                        message = "Enter test results to get started",
                        action = { GulaButton(onClick = onEntry, text = "Enter Results", icon = Icons.Default.EditNote) },
                    )
                }
            } else {
                item {
                    Text("All Results", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                }
                items(uiState.results, key = { it.id }) { result ->
                    ResultCard(result = result, onClick = { onResultClick(result.id) })
                    Spacer(Modifier.height(4.dp))
                }
            }
        }
    }
}
