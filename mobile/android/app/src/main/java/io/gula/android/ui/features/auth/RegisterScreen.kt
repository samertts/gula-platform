package io.gula.android.ui.features.auth

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
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.GulaButton
import io.gula.android.ui.components.core.GulaTextField

@Composable
fun RegisterScreen(
    onRegisterSuccess: () -> Unit,
    onBack: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    var isLab by remember { mutableStateOf(true) }
    var labName by remember { mutableStateOf("") }
    var adminName by remember { mutableStateOf("") }
    var staffName by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }
    var showPassword by remember { mutableStateOf(false) }

    LaunchedEffect(uiState.isLoggedIn) {
        if (!uiState.isLoading && uiState.error == null && uiState.isLoggedIn) {
            onRegisterSuccess()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(16.dp))

        Text(
            text = "Create Account",
            style = MaterialTheme.typography.headlineLarge,
        )
        Spacer(Modifier.height(24.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
        ) {
            FilterChip(
                selected = isLab,
                onClick = { isLab = true },
                label = { Text("Lab") },
                modifier = Modifier.padding(end = 8.dp),
            )
            FilterChip(
                selected = !isLab,
                onClick = { isLab = false },
                label = { Text("Staff") },
            )
        }

        Spacer(Modifier.height(24.dp))

        if (isLab) {
            GulaTextField(
                value = labName,
                onValueChange = { labName = it },
                label = "Lab Name",
                leadingIcon = Icons.Default.Business,
                imeAction = ImeAction.Next,
            )
            Spacer(Modifier.height(12.dp))
            GulaTextField(
                value = adminName,
                onValueChange = { adminName = it },
                label = "Admin Name",
                leadingIcon = Icons.Default.Person,
                imeAction = ImeAction.Next,
            )
        } else {
            GulaTextField(
                value = staffName,
                onValueChange = { staffName = it },
                label = "Full Name",
                leadingIcon = Icons.Default.Person,
                imeAction = ImeAction.Next,
            )
        }

        Spacer(Modifier.height(12.dp))
        GulaTextField(
            value = email,
            onValueChange = { email = it },
            label = "Email",
            leadingIcon = Icons.Default.Email,
            keyboardType = KeyboardType.Email,
            imeAction = ImeAction.Next,
        )

        Spacer(Modifier.height(12.dp))
        GulaTextField(
            value = password,
            onValueChange = { password = it },
            label = "Password",
            leadingIcon = Icons.Default.Lock,
            trailingIcon = if (showPassword) Icons.Default.VisibilityOff else Icons.Default.Visibility,
            onTrailingIconClick = { showPassword = !showPassword },
            visualTransformation = if (showPassword) VisualTransformation.None else PasswordVisualTransformation(),
            keyboardType = KeyboardType.Password,
            imeAction = ImeAction.Next,
        )

        Spacer(Modifier.height(12.dp))
        GulaTextField(
            value = confirmPassword,
            onValueChange = { confirmPassword = it },
            label = "Confirm Password",
            leadingIcon = Icons.Default.Lock,
            visualTransformation = PasswordVisualTransformation(),
            keyboardType = KeyboardType.Password,
            imeAction = ImeAction.Done,
        )

        if (uiState.error != null) {
            Spacer(Modifier.height(8.dp))
            Text(
                text = uiState.error.orEmpty(),
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth(),
            )
        }

        Spacer(Modifier.height(24.dp))

        GulaButton(
            onClick = {
                if (password != confirmPassword) return@GulaButton
                if (isLab) {
                    viewModel.registerLab(labName, adminName, email, password)
                } else {
                    viewModel.registerStaff(staffName, email, password, null)
                }
            },
            text = "Create Account",
            loading = uiState.isLoading,
            modifier = Modifier.fillMaxWidth(),
        )

        Spacer(Modifier.height(16.dp))
        TextButton(onClick = onBack) {
            Text("Already have an account? Sign In")
        }
    }
}
