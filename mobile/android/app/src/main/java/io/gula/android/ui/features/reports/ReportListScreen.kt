package io.gula.android.ui.features.reports

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import io.gula.android.ui.components.core.GulaTopBar

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReportListScreen(
    onReportClick: (Int) -> Unit,
    onBack: () -> Unit,
) {
    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Reports",
                onBackClick = onBack,
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Text(
                text = "Reports",
                style = MaterialTheme.typography.headlineSmall,
            )
            Text(
                text = "Generated reports will appear here.",
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}
