package io.gula.android.ui.features.results

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultEntryScreen(
    orderId: Int?,
    onBack: () -> Unit,
    onSaved: () -> Unit,
    viewModel: ResultsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    var entryOrderId by remember { mutableStateOf(orderId?.toString() ?: "") }
    var results by remember { mutableStateOf(listOf(ResultEntryItem())) }

    LaunchedEffect(uiState.saveSuccess) {
        if (uiState.saveSuccess) {
            viewModel.refresh()
            onSaved()
        }
    }

    Scaffold(
        topBar = {
            GulaTopBar(title = "Enter Results", onBackClick = onBack)
        },
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                if (orderId == null) {
                    GulaTextField(
                        value = entryOrderId,
                        onValueChange = { entryOrderId = it },
                        label = "Order ID",
                        leadingIcon = Icons.Default.Assignment,
                        keyboardType = KeyboardType.Number,
                    )
                    Spacer(Modifier.height(8.dp))
                }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text("Test Results", style = MaterialTheme.typography.titleMedium)
                    TextButton(onClick = { results = results + ResultEntryItem() }) {
                        Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(4.dp))
                        Text("Add")
                    }
                }
            }

            itemsIndexed(results) { index, item ->
                ResultEntryRow(
                    item = item,
                    onUpdate = { updated -> results = results.toMutableList().apply { set(index, updated) } },
                    onRemove = { results = results.toMutableList().apply { removeAt(index) } },
                )
            }

            if (uiState.error != null) {
                item { Text(uiState.error.orEmpty(), color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall) }
            }

            item {
                Spacer(Modifier.height(16.dp))
                GulaButton(
                    onClick = {
                        val validResults = results.filter { it.testName.isNotBlank() }
                        validResults.forEach { r ->
                            viewModel.createResult(
                                testCode = r.testCode.ifBlank { r.testName },
                                testNameEn = r.testName,
                                testNameAr = r.testNameAr.ifBlank { r.testName },
                                resultValue = r.value,
                                resultText = r.valueText?.ifBlank { null },
                                unit = r.unit?.ifBlank { null },
                                orderId = entryOrderId.toIntOrNull(),
                            )
                        }
                    },
                    text = "Save Results",
                    loading = uiState.isSaving,
                    modifier = Modifier.fillMaxWidth(),
                    icon = Icons.Default.Save,
                    enabled = results.any { it.testName.isNotBlank() },
                )
            }
        }
    }
}

data class ResultEntryItem(
    val testName: String = "",
    val testNameAr: String = "",
    val testCode: String = "",
    val value: Double? = null,
    val valueText: String? = null,
    val unit: String? = null,
)

@Composable
private fun ResultEntryRow(
    item: ResultEntryItem,
    onUpdate: (ResultEntryItem) -> Unit,
    onRemove: () -> Unit,
) {
    GulaCard {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                OutlinedTextField(
                    value = item.testName,
                    onValueChange = { onUpdate(item.copy(testName = it)) },
                    label = { Text("Test Name") },
                    modifier = Modifier.weight(1f),
                    singleLine = true,
                )
                IconButton(onClick = onRemove) {
                    Icon(Icons.Default.Close, contentDescription = "Remove", tint = MaterialTheme.colorScheme.error)
                }
            }
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = item.value?.toString() ?: "",
                    onValueChange = { onUpdate(item.copy(value = it.toDoubleOrNull())) },
                    label = { Text("Value") },
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    singleLine = true,
                )
                OutlinedTextField(
                    value = item.unit ?: "",
                    onValueChange = { onUpdate(item.copy(unit = it.ifBlank { null })) },
                    label = { Text("Unit") },
                    modifier = Modifier.weight(1f),
                    singleLine = true,
                )
            }
        }
    }
}
