package io.gula.android.ui.features.results

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.domain.model.ResultValidation
import io.gula.android.ui.components.core.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultValidationScreen(
    resultId: Int,
    onBack: () -> Unit,
    onValidated: () -> Unit,
    viewModel: ResultsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    var testName by remember { mutableStateOf("") }
    var testCode by remember { mutableStateOf("") }
    var value by remember { mutableStateOf("") }

    LaunchedEffect(resultId) {
        viewModel.loadResult(resultId)
    }

    LaunchedEffect(uiState.selectedResult) {
        uiState.selectedResult?.let { r ->
            testName = r.testNameEn
            testCode = r.testCode
            value = r.resultValue?.toString() ?: ""
        }
    }

    LaunchedEffect(uiState.saveSuccess) {
        if (uiState.saveSuccess) onValidated()
    }

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Validate Result",
                onBackClick = onBack,
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                "Review and validate this test result",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(8.dp))

            GulaTextField(
                value = testName,
                onValueChange = { testName = it },
                label = "Test Name",
                leadingIcon = Icons.Default.Science,
            )
            GulaTextField(
                value = testCode,
                onValueChange = { testCode = it },
                label = "Test Code",
                leadingIcon = Icons.Default.Code,
            )
            GulaTextField(
                value = value,
                onValueChange = { value = it },
                label = "Value",
                leadingIcon = Icons.Default.Pin,
                keyboardType = KeyboardType.Decimal,
            )

            if (uiState.error != null) {
                Text(uiState.error.orEmpty(), color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            }

            if (uiState.validationMessage != null) {
                Text(uiState.validationMessage.orEmpty(), color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold)
            }

            Spacer(Modifier.weight(1f))

            GulaButton(
                onClick = {
                    viewModel.validateResult(
                        resultId,
                        ResultValidation(
                            testName = testName,
                            testCode = testCode.ifBlank { null },
                            value = value.toDoubleOrNull(),
                        ),
                    )
                },
                text = "Validate Result",
                loading = uiState.isSaving,
                icon = Icons.Default.CheckCircle,
                modifier = Modifier.fillMaxWidth(),
                enabled = testName.isNotBlank(),
            )
        }
    }
}
