import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../core/gula_card.dart';
import '../core/gula_badge.dart';

class SampleCard extends StatelessWidget {
  final String id;
  final String barcode;
  final String sampleType;
  final String status;
  final String? patientName;
  final DateTime? collectedAt;
  final VoidCallback? onTap;

  const SampleCard({
    super.key,
    required this.id,
    required this.barcode,
    required this.sampleType,
    required this.status,
    this.patientName,
    this.collectedAt,
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
              color: AppColors.accent50,
              borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
            ),
            child: const Icon(
              Icons.science_outlined,
              color: AppColors.accent500,
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
                      barcode,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        fontFamily: 'monospace',
                      ),
                    ),
                    const SizedBox(width: 8),
                    _buildStatusBadge(status),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  sampleType,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.textPrimary,
                  ),
                ),
                if (patientName != null) ...[
                  Text(
                    patientName!,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
                if (collectedAt != null)
                  Text(
                    'Collected: ${collectedAt!.toLocal().toString().substring(0, 16)}',
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.textSecondary,
                    ),
                  ),
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
      case 'collected':
        return const GulaBadge(
          label: 'Collected',
          status: GulaBadgeStatus.info,
        );
      case 'received':
        return const GulaBadge(
          label: 'Received',
          status: GulaBadgeStatus.pending,
        );
      case 'processing':
        return const GulaBadge(
          label: 'Processing',
          status: GulaBadgeStatus.warning,
        );
      case 'analyzed':
        return const GulaBadge(
          label: 'Analyzed',
          status: GulaBadgeStatus.success,
        );
      case 'rejected':
        return const GulaBadge(
          label: 'Rejected',
          status: GulaBadgeStatus.error,
        );
      default:
        return GulaBadge(label: status, status: GulaBadgeStatus.neutral);
    }
  }
}
