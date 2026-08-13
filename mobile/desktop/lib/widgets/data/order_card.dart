import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../core/gula_card.dart';
import '../core/gula_badge.dart';

class OrderCard extends StatelessWidget {
  final String id;
  final String orderNumber;
  final String patientName;
  final String status;
  final String? testTypes;
  final DateTime? createdAt;
  final String? doctorName;
  final VoidCallback? onTap;

  const OrderCard({
    super.key,
    required this.id,
    required this.orderNumber,
    required this.patientName,
    required this.status,
    this.testTypes,
    this.createdAt,
    this.doctorName,
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
              color: AppColors.info50,
              borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
            ),
            child: const Icon(
              Icons.assignment_outlined,
              color: AppColors.info500,
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
                    Text(
                      '#$orderNumber',
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(width: 8),
                    _buildStatusBadge(status),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  patientName,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: AppColors.textPrimary,
                  ),
                ),
                if (testTypes != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    testTypes!,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
                if (createdAt != null || doctorName != null) ...[
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      if (createdAt != null)
                        Text(
                          createdAt!.toLocal().toString().substring(0, 10),
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      if (doctorName != null) ...[
                        const SizedBox(width: 12),
                        Text(
                          doctorName!,
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ],
            ),
          ),
          const Icon(Icons.chevron_right, color: AppColors.neutral400),
        ],
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
    switch (status) {
      case 'pending':
        return const GulaBadge(
          label: 'Pending',
          status: GulaBadgeStatus.pending,
        );
      case 'completed':
        return const GulaBadge(
          label: 'Completed',
          status: GulaBadgeStatus.success,
        );
      case 'validated':
        return const GulaBadge(
          label: 'Validated',
          status: GulaBadgeStatus.success,
        );
      case 'cancelled':
        return const GulaBadge(
          label: 'Cancelled',
          status: GulaBadgeStatus.cancelled,
        );
      default:
        return GulaBadge(label: status, status: GulaBadgeStatus.neutral);
    }
  }
}
