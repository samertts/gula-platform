package io.gula.android.ui.features.auth

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Security
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.GulaButton
import io.gula.android.ui.components.core.GulaTextField

@Composable
fun MfaScreen(
    sessionId: String,
    onVerified: () -> Unit,
    onBack: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    var code by remember { mutableStateOf("") }

    LaunchedEffect(uiState.isLoggedIn) {
        if (uiState.isLoggedIn) onVerified()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Icon(
            imageVector = Icons.Default.Security,
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.primary,
        )
        Spacer(Modifier.height(16.dp))
        Text(
            text = "Two-Factor Authentication",
            style = MaterialTheme.typography.headlineMedium,
        )
        Spacer(Modifier.height(8.dp))
        Text(
            text = "Enter the verification code sent to your device",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )

        Spacer(Modifier.height(32.dp))

        GulaTextField(
            value = code,
            onValueChange = { code = it.take(6) },
            label = "Verification Code",
            placeholder = "000000",
            keyboardType = KeyboardType.Number,
            imeAction = ImeAction.Done,
        )

        if (uiState.error != null) {
            Spacer(Modifier.height(8.dp))
            Text(
                text = uiState.error,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
            )
        }

        Spacer(Modifier.height(24.dp))

        GulaButton(
            onClick = { viewModel.verifyMfa(code, sessionId) },
            text = "Verify",
            loading = uiState.isLoading,
            modifier = Modifier.fillMaxWidth(),
        )

        Spacer(Modifier.height(16.dp))

        TextButton(onClick = onBack) {
            Text("Back to Login")
        }
    }
}
