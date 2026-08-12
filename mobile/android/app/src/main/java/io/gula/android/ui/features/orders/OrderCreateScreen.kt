package io.gula.android.ui.features.orders

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.domain.model.ResultItemInput
import io.gula.android.ui.components.core.GulaButton
import io.gula.android.ui.components.core.GulaCard
import io.gula.android.ui.components.core.GulaTextField
import io.gula.android.ui.components.core.GulaTopBar

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrderCreateScreen(
    preselectedPatientId: Int?,
    onBack: () -> Unit,
    onOrderCreated: () -> Unit,
    viewModel: OrdersViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    var selectedPatientId by remember { mutableStateOf(preselectedPatientId) }
    var doctorName by remember { mutableStateOf("") }
    var patientSearch by remember { mutableStateOf("") }
    var testItems by remember { mutableStateOf(listOf<ResultItemInput>()) }
    var showPatientDropdown by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        viewModel.loadPatients()
    }

    LaunchedEffect(uiState.saveSuccess) {
        if (uiState.saveSuccess) {
            viewModel.resetSaveState()
            onOrderCreated()
        }
    }

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "New Order",
                onBackClick = onBack,
            )
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
                Text("Select Patient", style = MaterialTheme.typography.titleMedium)
                ExposedDropdownMenuBox(
                    expanded = showPatientDropdown && uiState.availablePatients.isNotEmpty(),
                    onExpandedChange = { showPatientDropdown = !showPatientDropdown },
                ) {
                    OutlinedTextField(
                        value = uiState.availablePatients.find { it.id == selectedPatientId }?.fullName ?: "",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Patient") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = showPatientDropdown) },
                        leadingIcon = { Icon(Icons.Default.Person, contentDescription = null) },
                        modifier = Modifier.fillMaxWidth().menuAnchor(),
                        enabled = preselectedPatientId == null,
                    )
                    ExposedDropdownMenu(
                        expanded = showPatientDropdown && uiState.availablePatients.isNotEmpty(),
                        onDismissRequest = { showPatientDropdown = false },
                    ) {
                        uiState.availablePatients.forEach { patient ->
                            DropdownMenuItem(
                                text = { Text("${patient.fullName} (${patient.phone})") },
                                onClick = {
                                    selectedPatientId = patient.id
                                    showPatientDropdown = false
                                },
                            )
                        }
                    }
                }
            }

            item {
                GulaTextField(
                    value = doctorName,
                    onValueChange = { doctorName = it },
                    label = "Doctor Name (optional)",
                    leadingIcon = Icons.Default.MedicalServices,
                    imeAction = ImeAction.Next,
                )
            }

            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("Test Items", style = MaterialTheme.typography.titleMedium)
                    TextButton(onClick = {
                        testItems = testItems + ResultItemInput(testName = "")
                    }) {
                        Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(4.dp))
                        Text("Add Test")
                    }
                }
            }

            itemsIndexed(testItems) { index, item ->
                TestItemRow(
                    item = item,
                    onUpdate = { updated ->
                        testItems = testItems.toMutableList().apply { set(index, updated) }
                    },
                    onRemove = {
                        testItems = testItems.toMutableList().apply { removeAt(index) }
                    },
                )
            }

            if (uiState.error != null) {
                item {
                    Text(uiState.error.orEmpty(), color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                }
            }

            item {
                Spacer(Modifier.height(16.dp))
                GulaButton(
                    onClick = {
                        val validItems = testItems.filter { it.testName.isNotBlank() }
                        if (selectedPatientId != null && validItems.isNotEmpty()) {
                            viewModel.createOrder(
                                patientId = selectedPatientId!!,
                                doctorName = doctorName.ifBlank { null },
                                testItems = validItems,
                            )
                        }
                    },
                    text = "Create Order",
                    loading = uiState.isSaving,
                    modifier = Modifier.fillMaxWidth(),
                    enabled = selectedPatientId != null && testItems.any { it.testName.isNotBlank() },
                )
            }
        }
    }
}

@Composable
private fun TestItemRow(
    item: ResultItemInput,
    onUpdate: (ResultItemInput) -> Unit,
    onRemove: () -> Unit,
) {
    GulaCard {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
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
