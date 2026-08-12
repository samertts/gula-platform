package io.gula.android.ui.features.samples

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
import io.gula.android.ui.components.sample.SampleCard

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SampleListScreen(
    onSampleClick: (String) -> Unit,
    onCollect: () -> Unit,
    viewModel: SamplesViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Samples",
                actions = {
                    IconButton(onClick = { viewModel.refresh() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                },
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = onCollect,
                icon = { Icon(Icons.Default.QrCodeScanner, contentDescription = null) },
                text = { Text("Collect Sample") },
            )
        },
    ) { padding ->
        if (uiState.isLoading && uiState.samples.isEmpty()) {
            GulaLoadingIndicator(modifier = Modifier.padding(padding))
        } else if (uiState.samples.isEmpty()) {
            GulaEmptyState(
                title = "No Samples",
                message = "Collect your first sample to get started",
                action = {
                    GulaButton(onClick = onCollect, text = "Collect Sample", icon = Icons.Default.QrCodeScanner)
                },
                modifier = Modifier.padding(padding),
            )
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                items(uiState.samples, key = { it.id }) { sample ->
                    SampleCard(sample = sample, onClick = { onSampleClick(sample.barcode) })
                }
            }
        }
    }
}
