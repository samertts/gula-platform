import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';

enum GulaBadgeStatus {
  success, warning, error, info, neutral, critical, urgent, pending, cancelled
}

class GulaBadge extends StatelessWidget {
  final String label;
  final GulaBadgeStatus status;
  final Color? customColor;
  final Color? customTextColor;
  final IconData? icon;
  final double? fontSize;
  final double? height;
  final bool showDot;

  const GulaBadge({
    super.key,
    required this.label,
    this.status = GulaBadgeStatus.neutral,
    this.customColor,
    this.customTextColor,
    this.icon,
    this.fontSize,
    this.height,
    this.showDot = true,
  });

  Color get _backgroundColor {
    if (customColor != null) return customColor!;
    switch (status) {
      case GulaBadgeStatus.success:
        return AppColors.success50;
      case GulaBadgeStatus.warning:
        return AppColors.warning50;
      case GulaBadgeStatus.error:
        return AppColors.error50;
      case GulaBadgeStatus.info:
        return AppColors.info50;
      case GulaBadgeStatus.critical:
        return AppColors.error50;
      case GulaBadgeStatus.urgent:
        return AppColors.warning50;
      case GulaBadgeStatus.pending:
        return AppColors.info50;
      case GulaBadgeStatus.cancelled:
        return AppColors.neutral100;
      case GulaBadgeStatus.neutral:
        return AppColors.neutral100;
    }
  }

  Color get _textColor {
    if (customTextColor != null) return customTextColor!;
    switch (status) {
      case GulaBadgeStatus.success:
        return AppColors.success700;
      case GulaBadgeStatus.warning:
        return AppColors.warning800;
      case GulaBadgeStatus.error:
        return AppColors.error700;
      case GulaBadgeStatus.info:
        return AppColors.info700;
      case GulaBadgeStatus.critical:
        return AppColors.error800;
      case GulaBadgeStatus.urgent:
        return AppColors.warning900;
      case GulaBadgeStatus.pending:
        return AppColors.info800;
      case GulaBadgeStatus.cancelled:
        return AppColors.neutral600;
      case GulaBadgeStatus.neutral:
        return AppColors.neutral700;
    }
  }

  Color get _dotColor {
    if (customColor != null) return customColor!;
    switch (status) {
      case GulaBadgeStatus.success:
        return AppColors.success500;
      case GulaBadgeStatus.warning:
        return AppColors.warning500;
      case GulaBadgeStatus.error:
        return AppColors.error500;
      case GulaBadgeStatus.info:
        return AppColors.info500;
      case GulaBadgeStatus.critical:
        return AppColors.critical;
      case GulaBadgeStatus.urgent:
        return AppColors.urgent;
      case GulaBadgeStatus.pending:
        return AppColors.pending;
      case GulaBadgeStatus.cancelled:
        return AppColors.cancelled;
      case GulaBadgeStatus.neutral:
        return AppColors.neutral500;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height ?? AppDimensions.badgeHeight,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        color: _backgroundColor,
        borderRadius: BorderRadius.circular(AppDimensions.radiusFull),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (showDot) ...[
            Container(
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                color: _dotColor,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 4),
          ],
          if (icon != null) ...[
            Icon(icon, size: 12, color: _textColor),
            const SizedBox(width: 4),
          ],
          Text(
            label,
            style: TextStyle(
              fontSize: fontSize ?? 11,
              fontWeight: FontWeight.w600,
              color: _textColor,
            ),
          ),
        ],
      ),
    );
  }
}
