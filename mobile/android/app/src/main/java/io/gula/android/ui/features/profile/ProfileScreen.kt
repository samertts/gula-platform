package io.gula.android.ui.features.profile

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.features.auth.AuthViewModel
import io.gula.android.ui.components.core.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(
    onBack: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            GulaTopBar(title = "Profile", onBackClick = onBack)
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Spacer(Modifier.height(24.dp))

            Icon(
                imageVector = Icons.Default.AccountCircle,
                contentDescription = null,
                modifier = Modifier.size(96.dp),
                tint = MaterialTheme.colorScheme.primary,
            )

            Spacer(Modifier.height(16.dp))

            Text(
                text = uiState.userName.ifBlank { "User" },
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
            )
            Text(
                text = uiState.userEmail,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(Modifier.height(8.dp))

            GulaStatusBadge(
                text = uiState.userRole.replace("_", " ").replaceFirstChar { it.uppercase() },
                color = MaterialTheme.colorScheme.primary,
            )

            Spacer(Modifier.height(32.dp))

            GulaCard {
                Column(modifier = Modifier.padding(4.dp)) {
                    ListItem(
                        headlineContent = { Text("Role") },
                        supportingContent = { Text(uiState.userRole) },
                        leadingContent = { Icon(Icons.Default.Badge, contentDescription = null) },
                    )
                }
            }

            Spacer(Modifier.weight(1f))

            GulaButton(
                onClick = onBack,
                text = "Back",
                variant = GulaButtonVariant.OUTLINE,
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}
