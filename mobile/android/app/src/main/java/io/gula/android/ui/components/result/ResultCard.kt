package io.gula.android.ui.components.result

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import io.gula.android.domain.model.TestResult
import io.gula.android.ui.components.core.GulaCard
import io.gula.android.ui.components.core.GulaStatusBadge

@Composable
fun ResultCard(
    result: TestResult,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    GulaCard(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
        colors = if (result.isCritical) {
            CardDefaults.cardColors(containerColor = Color(0xFFFFF0F0))
        } else null,
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = result.testNameEn,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                    )
                    if (result.testNameAr.isNotBlank()) {
                        Text(
                            text = result.testNameAr,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
                if (result.isCritical) {
                    GulaStatusBadge(
                        text = "CRITICAL",
                        color = Color(0xFFD32F2F),
                    )
                } else if (result.isAbnormal) {
                    GulaStatusBadge(
                        text = "ABNORMAL",
                        color = Color(0xFFF57C00),
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Bottom,
            ) {
                Column {
                    Text(
                        text = buildString {
                            append(result.resultValue?.toString() ?: result.resultText ?: "—")
                            if (result.unit != null) append(" ${result.unit}")
                        },
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Bold,
                        color = when {
                            result.isCritical -> Color(0xFFD32F2F)
                            result.isAbnormal -> Color(0xFFF57C00)
                            else -> MaterialTheme.colorScheme.primary
                        },
                    )
                    if (result.referenceMin != null || result.referenceMax != null) {
                        Text(
                            text = "Ref: ${result.referenceMin ?: "—"} — ${result.referenceMax ?: "—"}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
                Text(
                    text = result.status,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
