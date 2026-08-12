package io.gula.android.ui.features.reports

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import io.gula.android.ui.components.core.GulaTopBar

@Composable
fun ReportViewerScreen(
    reportId: Int,
    onBack: () -> Unit,
) {
    Scaffold(
        topBar = {
            GulaTopBar(
                title = "Report",
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
                text = "Report #$reportId",
                style = MaterialTheme.typography.headlineSmall,
            )
            Text(
                text = "The report viewer will display the authorised report content here.",
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}
