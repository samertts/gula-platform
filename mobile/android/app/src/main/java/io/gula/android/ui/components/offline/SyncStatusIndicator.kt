package io.gula.android.ui.components.offline

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import io.gula.android.domain.model.SyncStatus

@Composable
fun SyncStatusIndicator(
    status: SyncStatus,
    modifier: Modifier = Modifier,
    onSyncNow: (() -> Unit)? = null,
) {
    if (status.isSyncing) {
        Row(
            modifier = modifier.padding(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            CircularProgressIndicator(
                modifier = Modifier.size(16.dp),
                strokeWidth = 2.dp,
            )
            Spacer(Modifier.width(8.dp))
            Text("Syncing...", style = MaterialTheme.typography.bodySmall)
        }
    } else if (status.pendingCount > 0 || status.failedCount > 0) {
        Row(
            modifier = modifier.padding(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                Icons.Default.SyncProblem,
                contentDescription = null,
                tint = if (status.failedCount > 0) Color(0xFFF57C00) else MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(16.dp),
            )
            Spacer(Modifier.width(8.dp))
            Text(
                text = buildString {
                    if (status.pendingCount > 0) append("${status.pendingCount} pending")
                    if (status.pendingCount > 0 && status.failedCount > 0) append(", ")
                    if (status.failedCount > 0) append("${status.failedCount} failed")
                },
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (onSyncNow != null) {
                Spacer(Modifier.width(8.dp))
                TextButton(onClick = onSyncNow) {
                    Text("Sync", style = MaterialTheme.typography.labelSmall)
                }
            }
        }
    } else if (status.lastSyncTime != null) {
        Row(
            modifier = modifier.padding(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                Icons.Default.CheckCircle,
                contentDescription = null,
                tint = Color(0xFF4CAF50),
                modifier = Modifier.size(16.dp),
            )
            Spacer(Modifier.width(8.dp))
            Text(
                text = "Synced",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
