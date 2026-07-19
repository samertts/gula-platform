import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';

enum GulaAlertType { info, success, warning, error }

class GulaAlert extends StatelessWidget {
  final String title;
  final String? message;
  final GulaAlertType type;
  final VoidCallback? onDismiss;
  final List<Widget>? actions;
  final bool dismissible;

  const GulaAlert({
    super.key,
    required this.title,
    this.message,
    this.type = GulaAlertType.info,
    this.onDismiss,
    this.actions,
    this.dismissible = false,
  });

  IconData get _icon {
    switch (type) {
      case GulaAlertType.info:
        return Icons.info_outline;
      case GulaAlertType.success:
        return Icons.check_circle_outline;
      case GulaAlertType.warning:
        return Icons.warning_amber_outlined;
      case GulaAlertType.error:
        return Icons.error_outline;
    }
  }

  Color get _color {
    switch (type) {
      case GulaAlertType.info:
        return AppColors.info50;
      case GulaAlertType.success:
        return AppColors.success50;
      case GulaAlertType.warning:
        return AppColors.warning50;
      case GulaAlertType.error:
        return AppColors.error50;
    }
  }

  Color get _iconColor {
    switch (type) {
      case GulaAlertType.info:
        return AppColors.info500;
      case GulaAlertType.success:
        return AppColors.success500;
      case GulaAlertType.warning:
        return AppColors.warning500;
      case GulaAlertType.error:
        return AppColors.error500;
    }
  }

  Color get _borderColor {
    switch (type) {
      case GulaAlertType.info:
        return AppColors.info200;
      case GulaAlertType.success:
        return AppColors.success200;
      case GulaAlertType.warning:
        return AppColors.warning200;
      case GulaAlertType.error:
        return AppColors.error200;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppDimensions.space4),
      decoration: BoxDecoration(
        color: _color,
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        border: Border.all(color: _borderColor),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(_icon, color: _iconColor, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: _iconColor,
                    fontSize: 14,
                  ),
                ),
                if (message != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    message!,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                ],
                if (actions != null) ...[
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    children: actions!,
                  ),
                ],
              ],
            ),
          ),
          if (dismissible)
            InkWell(
              onTap: onDismiss,
              child: Icon(Icons.close, size: 18, color: AppColors.textSecondary),
            ),
        ],
      ),
    );
  }
}
