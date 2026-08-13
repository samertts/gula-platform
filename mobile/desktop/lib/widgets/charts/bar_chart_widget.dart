import 'package:fl_chart/fl_chart.dart' as fl;
import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

class BarChartWidget extends StatelessWidget {
  final List<BarChartData> data;
  final String? title;
  final double? height;
  final bool showLegend;
  final bool isHorizontal;

  const BarChartWidget({
    super.key,
    required this.data,
    this.title,
    this.height,
    this.showLegend = true,
    this.isHorizontal = false,
  });

  @override
  Widget build(BuildContext context) {
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
          child: fl.BarChart(
            fl.BarChartData(
              alignment: fl.BarChartAlignment.spaceAround,
              maxY: _maxY,
              minY: 0,
              barTouchData: fl.BarTouchData(
                enabled: true,
                touchTooltipData: fl.BarTouchTooltipData(
                  getTooltipItem: (group, groupIndex, rod, rodIndex) {
                    return fl.BarTooltipItem(
                      '${data[group.x.toInt()].label}\n${rod.toY.toStringAsFixed(0)}',
                      const TextStyle(color: Colors.white, fontSize: 12),
                    );
                  },
                ),
              ),
              titlesData: fl.FlTitlesData(
                show: true,
                bottomTitles: fl.AxisTitles(
                  sideTitles: fl.SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      if (value.toInt() >= 0 && value.toInt() < data.length) {
                        return Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            data[value.toInt()].label,
                            style: const TextStyle(
                              fontSize: 10,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        );
                      }
                      return const SizedBox.shrink();
                    },
                  ),
                ),
                leftTitles: fl.AxisTitles(
                  sideTitles: fl.SideTitles(
                    showTitles: true,
                    reservedSize: 40,
                    getTitlesWidget: (value, meta) => Text(
                      value.toInt().toString(),
                      style: const TextStyle(
                        fontSize: 10,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ),
                ),
                topTitles: const fl.AxisTitles(
                  sideTitles: fl.SideTitles(showTitles: false),
                ),
                rightTitles: const fl.AxisTitles(
                  sideTitles: fl.SideTitles(showTitles: false),
                ),
              ),
              gridData: fl.FlGridData(
                show: true,
                drawVerticalLine: false,
                horizontalInterval: _maxY / 4,
              ),
              borderData: fl.FlBorderData(show: false),
              barGroups: data.asMap().entries.map((entry) {
                return fl.BarChartGroupData(
                  x: entry.key,
                  barRods: [
                    fl.BarChartRodData(
                      toY: entry.value.value,
                      color: entry.value.color ?? AppColors.primary500,
                      width: 20,
                      borderRadius: const BorderRadius.only(
                        topLeft: Radius.circular(4),
                        topRight: Radius.circular(4),
                      ),
                    ),
                  ],
                );
              }).toList(),
            ),
          ),
        ),
        if (showLegend) ...[
          const SizedBox(height: 12),
          Wrap(
            spacing: 16,
            children: data
                .map(
                  (d) => Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 12,
                        height: 12,
                        decoration: BoxDecoration(
                          color: d.color ?? AppColors.primary500,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      const SizedBox(width: 4),
                      Text(d.label, style: const TextStyle(fontSize: 12)),
                    ],
                  ),
                )
                .toList(),
          ),
        ],
      ],
    );
  }

  double get _maxY {
    final max = data.fold<double>(
      0,
      (prev, d) => d.value > prev ? d.value : prev,
    );
    return (max * 1.2).ceilToDouble();
  }
}

class BarChartData {
  final String label;
  final double value;
  final Color? color;

  BarChartData({required this.label, required this.value, this.color});
}
