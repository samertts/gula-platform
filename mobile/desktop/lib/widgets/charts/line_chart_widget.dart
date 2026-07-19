import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

class LineChartWidget extends StatelessWidget {
  final List<LineChartDataPoint> data;
  final String? title;
  final double? height;
  final Color? lineColor;
  final Color? fillColor;
  final bool showDots;
  final bool isCurved;

  const LineChartWidget({
    super.key,
    required this.data,
    this.title,
    this.height,
    this.lineColor,
    this.fillColor,
    this.showDots = true,
    this.isCurved = true,
  });

  @override
  Widget build(BuildContext context) {
    final maxY = data.fold<double>(0, (prev, d) => d.y > prev ? d.y : prev);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (title != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Text(
              title!,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ),
        SizedBox(
          height: height ?? 250,
          child: LineChart(
            LineChartData(
              minX: 0,
              maxX: (data.length - 1).toDouble(),
              minY: 0,
              maxY: (maxY * 1.2).ceilToDouble(),
              lineBarsData: [
                LineChartBarData(
                  spots: data.asMap().entries.map((e) =>
                    FlSpot(e.key.toDouble(), e.value.y)
                  ).toList(),
                  isCurved: isCurved,
                  color: lineColor ?? AppColors.primary500,
                  barWidth: 2.5,
                  isStrokeCapRound: true,
                  dotData: FlDotData(
                    show: showDots,
                    getDotPainter: (spot, percent, bar, index) => FlDotCirclePainter(
                      radius: 4,
                      color: lineColor ?? AppColors.primary500,
                      strokeWidth: 2,
                      strokeColor: Colors.white,
                    ),
                  ),
                  belowBarData: BarAreaData(
                    show: true,
                    color: (fillColor ?? AppColors.primary500).withOpacity(0.1),
                  ),
                ),
              ],
              titlesData: FlTitlesData(
                show: true,
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: (data.length / 6).ceilToDouble().clamp(1, double.infinity),
                    getTitlesWidget: (value, meta) {
                      final index = value.toInt();
                      if (index >= 0 && index < data.length) {
                        return Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            data[index].label,
                            style: const TextStyle(fontSize: 10, color: AppColors.textSecondary),
                          ),
                        );
                      }
                      return const SizedBox.shrink();
                    },
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 40,
                    getTitlesWidget: (value, meta) => Text(
                      value.toInt().toString(),
                      style: const TextStyle(fontSize: 10, color: AppColors.textSecondary),
                    ),
                  ),
                ),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              ),
              gridData: FlGridData(
                show: true,
                drawVerticalLine: false,
                horizontalInterval: (maxY / 4).ceilToDouble().clamp(1, double.infinity),
              ),
              borderData: FlBorderData(show: false),
              lineTouchData: LineTouchData(
                enabled: true,
                touchTooltipData: LineTouchTooltipData(
                  getTooltipItems: (touchedSpots) => touchedSpots.map((spot) {
                    final index = spot.x.toInt();
                    final label = index >= 0 && index < data.length ? data[index].label : '';
                    return LineTooltipItem(
                      '$label\n${spot.y.toStringAsFixed(1)}',
                      const TextStyle(color: Colors.white, fontSize: 12),
                    );
                  }).toList(),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class LineChartDataPoint {
  final String label;
  final double y;

  LineChartDataPoint({required this.label, required this.y});
}
