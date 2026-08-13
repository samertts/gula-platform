package io.gula.android.ui.features.dashboard

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.*
import io.gula.android.ui.components.offline.SyncStatusIndicator
import io.gula.android.ui.theme.*

data class KpiCard(
    val title: String,
    val value: String,
    val icon: ImageVector,
    val color: Color,
    val onClick: () -> Unit,
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    onNavigateToPatients: () -> Unit,
    onNavigateToOrders: () -> Unit,
    onNavigateToResults: () -> Unit,
    onNavigateToSamples: () -> Unit,
    onNavigateToNotifications: () -> Unit,
    viewModel: DashboardViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    val scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior()

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Dashboard",
                actions = {
                    IconButton(onClick = { viewModel.refresh() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                },
                scrollBehavior = scrollBehavior,
            )
        },
    ) { padding ->
        if (uiState.isLoading) {
            GulaLoadingIndicator(message = "Loading dashboard...")
        } else if (uiState.error != null && uiState.stats.patientsCount == 0) {
            GulaErrorView(
                message = uiState.error.orEmpty(),
                onRetry = { viewModel.refresh() },
                modifier = Modifier.padding(padding),
            )
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                item {
                    Text(
                        text = "Overview",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                    )
                }

                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        KpiCard(
                            modifier = Modifier.weight(1f),
                            title = "Patients",
                            value = uiState.stats.patientsCount.toString(),
                            icon = Icons.Default.People,
                            color = Green40,
                            onClick = onNavigateToPatients,
                        )
                        KpiCard(
                            modifier = Modifier.weight(1f),
                            title = "Orders Today",
                            value = uiState.stats.ordersToday.toString(),
                            icon = Icons.Default.Assignment,
                            color = Blue40,
                            onClick = onNavigateToOrders,
                        )
                    }
                }

                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        KpiCard(
                            modifier = Modifier.weight(1f),
                            title = "Pending Results",
                            value = uiState.stats.pendingResults.toString(),
                            icon = Icons.Default.Science,
                            color = Orange40,
                            onClick = onNavigateToResults,
                        )
                        KpiCard(
                            modifier = Modifier.weight(1f),
                            title = "Samples Today",
                            value = uiState.stats.samplesToday.toString(),
                            icon = Icons.Default.Biotech,
                            color = ChartTeal,
                            onClick = onNavigateToSamples,
                        )
                    }
                }

                if (uiState.stats.criticalAlerts > 0) {
                    item {
                        Spacer(Modifier.height(8.dp))
                        GulaAlert(
                            message = "There are ${uiState.stats.criticalAlerts} critical alerts requiring attention",
                            type = AlertType.ERROR,
                            title = "Critical Alerts",
                            action = AlertAction("View", onNavigateToNotifications),
                        )
                    }
                }

                item {
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = "Quick Actions",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                    )
                }

                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        QuickActionCard(
                            modifier = Modifier.weight(1f),
                            title = "New Patient",
                            icon = Icons.Default.PersonAdd,
                            onClick = onNavigateToPatients,
                        )
                        QuickActionCard(
                            modifier = Modifier.weight(1f),
                            title = "New Order",
                            icon = Icons.Default.PostAdd,
                            onClick = onNavigateToOrders,
                        )
                    }
                }

                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        QuickActionCard(
                            modifier = Modifier.weight(1f),
                            title = "Collect Sample",
                            icon = Icons.Default.Biotech,
                            onClick = onNavigateToSamples,
                        )
                        QuickActionCard(
                            modifier = Modifier.weight(1f),
                            title = "Enter Results",
                            icon = Icons.Default.EditNote,
                            onClick = onNavigateToResults,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun KpiCard(
    modifier: Modifier = Modifier,
    title: String,
    value: String,
    icon: ImageVector,
    color: Color,
    onClick: () -> Unit,
) {
    GulaCard(
        onClick = onClick,
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.08f)),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = color,
                modifier = Modifier.size(28.dp),
            )
            Spacer(Modifier.height(8.dp))
            Text(
                text = value,
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = color,
            )
            Text(
                text = title,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun QuickActionCard(
    modifier: Modifier = Modifier,
    title: String,
    icon: ImageVector,
    onClick: () -> Unit,
) {
    GulaCard(
        onClick = onClick,
        modifier = modifier,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(32.dp),
            )
            Spacer(Modifier.height(8.dp))
            Text(
                text = title,
                style = MaterialTheme.typography.labelLarge,
            )
        }
    }
}
