package io.gula.android.ui.features.auth

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.GulaButton
import io.gula.android.ui.components.core.GulaButtonVariant
import io.gula.android.ui.components.core.GulaTextField

@Composable
fun LoginScreen(
    onLoginSuccess: () -> Unit,
    onMfaRequired: (String) -> Unit,
    onRegister: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var showPassword by remember { mutableStateOf(false) }
    var emailError by remember { mutableStateOf<String?>(null) }
    var passwordError by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(uiState.isLoggedIn) {
        if (uiState.isLoggedIn) onLoginSuccess()
    }
    LaunchedEffect(uiState.mfaRequired) {
        if (uiState.mfaRequired) onMfaRequired(uiState.mfaSessionId)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Spacer(Modifier.height(48.dp))

        Icon(
            imageVector = Icons.Default.MedicalServices,
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.primary,
        )
        Spacer(Modifier.height(16.dp))
        Text(
            text = "GULA Platform",
            style = MaterialTheme.typography.headlineLarge,
            color = MaterialTheme.colorScheme.primary,
        )
        Text(
            text = "Medical Laboratory Management",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Spacer(Modifier.height(48.dp))

        GulaTextField(
            value = email,
            onValueChange = { email = it; emailError = null; viewModel.clearError() },
            label = "Email",
            placeholder = "Enter your email",
            leadingIcon = Icons.Default.Email,
            keyboardType = KeyboardType.Email,
            imeAction = ImeAction.Next,
            error = emailError,
        )
        Spacer(Modifier.height(16.dp))

        GulaTextField(
            value = password,
            onValueChange = { password = it; passwordError = null; viewModel.clearError() },
            label = "Password",
            placeholder = "Enter your password",
            leadingIcon = Icons.Default.Lock,
            trailingIcon = if (showPassword) Icons.Default.VisibilityOff else Icons.Default.Visibility,
            onTrailingIconClick = { showPassword = !showPassword },
            visualTransformation = if (showPassword) VisualTransformation.None else PasswordVisualTransformation(),
            keyboardType = KeyboardType.Password,
            imeAction = ImeAction.Done,
            error = passwordError,
        )

        if (uiState.error != null) {
            Spacer(Modifier.height(8.dp))
            Text(
                text = uiState.error,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth(),
            )
        }

        Spacer(Modifier.height(24.dp))

        GulaButton(
            onClick = { viewModel.login(email, password) },
            text = "Sign In",
            loading = uiState.isLoading,
            modifier = Modifier.fillMaxWidth(),
        )

        if (uiState.biometricAvailable) {
            Spacer(Modifier.height(12.dp))
            GulaButton(
                onClick = { viewModel.loginWithBiometric() },
                text = "Login with Biometrics",
                variant = GulaButtonVariant.OUTLINE,
                icon = Icons.Default.Fingerprint,
                modifier = Modifier.fillMaxWidth(),
            )
        }

        Spacer(Modifier.height(24.dp))

        TextButton(onClick = onRegister) {
            Text("Create New Account")
        }

        Spacer(Modifier.height(16.dp))

        Text(
            text = "v1.0.0",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
