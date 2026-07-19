package io.gula.android.ui.components.core

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun GulaCard(
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
    elevation: CardElevation? = null,
    colors: CardColors? = null,
    shape: androidx.compose.ui.graphics.Shape = RoundedCornerShape(12.dp),
    content: @Composable ColumnScope.() -> Unit,
) {
    if (onClick != null) {
        Card(
            onClick = onClick,
            modifier = modifier,
            shape = shape,
            elevation = elevation ?: CardDefaults.cardElevation(defaultElevation = 2.dp),
            colors = colors ?: CardDefaults.cardColors(),
        ) {
            Column(modifier = Modifier.fillMaxWidth(), content = content)
        }
    } else {
        Card(
            modifier = modifier,
            shape = shape,
            elevation = elevation ?: CardDefaults.cardElevation(defaultElevation = 2.dp),
            colors = colors ?: CardDefaults.cardColors(),
        ) {
            Column(modifier = Modifier.fillMaxWidth(), content = content)
        }
    }
}
