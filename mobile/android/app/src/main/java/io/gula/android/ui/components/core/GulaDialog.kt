package io.gula.android.ui.components.core

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector

@Composable
fun GulaDialog(
    show: Boolean,
    onDismiss: () -> Unit,
    title: String = "",
    text: String = "",
    confirmText: String = "Confirm",
    dismissText: String = "Cancel",
    icon: ImageVector? = null,
    onConfirm: (() -> Unit)? = null,
    onDismissButton: (() -> Unit)? = null,
    confirmEnabled: Boolean = true,
    confirmLoading: Boolean = false,
) {
    if (show) {
        AlertDialog(
            onDismissRequest = onDismiss,
            icon = icon?.let { { Icon(it, contentDescription = null) } },
            title = if (title.isNotBlank()) { @Composable { Text(title) } } else null,
            text = if (text.isNotBlank()) { @Composable { Text(text) } } else null,
            confirmButton = {
                onConfirm?.let { confirm ->
                    GulaButton(
                        onClick = confirm,
                        text = confirmText,
                        loading = confirmLoading,
                        enabled = confirmEnabled,
                        variant = ButtonVariant.PRIMARY,
                    )
                }
            },
            dismissButton = {
                TextButton(onClick = onDismissButton ?: onDismiss) {
                    Text(dismissText)
                }
            },
        )
    }
}
