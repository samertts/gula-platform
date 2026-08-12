package io.gula.android.ui.components.core

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp

@Composable
fun GulaButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    text: String = "",
    enabled: Boolean = true,
    loading: Boolean = false,
    icon: ImageVector? = null,
    variant: ButtonVariant = ButtonVariant.PRIMARY,
    colors: ButtonColors? = null,
    contentPadding: PaddingValues = PaddingValues(horizontal = 24.dp, vertical = 14.dp),
) {
    val buttonColors = colors ?: when (variant) {
        ButtonVariant.PRIMARY -> ButtonDefaults.buttonColors()
        ButtonVariant.SECONDARY -> ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.secondary,
            contentColor = MaterialTheme.colorScheme.onSecondary,
        )
        ButtonVariant.OUTLINE -> ButtonDefaults.outlinedButtonColors()
        ButtonVariant.GHOST -> ButtonDefaults.textButtonColors()
        ButtonVariant.DANGER -> ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.error,
            contentColor = MaterialTheme.colorScheme.onError,
        )
    }

    when (variant) {
        ButtonVariant.OUTLINE -> {
            OutlinedButton(
                onClick = onClick,
                modifier = modifier.height(48.dp),
                enabled = enabled && !loading,
                colors = buttonColors,
                contentPadding = contentPadding,
            ) {
                ButtonContent(text, loading, icon)
            }
        }
        ButtonVariant.GHOST -> {
            TextButton(
                onClick = onClick,
                modifier = modifier.height(48.dp),
                enabled = enabled && !loading,
                colors = buttonColors,
                contentPadding = contentPadding,
            ) {
                ButtonContent(text, loading, icon)
            }
        }
        else -> {
            Button(
                onClick = onClick,
                modifier = modifier.height(48.dp),
                enabled = enabled && !loading,
                colors = buttonColors,
                contentPadding = contentPadding,
            ) {
                ButtonContent(text, loading, icon)
            }
        }
    }
}

@Composable
private fun RowScope.ButtonContent(text: String, loading: Boolean, icon: ImageVector?) {
    if (loading) {
        CircularProgressIndicator(
            modifier = Modifier.size(20.dp),
            strokeWidth = 2.dp,
            color = MaterialTheme.colorScheme.onPrimary,
        )
    }
    if (icon != null && !loading) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            modifier = Modifier.size(20.dp),
        )
    }
    if (text.isNotBlank()) {
        if (icon != null || loading) Spacer(Modifier.width(8.dp))
        Text(text = text, style = MaterialTheme.typography.labelLarge)
    }
}

enum class ButtonVariant {
    PRIMARY, SECONDARY, OUTLINE, GHOST, DANGER
}
