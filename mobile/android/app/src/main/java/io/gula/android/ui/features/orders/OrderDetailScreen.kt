package io.gula.android.ui.features.orders

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.domain.model.ResultItem
import io.gula.android.ui.components.core.*
import io.gula.android.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrderDetailScreen(
    orderId: Int,
    onBack: () -> Unit,
    viewModel: OrdersViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    var showCancelDialog by remember { mutableStateOf(false) }

    LaunchedEffect(orderId) {
        viewModel.loadOrder(orderId)
    }

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Order #$orderId",
                onBackClick = onBack,
                actions = {
                    if (uiState.selectedOrder?.status == "pending") {
                        IconButton(onClick = { showCancelDialog = true }) {
                            Icon(Icons.Default.Cancel, contentDescription = "Cancel")
                        }
                    }
                },
            )
        },
    ) { padding ->
        when {
            uiState.isLoading -> GulaLoadingIndicator(modifier = Modifier.padding(padding))
            uiState.selectedOrder == null -> GulaErrorView(message = uiState.error ?: "Order not found", modifier = Modifier.padding(padding))
            else -> {
                val order = uiState.selectedOrder!!
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    item {
                        GulaCard {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    Text("Order #${order.id}", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                                    GulaStatusBadge(
                                        text = order.status,
                                        color = when (order.status) {
                                            "pending" -> Orange40
                                            "completed" -> Green40
                                            "validated" -> Blue40
                                            "cancelled" -> Red40
                                            else -> Neutral40
                                        },
                                    )
                                }
                                Spacer(Modifier.height(8.dp))
                                DetailRow(icon = Icons.Default.Person, label = "Patient", value = order.patientName ?: "ID: ${order.patientId}")
                                if (order.doctorName != null) DetailRow(icon = Icons.Default.MedicalServices, label = "Doctor", value = order.doctorName)
                                DetailRow(icon = Icons.Default.CalendarMonth, label = "Created", value = order.createdAt?.take(10) ?: "")
                            }
                        }
                    }

                    item {
                        Text("Test Results", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    }

                    if (order.results.isEmpty()) {
                        item {
                            GulaCard {
                                Box(modifier = Modifier.padding(24.dp).fillMaxWidth(), contentAlignment = Alignment.Center) {
                                    Text("No results yet", color = MaterialTheme.colorScheme.onSurfaceVariant)
                                }
                            }
                        }
                    } else {
                        items(order.results, key = { it.id ?: it.testName }) { result ->
                            ResultItemCard(result = result)
                        }
                    }

                    if (order.status == "pending") {
                        item {
                            Spacer(Modifier.height(8.dp))
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                GulaButton(
                                    onClick = { viewModel.validateOrder(order.id) },
                                    text = "Validate",
                                    icon = Icons.Default.CheckCircle,
                                    modifier = Modifier.weight(1f),
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    GulaDialog(
        show = showCancelDialog,
        onDismiss = { showCancelDialog = false },
        title = "Cancel Order",
        text = "Are you sure you want to cancel this order?",
        confirmText = "Cancel Order",
        onConfirm = { viewModel.cancelOrder(orderId); showCancelDialog = false },
        onDismissButton = { showCancelDialog = false },
    )
}

@Composable
private fun ResultItemCard(result: ResultItem) {
    GulaCard(
        colors = CardDefaults.cardColors(
            containerColor = when {
                result.isCritical -> CriticalRedLight
                result.isAbnormal -> Color(0xFFFFF3E0)
                else -> MaterialTheme.colorScheme.surface
            }
        ),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(result.testName, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Medium)
                if (result.unit != null) Text(result.unit, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = buildString {
                        append(result.value?.toString() ?: result.valueText ?: "—")
                    },
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = when {
                        result.isCritical -> CriticalRed
                        result.isAbnormal -> AbnormalOrange
                        else -> MaterialTheme.colorScheme.onSurface
                    },
                )
                if (result.normalRangeLow != null || result.normalRangeHigh != null) {
                    Text(
                        text = "${result.normalRangeLow ?: "—"} — ${result.normalRangeHigh ?: "—"}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}

@Composable
private fun DetailRow(icon: androidx.compose.ui.graphics.vector.ImageVector, label: String, value: String) {
    Row(modifier = Modifier.padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
        Icon(icon, contentDescription = null, modifier = Modifier.size(18.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.width(12.dp))
        Column {
            Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
