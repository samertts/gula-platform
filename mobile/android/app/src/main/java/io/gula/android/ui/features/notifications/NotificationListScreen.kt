package io.gula.android.ui.features.notifications

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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.*
import io.gula.android.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NotificationListScreen(
    onBack: () -> Unit,
    viewModel: NotificationsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Notifications",
                onBackClick = onBack,
                actions = {
                    if (uiState.unreadCount > 0) {
                        IconButton(onClick = { viewModel.markAllAsRead() }) {
                            Icon(Icons.Default.DoneAll, contentDescription = "Mark all read")
                        }
                    }
                    IconButton(onClick = { viewModel.refresh() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                },
            )
        },
    ) { padding ->
        if (uiState.isLoading && uiState.notifications.isEmpty()) {
            GulaLoadingIndicator(modifier = Modifier.padding(padding))
        } else if (uiState.notifications.isEmpty()) {
            GulaEmptyState(
                title = "No Notifications",
                message = "You're all caught up!",
                modifier = Modifier.padding(padding),
            )
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                items(uiState.notifications, key = { it.id }) { notification ->
                    GulaCard(
                        onClick = { if (!notification.read) viewModel.markAsRead(notification.id) },
                        colors = CardDefaults.cardColors(
                            containerColor = if (notification.read) MaterialTheme.colorScheme.surface
                            else MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f)
                        ),
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Icon(
                                imageVector = when (notification.type) {
                                    "critical" -> Icons.Default.Warning
                                    "result" -> Icons.Default.Science
                                    "order" -> Icons.Default.Assignment
                                    else -> Icons.Default.Notifications
                                },
                                contentDescription = null,
                                tint = when (notification.type) {
                                    "critical" -> CriticalRed
                                    "result" -> Blue40
                                    "order" -> Orange40
                                    else -> MaterialTheme.colorScheme.onSurfaceVariant
                                },
                                modifier = Modifier.size(24.dp),
                            )
                            Spacer(Modifier.width(12.dp))
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    notification.title,
                                    style = MaterialTheme.typography.titleSmall,
                                    fontWeight = if (notification.read) FontWeight.Normal else FontWeight.SemiBold,
                                )
                                Text(
                                    notification.body,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    maxLines = 2,
                                )
                            }
                            if (!notification.read) {
                                Box(
                                    modifier = Modifier.size(8.dp),
                                ) {
                                    Surface(
                                        modifier = Modifier.size(8.dp),
                                        shape = MaterialTheme.shapes.extraSmall,
                                        color = MaterialTheme.colorScheme.primary,
                                    ) {}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
