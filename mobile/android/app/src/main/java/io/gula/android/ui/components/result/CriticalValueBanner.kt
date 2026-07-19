package io.gula.android.ui.components.result

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import io.gula.android.domain.model.CriticalAlert

@Composable
fun CriticalValueBanner(
    alert: CriticalAlert,
    modifier: Modifier = Modifier,
    onAcknowledge: (() -> Unit)? = null,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(Color(0xFFFFEBEE))
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            imageVector = Icons.Default.Warning,
            contentDescription = null,
            tint = Color(0xFFD32F2F),
            modifier = Modifier.size(24.dp),
        )
        Spacer(Modifier.width(12.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = "Critical Alert",
                style = MaterialTheme.typography.titleSmall,
                color = Color(0xFFD32F2F),
                fontWeight = androidx.compose.ui.text.font.FontWeight.Bold,
            )
            Spacer(Modifier.height(2.dp))
            Text(
                text = "${alert.patientName} - ${alert.testName}: ${alert.value}",
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF5C3F00),
            )
        }
        if (onAcknowledge != null && alert.status == "active") {
            Spacer(Modifier.width(8.dp))
            TextButton(onClick = onAcknowledge) {
                Text("Acknowledge", color = Color(0xFFD32F2F))
            }
        }
    }
}
