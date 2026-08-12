package io.gula.android.ui.features.orders

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.gula.android.ui.components.core.*
import io.gula.android.ui.components.order.OrderCard

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrderListScreen(
    onOrderClick: (Int) -> Unit,
    onCreateOrder: () -> Unit,
    viewModel: OrdersViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Orders",
                actions = {
                    IconButton(onClick = { viewModel.refresh() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                },
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = onCreateOrder,
                icon = { Icon(Icons.Default.Add, contentDescription = null) },
                text = { Text("New Order") },
            )
        },
    ) { padding ->
        if (uiState.isLoading && uiState.orders.isEmpty()) {
            GulaLoadingIndicator(modifier = Modifier.padding(padding))
        } else if (uiState.orders.isEmpty()) {
            GulaEmptyState(
                title = "No Orders",
                message = "Create your first order to get started",
                action = {
                    GulaButton(
                        onClick = onCreateOrder,
                        text = "Create Order",
                        icon = Icons.Default.PostAdd,
                    )
                },
                modifier = Modifier.padding(padding),
            )
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                items(uiState.orders, key = { it.id }) { order ->
                    OrderCard(
                        order = order,
                        onClick = { onOrderClick(order.id) },
                    )
                }
            }
        }
    }
}
