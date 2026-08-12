package io.gula.android.ui.features.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.GulaButton
import io.gula.android.ui.components.core.GulaButtonVariant

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onBack: () -> Unit,
    onNavigateToProfile: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    var languageExpanded by remember { mutableStateOf(false) }
    var darkModeExpanded by remember { mutableStateOf(false) }
    var showLogoutDialog by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            GulaTopBar(title = "Settings", onBackClick = onBack)
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Preferences", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(4.dp))

            GulaCard {
                Column(modifier = Modifier.padding(4.dp)) {
                    ListItem(
                        headlineContent = { Text("Profile") },
                        leadingContent = { Icon(Icons.Default.Person, contentDescription = null) },
                        trailingContent = { Icon(Icons.Default.ChevronRight, contentDescription = null) },
                        modifier = Modifier.clickable { onNavigateToProfile() },
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                    ListItem(
                        headlineContent = { Text("Language") },
                        supportingContent = { Text(if (uiState.locale == "ar") "العربية" else "English") },
                        leadingContent = { Icon(Icons.Default.Language, contentDescription = null) },
                        modifier = Modifier.clickable { languageExpanded = true },
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                    ListItem(
                        headlineContent = { Text("Dark Mode") },
                        supportingContent = { Text(uiState.darkMode.replaceFirstChar { it.uppercase() }) },
                        leadingContent = { Icon(Icons.Default.DarkMode, contentDescription = null) },
                        modifier = Modifier.clickable { darkModeExpanded = true },
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                    ListItem(
                        headlineContent = { Text("Biometric Login") },
                        leadingContent = { Icon(Icons.Default.Fingerprint, contentDescription = null) },
                        trailingContent = {
                            Switch(
                                checked = uiState.biometricEnabled,
                                onCheckedChange = { viewModel.setBiometricEnabled(it) },
                            )
                        },
                    )
                }
            }

            Spacer(Modifier.height(8.dp))
            Text("Sync", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(4.dp))

            GulaCard {
                Column(modifier = Modifier.padding(4.dp)) {
                    ListItem(
                        headlineContent = { Text("Pending items: ${uiState.pendingSync}") },
                        leadingContent = { Icon(Icons.Default.Sync, contentDescription = null) },
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                    ListItem(
                        headlineContent = { Text("Failed items: ${uiState.failedSync}") },
                        leadingContent = { Icon(Icons.Default.Error, contentDescription = null) },
                    )
                    if (uiState.lastSyncTime != null) {
                        HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                        ListItem(
                            headlineContent = { Text("Last synced: ${uiState.lastSyncTime?.take(19)}") },
                            leadingContent = { Icon(Icons.Default.Schedule, contentDescription = null) },
                        )
                    }
                }
            }

            GulaButton(
                onClick = { viewModel.syncNow() },
                text = "Sync Now",
                loading = uiState.isSyncing,
                modifier = Modifier.fillMaxWidth(),
                icon = Icons.Default.Sync,
            )

            Spacer(Modifier.height(16.dp))
            Text("About", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(4.dp))

            GulaCard {
                Column(modifier = Modifier.padding(4.dp)) {
                    ListItem(
                        headlineContent = { Text("Version") },
                        supportingContent = { Text("1.0.0") },
                        leadingContent = { Icon(Icons.Default.Info, contentDescription = null) },
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                    ListItem(
                        headlineContent = { Text("GULA Platform") },
                        supportingContent = { Text("Medical Laboratory Management") },
                        leadingContent = { Icon(Icons.Default.MedicalServices, contentDescription = null) },
                    )
                }
            }

            Spacer(Modifier.height(24.dp))

            GulaButton(
                onClick = { showLogoutDialog = true },
                text = "Sign Out",
                variant = GulaButtonVariant.DANGER,
                modifier = Modifier.fillMaxWidth(),
                icon = Icons.Default.Logout,
            )
        }
    }

    if (languageExpanded) {
        AlertDialog(
            onDismissRequest = { languageExpanded = false },
            title = { Text("Select Language") },
            text = {
                Column {
                    TextButton(onClick = { viewModel.setLocale("ar"); languageExpanded = false }) { Text("العربية") }
                    TextButton(onClick = { viewModel.setLocale("en"); languageExpanded = false }) { Text("English") }
                }
            },
            confirmButton = {},
        )
    }

    if (darkModeExpanded) {
        AlertDialog(
            onDismissRequest = { darkModeExpanded = false },
            title = { Text("Dark Mode") },
            text = {
                Column {
                    TextButton(onClick = { viewModel.setDarkMode("system"); darkModeExpanded = false }) { Text("System") }
                    TextButton(onClick = { viewModel.setDarkMode("light"); darkModeExpanded = false }) { Text("Light") }
                    TextButton(onClick = { viewModel.setDarkMode("dark"); darkModeExpanded = false }) { Text("Dark") }
                }
            },
            confirmButton = {},
        )
    }

    if (showLogoutDialog) {
        AlertDialog(
            onDismissRequest = { showLogoutDialog = false },
            title = { Text("Sign Out") },
            text = { Text("Are you sure you want to sign out?") },
            confirmButton = {
                TextButton(onClick = { viewModel.logout(); showLogoutDialog = false }) { Text("Sign Out") }
            },
            dismissButton = {
                TextButton(onClick = { showLogoutDialog = false }) { Text("Cancel") }
            },
        )
    }
}

private fun Modifier.clickable(onClick: () -> Unit): Modifier = this.then(
    androidx.compose.foundation.clickable(onClick = onClick)
)
