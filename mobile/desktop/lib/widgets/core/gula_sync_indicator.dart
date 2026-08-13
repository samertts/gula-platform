import 'package:flutter/material.dart';

import '../../core/offline/sync_engine.dart';
import '../../core/theme/app_colors.dart';

class GulaSyncIndicator extends StatelessWidget {
  final SyncStatus status;
  final double progress;
  final DateTime? lastSync;
  final VoidCallback? onSync;
  final bool showLabel;

  const GulaSyncIndicator({
    super.key,
    required this.status,
    this.progress = 0.0,
    this.lastSync,
    this.onSync,
    this.showLabel = true,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onSync,
      child: Tooltip(
        message: _tooltipMessage,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildIcon(),
            if (showLabel) ...[
              const SizedBox(width: 6),
              Text(
                _label,
                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildIcon() {
    switch (status) {
      case SyncStatus.syncing:
        return SizedBox(
          width: 16,
          height: 16,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            value: progress > 0 ? progress : null,
            valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary500),
          ),
        );
      case SyncStatus.error:
        return const Icon(Icons.sync_problem, size: 16, color: AppColors.error500);
      case SyncStatus.offline:
        return const Icon(Icons.wifi_off, size: 16, color: AppColors.warning500);
      case SyncStatus.pending:
        return const Icon(Icons.sync, size: 16, color: AppColors.info500);
      case SyncStatus.idle:
        return Icon(Icons.cloud_done, size: 16, color: lastSync != null ? AppColors.success500 : AppColors.neutral400);
    }
  }

  String get _label {
    switch (status) {
      case SyncStatus.syncing:
        return 'Syncing...';
      case SyncStatus.error:
        return 'Sync Error';
      case SyncStatus.offline:
        return 'Offline';
      case SyncStatus.pending:
        return 'Pending Sync';
      case SyncStatus.idle:
        return lastSync != null ? 'Synced' : '';
    }
  }

  String get _tooltipMessage {
    switch (status) {
      case SyncStatus.syncing:
        return 'Synchronizing data...';
      case SyncStatus.error:
        return 'Sync failed. Tap to retry.';
      case SyncStatus.offline:
        return 'Offline mode';
      case SyncStatus.pending:
        return 'Pending changes';
      case SyncStatus.idle:
        if (lastSync != null) {
          return 'Last sync: ${lastSync!.toLocal().toString().substring(0, 19)}';
        }
        return 'No sync yet';
    }
  }
}
