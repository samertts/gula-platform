import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

class TrendIndicator extends StatelessWidget {
  final double value;
  final String? label;
  final Color? color;

  const TrendIndicator({
    super.key,
    required this.value,
    this.label,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final isUp = value >= 0;
    final trendColor = color ?? (isUp ? AppColors.success500 : AppColors.error500);

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          isUp ? Icons.trending_up : Icons.trending_down,
          size: 16,
          color: trendColor,
        ),
        const SizedBox(width: 2),
        Text(
          '${isUp ? '+' : ''}${value.toStringAsFixed(1)}%',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: trendColor,
          ),
        ),
        if (label != null) ...[
          const SizedBox(width: 4),
          Text(
            label!,
            style: const TextStyle(
              fontSize: 11,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ],
    );
  }
}
