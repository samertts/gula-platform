import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../core/gula_card.dart';
import '../core/gula_badge.dart';
import 'critical_value_flag.dart';

class ResultCard extends StatelessWidget {
  final String id;
  final String testName;
  final String result;
  final String? unit;
  final String? referenceRange;
  final String? flag;
  final String? patientName;
  final String? status;
  final DateTime? createdAt;
  final VoidCallback? onTap;

  const ResultCard({
    super.key,
    required this.id,
    required this.testName,
    required this.result,
    this.unit,
    this.referenceRange,
    this.flag,
    this.patientName,
    this.status,
    this.createdAt,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GulaCard(
      onTap: onTap,
      variant: GulaCardVariant.outlined,
      padding: const EdgeInsets.all(AppDimensions.space3),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: _isCritical ? AppColors.error50 : AppColors.success50,
              borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
            ),
            child: Icon(
              _isCritical ? Icons.warning_amber : Icons.check_circle_outline,
              color: _isCritical ? AppColors.error500 : AppColors.success500,
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        testName,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    if (flag != null && flag != 'normal')
                      CriticalValueFlag(flag: flag!),
                  ],
                ),
                const SizedBox(height: 4),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      result,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: _isCritical ? AppColors.error500 : AppColors.textPrimary,
                      ),
                    ),
                    if (unit != null) ...[
                      const SizedBox(width: 4),
                      Text(
                        unit!,
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                    ],
                  ],
                ),
                if (referenceRange != null)
                  Text(
                    'Ref: $referenceRange',
                    style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                  ),
                if (patientName != null || createdAt != null) ...[
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      if (patientName != null)
                        Text(
                          patientName!,
                          style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                        ),
                      if (createdAt != null) ...[
                        const SizedBox(width: 12),
                        Text(
                          createdAt!.toLocal().toString().substring(0, 10),
                          style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                        ),
                      ],
                    ],
                  ),
                ],
              ],
            ),
          ),
          if (status != null)
            Padding(
              padding: const EdgeInsets.only(left: 8),
              child: GulaBadge(
                label: status!,
                status: status == 'verified' ? GulaBadgeStatus.success : GulaBadgeStatus.pending,
              ),
            ),
        ],
      ),
    );
  }

  bool get _isCritical => flag == 'critical' || flag == 'h' || flag == 'l';
}
