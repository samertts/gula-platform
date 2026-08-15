package io.gula.android.ui.features.settings

import androidx.compose.foundation.clickable
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
import io.gula.android.ui.components.core.ButtonVariant
import io.gula.android.ui.components.core.GulaButton
import io.gula.android.ui.components.core.GulaCard
import io.gula.android.ui.components.core.GulaTopBar

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
    var colorBlindExpanded by remember { mutableStateOf(false) }

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
            Text("Accessibility", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(4.dp))

            GulaCard {
                Column(modifier = Modifier.padding(4.dp)) {
                    Text("Text size: ${"%.2f".format(uiState.textScale)}×", modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp), style = MaterialTheme.typography.bodyMedium)
                    Slider(
                        value = uiState.textScale,
                        onValueChange = viewModel::setTextScale,
                        valueRange = 0.85f..2.0f,
                        steps = 22,
                        modifier = Modifier.padding(horizontal = 12.dp),
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                    ListItem(
                        headlineContent = { Text("High contrast") },
                        supportingContent = { Text("Keep status meaning visible beyond color alone") },
                        leadingContent = { Icon(Icons.Default.Contrast, contentDescription = null) },
                        trailingContent = { Switch(checked = uiState.highContrast, onCheckedChange = viewModel::setHighContrast) },
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                    ListItem(
                        headlineContent = { Text("Reduced motion") },
                        supportingContent = { Text("Disable non-essential motion and flashing") },
                        leadingContent = { Icon(Icons.Default.MotionPhotosOff, contentDescription = null) },
                        trailingContent = { Switch(checked = uiState.reducedMotion, onCheckedChange = viewModel::setReducedMotion) },
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                    ListItem(
                        headlineContent = { Text("Screen reader optimized") },
                        supportingContent = { Text("Prefer semantic labels and predictable focus") },
                        leadingContent = { Icon(Icons.Default.RecordVoiceOver, contentDescription = null) },
                        trailingContent = { Switch(checked = uiState.screenReaderOptimized, onCheckedChange = viewModel::setScreenReaderOptimized) },
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                    ListItem(
                        headlineContent = { Text("Larger touch targets") },
                        supportingContent = { Text("Increase interactive target size") },
                        leadingContent = { Icon(Icons.Default.TouchApp, contentDescription = null) },
                        trailingContent = { Switch(checked = uiState.largerTouchTargets, onCheckedChange = viewModel::setLargerTouchTargets) },
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                    ListItem(
                        headlineContent = { Text("Color blind safe palette") },
                        supportingContent = { Text(uiState.colorBlindMode) },
                        leadingContent = { Icon(Icons.Default.Palette, contentDescription = null) },
                        modifier = Modifier.clickable { colorBlindExpanded = true },
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
                variant = ButtonVariant.DANGER,
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

    if (colorBlindExpanded) {
        AlertDialog(
            onDismissRequest = { colorBlindExpanded = false },
            title = { Text("Color blind safe palette") },
            text = {
                Column {
                    listOf("none", "protanopia", "deuteranopia", "tritanopia", "monochrome").forEach { mode ->
                        TextButton(onClick = { viewModel.setColorBlindMode(mode); colorBlindExpanded = false }) { Text(mode) }
                    }
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
