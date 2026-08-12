import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

class PieChartWidget extends StatelessWidget {
  final List<PieChartDataItem> data;
  final String? title;
  final double? height;
  final bool showLegend;

  const PieChartWidget({
    super.key,
    required this.data,
    this.title,
    this.height,
    this.showLegend = true,
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
        Row(
          children: [
            SizedBox(
              width: height ?? 200,
              height: height ?? 200,
              child: PieChart(
                PieChartData(
                  sections: data.asMap().entries.map((entry) {
                    final isTouched = false;
                    final item = entry.value;
                    return PieChartSectionData(
                      value: item.value,
                      title: '${item.value.toStringAsFixed(0)}%',
                      radius: isTouched ? 60 : 50,
                      color: item.color,
                      titleStyle: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    );
                  }).toList(),
                  sectionsSpace: 2,
                  centerSpaceRadius: 40,
                  pieTouchData: PieTouchData(enabled: true),
                ),
              ),
            ),
            if (showLegend) ...[
              const SizedBox(width: 24),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: data.map((item) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 12,
                          height: 12,
                          decoration: BoxDecoration(
                            color: item.color,
                            borderRadius: BorderRadius.circular(3),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Flexible(
                          child: Text(
                            item.label,
                            style: const TextStyle(fontSize: 12),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  )).toList(),
                ),
              ),
            ],
          ],
        ),
      ],
    );
  }
}

class PieChartDataItem {
  final String label;
  final double value;
  final Color color;

  PieChartDataItem({
    required this.label,
    required this.value,
    required this.color,
  });
}
