package io.gula.android.ui.components.patient

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import io.gula.android.domain.model.Patient
import io.gula.android.ui.components.core.GulaCard
import io.gula.android.ui.components.core.GulaStatusBadge

@Composable
fun PatientCard(
    patient: Patient,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    GulaCard(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = if (patient.gender == "M") Icons.Default.Male else Icons.Default.Female,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(20.dp),
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        text = patient.fullName,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                    )
                }
                if (patient.gender != null || patient.age != null) {
                    Text(
                        text = buildString {
                            patient.gender?.let { append(if (it == "M") "Male" else "Female") }
                            if (patient.age != null) {
                                if (isNotEmpty()) append(" · ")
                                append("${patient.age}y")
                            }
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                if (patient.phone.isNotBlank()) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Default.Phone, contentDescription = null,
                            modifier = Modifier.size(14.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Spacer(Modifier.width(4.dp))
                        Text(patient.phone, style = MaterialTheme.typography.bodySmall)
                    }
                }
                if (patient.nationalId != null) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Default.Badge, contentDescription = null,
                            modifier = Modifier.size(14.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Spacer(Modifier.width(4.dp))
                        Text("ID: ${patient.nationalId}", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
            if (patient.healthId != null) {
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Health ID: ${patient.healthId}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            if (patient.status != null) {
                Spacer(Modifier.height(8.dp))
                GulaStatusBadge(
                    text = patient.status,
                    color = when (patient.status) {
                        "active" -> MaterialTheme.colorScheme.primary
                        "inactive" -> MaterialTheme.colorScheme.error
                        else -> MaterialTheme.colorScheme.secondary
                    }
                )
            }
        }
    }
}
