import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';

class GulaStatusBar extends StatelessWidget {
  final bool isOnline;
  final DateTime? lastSync;
  final int? pendingCount;
  final String? labName;

  const GulaStatusBar({
    super.key,
    this.isOnline = true,
    this.lastSync,
    this.pendingCount,
    this.labName,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: AppDimensions.statusBarHeight,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: AppColors.neutral900,
        border: Border(
          top: BorderSide(color: AppColors.neutral800),
        ),
      ),
      child: Row(
        children: [
          _buildStatusDot(isOnline),
          const SizedBox(width: 6),
          Text(
            isOnline ? 'Online' : 'Offline',
            style: TextStyle(
              color: isOnline ? AppColors.success400 : AppColors.warning400,
              fontSize: 11,
            ),
          ),
          if (!isOnline) ...[
            const SizedBox(width: 16),
            Icon(Icons.sync, size: 12, color: AppColors.warning400),
            const SizedBox(width: 4),
            Text(
              '$pendingCount pending',
              style: const TextStyle(color: AppColors.warning400, fontSize: 11),
            ),
          ],
          if (lastSync != null) ...[
            const SizedBox(width: 16),
            const Icon(Icons.cloud_done, size: 12, color: AppColors.neutral400),
            const SizedBox(width: 4),
            Text(
              'Last sync: ${lastSync!.toLocal().toString().substring(0, 19)}',
              style: const TextStyle(color: AppColors.neutral400, fontSize: 11),
            ),
          ],
          const Spacer(),
          if (labName != null)
            Text(
              labName!,
              style: const TextStyle(color: AppColors.neutral400, fontSize: 11),
            ),
          const SizedBox(width: 16),
          Text(
            'GULA v2.1.0',
            style: const TextStyle(color: AppColors.neutral600, fontSize: 11),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusDot(bool online) {
    return Container(
      width: 8,
      height: 8,
      decoration: BoxDecoration(
        color: online ? AppColors.success400 : AppColors.warning400,
        shape: BoxShape.circle,
      ),
    );
  }
}
