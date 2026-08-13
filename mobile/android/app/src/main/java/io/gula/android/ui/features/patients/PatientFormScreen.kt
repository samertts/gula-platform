package io.gula.android.ui.features.patients

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
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
import io.gula.android.ui.components.core.GulaButton
import io.gula.android.ui.components.core.GulaTextField
import io.gula.android.ui.components.core.GulaTopBar

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PatientFormScreen(
    patientId: Int?,
    onBack: () -> Unit,
    onSaved: () -> Unit,
    viewModel: PatientsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    val isEditing = patientId != null

    var fullName by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var birthDate by remember { mutableStateOf("") }
    var nationalId by remember { mutableStateOf("") }
    var gender by remember { mutableStateOf<String?>(null) }
    var genderExpanded by remember { mutableStateOf(false) }

    LaunchedEffect(patientId) {
        if (patientId != null) viewModel.loadPatient(patientId)
    }

    LaunchedEffect(uiState.selectedPatient) {
        if (isEditing && uiState.selectedPatient != null) {
            val p = uiState.selectedPatient!!
            fullName = p.fullName
            phone = p.phone
            email = p.email ?: ""
            birthDate = p.birthDate ?: ""
            nationalId = p.nationalId ?: ""
            gender = p.gender
        }
    }

    LaunchedEffect(uiState.saveSuccess) {
        if (uiState.saveSuccess) {
            viewModel.resetSaveState()
            onSaved()
        }
    }

    Scaffold(
        topBar = {
            GulaTopBar(
                title = if (isEditing) "Edit Patient" else "New Patient",
                onBackClick = onBack,
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
        ) {
            GulaTextField(
                value = fullName,
                onValueChange = { fullName = it },
                label = "Full Name",
                leadingIcon = Icons.Default.Person,
                imeAction = ImeAction.Next,
            )
            Spacer(Modifier.height(12.dp))

            GulaTextField(
                value = phone,
                onValueChange = { phone = it },
                label = "Phone",
                leadingIcon = Icons.Default.Phone,
                keyboardType = KeyboardType.Phone,
                imeAction = ImeAction.Next,
            )
            Spacer(Modifier.height(12.dp))

            GulaTextField(
                value = email,
                onValueChange = { email = it },
                label = "Email (optional)",
                leadingIcon = Icons.Default.Email,
                keyboardType = KeyboardType.Email,
                imeAction = ImeAction.Next,
            )
            Spacer(Modifier.height(12.dp))

            GulaTextField(
                value = birthDate,
                onValueChange = { birthDate = it },
                label = "Birth Date (YYYY-MM-DD)",
                leadingIcon = Icons.Default.CalendarMonth,
                imeAction = ImeAction.Next,
            )
            Spacer(Modifier.height(12.dp))

            ExposedDropdownMenuBox(
                expanded = genderExpanded,
                onExpandedChange = { genderExpanded = !genderExpanded },
            ) {
                OutlinedTextField(
                    value = gender?.let { if (it == "M") "Male" else "Female" } ?: "",
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Gender") },
                    leadingIcon = { Icon(Icons.Default.Wc, contentDescription = null) },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = genderExpanded) },
                    modifier = Modifier.fillMaxWidth().menuAnchor(),
                )
                ExposedDropdownMenu(
                    expanded = genderExpanded,
                    onDismissRequest = { genderExpanded = false },
                ) {
                    DropdownMenuItem(
                        text = { Text("Male") },
                        onClick = { gender = "M"; genderExpanded = false },
                    )
                    DropdownMenuItem(
                        text = { Text("Female") },
                        onClick = { gender = "F"; genderExpanded = false },
                    )
                }
            }

            if (!isEditing) {
                Spacer(Modifier.height(12.dp))
                GulaTextField(
                    value = nationalId,
                    onValueChange = { nationalId = it },
                    label = "National ID (optional)",
                    leadingIcon = Icons.Default.Badge,
                    imeAction = ImeAction.Done,
                )
            }

            if (uiState.error != null) {
                Spacer(Modifier.height(8.dp))
                Text(
                    text = uiState.error.orEmpty(),
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall,
                )
            }

            Spacer(Modifier.height(24.dp))

            GulaButton(
                onClick = {
                    if (isEditing && patientId != null) {
                        viewModel.updatePatient(patientId, fullName, phone, email.ifBlank { null })
                    } else {
                        viewModel.createPatient(
                            fullName = fullName,
                            phone = phone,
                            birthDate = birthDate.ifBlank { null },
                            gender = gender,
                            email = email.ifBlank { null },
                            nationalId = nationalId.ifBlank { null },
                        )
                    }
                },
                text = if (isEditing) "Update Patient" else "Create Patient",
                loading = uiState.isSaving,
                modifier = Modifier.fillMaxWidth(),
                enabled = fullName.isNotBlank() && phone.isNotBlank(),
            )
        }
    }
}
