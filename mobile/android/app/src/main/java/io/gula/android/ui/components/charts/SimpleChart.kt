package io.gula.android.ui.components.charts

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import io.gula.android.ui.theme.*

@Composable
fun BarChart(
    data: List<BarChartData>,
    modifier: Modifier = Modifier,
    title: String? = null,
    maxValue: Float? = null,
    barColor: Color = MaterialTheme.colorScheme.primary,
) {
    Column(modifier = modifier) {
        if (title != null) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                modifier = Modifier.padding(bottom = 8.dp),
            )
        }
        val effectiveMax = maxValue ?: data.maxOfOrNull { it.value } ?: 1f
        Canvas(
            modifier = Modifier
                .fillMaxWidth()
                .height(160.dp)
        ) {
            val barWidth = size.width / (data.size * 2f)
            val gap = barWidth
            data.forEachIndexed { index, item ->
                val barHeight = (item.value / effectiveMax) * size.height * 0.85f
                val x = index * (barWidth + gap) + gap
                val y = size.height - barHeight
                drawRoundRect(
                    color = item.color ?: barColor,
                    topLeft = Offset(x, y),
                    size = androidx.compose.ui.geometry.Size(barWidth, barHeight),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(4f, 4f),
                )
            }
        }
    }
}

@Composable
fun PieChart(
    data: List<PieChartData>,
    modifier: Modifier = Modifier,
    title: String? = null,
) {
    Column(modifier = modifier, horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
        if (title != null) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                modifier = Modifier.padding(bottom = 8.dp),
            )
        }
        val total = data.sumOf { it.value.toDouble() }.toFloat()
        Canvas(modifier = Modifier.size(120.dp)) {
            if (total <= 0f) return@Canvas
            val strokeWidth = 36.dp.toPx()
            val radius = (size.minDimension - strokeWidth) / 2
            val center = Offset(size.width / 2, size.height / 2)
            var startAngle = -90f
            for (item in data) {
                val sweep = (item.value / total) * 360f
                drawArc(
                    color = item.color,
                    startAngle = startAngle,
                    sweepAngle = sweep,
                    useCenter = false,
                    topLeft = Offset(center.x - radius, center.y - radius),
                    size = androidx.compose.ui.geometry.Size(radius * 2, radius * 2),
                    style = Stroke(width = strokeWidth),
                )
                startAngle += sweep
            }
        }
    }
}

@Composable
fun LineChart(
    dataPoints: List<Float>,
    modifier: Modifier = Modifier,
    title: String? = null,
    lineColor: Color = MaterialTheme.colorScheme.primary,
    gridColor: Color = MaterialTheme.colorScheme.outlineVariant,
) {
    Column(modifier = modifier) {
        if (title != null) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                modifier = Modifier.padding(bottom = 8.dp),
            )
        }
        Canvas(
            modifier = Modifier
                .fillMaxWidth()
                .height(120.dp)
        ) {
            if (dataPoints.isEmpty()) return@Canvas
            val maxVal = dataPoints.max()
            val minVal = dataPoints.min()
            val range = (maxVal - minVal).coerceAtLeast(1f)
            val stepX = size.width / (dataPoints.size - 1).coerceAtLeast(1)
            val path = Path()
            dataPoints.forEachIndexed { index, value ->
                val x = index * stepX
                val y = size.height - ((value - minVal) / range) * size.height * 0.85f - 8.dp.toPx()
                if (index == 0) path.moveTo(x, y) else path.lineTo(x, y)
            }
            drawPath(path, color = lineColor, style = Stroke(width = 3.dp.toPx()))
            dataPoints.forEachIndexed { index, value ->
                val x = index * stepX
                val y = size.height - ((value - minVal) / range) * size.height * 0.85f - 8.dp.toPx()
                drawCircle(color = lineColor, radius = 4.dp.toPx(), center = Offset(x, y))
            }
        }
    }
}

data class BarChartData(
    val label: String,
    val value: Float,
    val color: Color? = null,
)

data class PieChartData(
    val label: String,
    val value: Float,
    val color: Color,
)
