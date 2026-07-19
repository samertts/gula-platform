package io.gula.android.ui.components.core

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp

@Composable
fun GulaAlert(
    message: String,
    modifier: Modifier = Modifier,
    type: AlertType = AlertType.INFO,
    title: String? = null,
    onDismiss: (() -> Unit)? = null,
    action: AlertAction? = null,
) {
    val colors = type.colors()
    val icon = type.icon()
    val bgColor = type.backgroundColor()

    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.small,
        color = bgColor,
        tonalElevation = 0.dp,
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = colors.first,
                modifier = Modifier.size(20.dp),
            )
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                if (title != null) {
                    Text(
                        text = title,
                        style = MaterialTheme.typography.titleSmall,
                        color = colors.first,
                    )
                    Spacer(Modifier.height(2.dp))
                }
                Text(
                    text = message,
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.second,
                )
            }
            if (action != null) {
                Spacer(Modifier.width(8.dp))
                TextButton(onClick = action.onClick) {
                    Text(action.label, color = colors.first)
                }
            }
            if (onDismiss != null) {
                IconButton(onClick = onDismiss, modifier = Modifier.size(20.dp)) {
                    Icon(Icons.Default.Close, "Dismiss", tint = colors.second, modifier = Modifier.size(16.dp))
                }
            }
        }
    }
}

data class AlertAction(val label: String, val onClick: () -> Unit)

enum class AlertType {
    SUCCESS, ERROR, WARNING, INFO;

    fun icon(): ImageVector = when (this) {
        SUCCESS -> Icons.Default.CheckCircle
        ERROR -> Icons.Default.Error
        WARNING -> Icons.Default.Warning
        INFO -> Icons.Default.Info
    }

    fun colors(): Pair<Color, Color> = when (this) {
        SUCCESS -> MaterialTheme.colorScheme.primary to MaterialTheme.colorScheme.onSurface
        ERROR -> MaterialTheme.colorScheme.error to MaterialTheme.colorScheme.onSurface
        WARNING -> Color(0xFFF57C00) to Color(0xFF5C3F00)
        INFO -> MaterialTheme.colorScheme.secondary to MaterialTheme.colorScheme.onSurface
    }

    fun backgroundColor(): Color = when (this) {
        SUCCESS -> MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f)
        ERROR -> MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.3f)
        WARNING -> Color(0xFFFFF0E0)
        INFO -> MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.3f)
    }
}
