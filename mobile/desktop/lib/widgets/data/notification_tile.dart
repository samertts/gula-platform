import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../core/gula_badge.dart';

class NotificationTile extends StatelessWidget {
  final String id;
  final String title;
  final String body;
  final String type;
  final String severity;
  final bool isRead;
  final DateTime createdAt;
  final VoidCallback? onTap;

  const NotificationTile({
    super.key,
    required this.id,
    required this.title,
    required this.body,
    required this.type,
    required this.severity,
    required this.isRead,
    required this.createdAt,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: onTap,
      leading: _buildIcon(),
      title: Text(
        title,
        style: TextStyle(
          fontSize: 14,
          fontWeight: isRead ? FontWeight.w400 : FontWeight.w600,
          color: AppColors.textPrimary,
        ),
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 2),
          Text(
            body,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              _buildSeverityBadge(),
              const SizedBox(width: 8),
              Text(
                _formatTime(createdAt),
                style: const TextStyle(
                  fontSize: 11,
                  color: AppColors.neutral400,
                ),
              ),
            ],
          ),
        ],
      ),
      trailing: !isRead
          ? Container(
              width: 8,
              height: 8,
              decoration: const BoxDecoration(
                color: AppColors.primary500,
                shape: BoxShape.circle,
              ),
            )
          : null,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: AppDimensions.space4,
        vertical: AppDimensions.space1,
      ),
      tileColor: isRead ? null : AppColors.primary50.withOpacity(0.5),
    );
  }

  Widget _buildIcon() {
    IconData icon;
    Color color;
    switch (type) {
      case 'critical':
        icon = Icons.warning_amber;
        color = AppColors.error500;
      case 'result':
        icon = Icons.description;
        color = AppColors.info500;
      case 'order':
        icon = Icons.assignment;
        color = AppColors.primary500;
      case 'system':
        icon = Icons.settings;
        color = AppColors.accent500;
      default:
        icon = Icons.notifications;
        color = AppColors.neutral500;
    }

    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
      ),
      child: Icon(icon, color: color, size: 18),
    );
  }

  Widget _buildSeverityBadge() {
    GulaBadgeStatus status;
    switch (severity) {
      case 'critical':
        status = GulaBadgeStatus.critical;
      case 'warning':
        status = GulaBadgeStatus.warning;
      case 'error':
        status = GulaBadgeStatus.error;
      default:
        status = GulaBadgeStatus.info;
    }
    return GulaBadge(label: severity, status: status, showDot: false);
  }

  String _formatTime(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }
}
