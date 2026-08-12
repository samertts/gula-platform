import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../core/gula_card.dart';
import 'trend_indicator.dart';

class KpiCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color? color;
  final double? trendValue;
  final String? trendLabel;
  final Color? trendColor;
  final VoidCallback? onTap;
  final Widget? bottomWidget;

  const KpiCard({
    super.key,
    required this.title,
    required this.value,
    required this.icon,
    this.color,
    this.trendValue,
    this.trendLabel,
    this.trendColor,
    this.onTap,
    this.bottomWidget,
  });

  @override
  Widget build(BuildContext context) {
    return GulaCard(
      onTap: onTap,
      padding: const EdgeInsets.all(AppDimensions.space4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: (color ?? AppColors.primary500).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
                ),
                child: Icon(
                  icon,
                  color: color ?? AppColors.primary500,
                  size: 20,
                ),
              ),
              const Spacer(),
              if (trendValue != null)
                TrendIndicator(
                  value: trendValue!,
                  label: trendLabel,
                  color: trendColor,
                ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            value,
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
              color: color ?? AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            title,
            style: const TextStyle(
              fontSize: 13,
              color: AppColors.textSecondary,
            ),
          ),
          if (bottomWidget != null) ...[
            const SizedBox(height: 8),
            bottomWidget!,
          ],
        ],
      ),
    );
  }
}
