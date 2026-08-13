import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';

enum GulaCardVariant { elevated, outlined, filled }

class GulaCard extends StatelessWidget {
  final Widget child;
  final GulaCardVariant variant;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final double? elevation;
  final Color? color;
  final Color? borderColor;
  final double? borderRadius;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;
  final bool hasShadow;

  const GulaCard({
    super.key,
    required this.child,
    this.variant = GulaCardVariant.elevated,
    this.padding,
    this.margin,
    this.elevation,
    this.color,
    this.borderColor,
    this.borderRadius,
    this.onTap,
    this.onLongPress,
    this.hasShadow = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final effectiveRadius = borderRadius ?? AppDimensions.radiusLg;
    final effectiveMargin =
        margin ?? const EdgeInsets.all(AppDimensions.space2);
    final effectivePadding =
        padding ?? const EdgeInsets.all(AppDimensions.space4);

    switch (variant) {
      case GulaCardVariant.elevated:
        return Card(
          margin: effectiveMargin,
          elevation: elevation ?? (hasShadow ? 1 : 0),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(effectiveRadius),
          ),
          color: color ?? theme.cardColor,
          clipBehavior: Clip.antiAlias,
          child: InkWell(
            onTap: onTap,
            onLongPress: onLongPress,
            child: Padding(padding: effectivePadding, child: child),
          ),
        );
      case GulaCardVariant.outlined:
        return Card(
          margin: effectiveMargin,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(effectiveRadius),
            side: BorderSide(color: borderColor ?? AppColors.border, width: 1),
          ),
          color: color ?? theme.cardColor,
          clipBehavior: Clip.antiAlias,
          child: InkWell(
            onTap: onTap,
            onLongPress: onLongPress,
            child: Padding(padding: effectivePadding, child: child),
          ),
        );
      case GulaCardVariant.filled:
        return Container(
          margin: effectiveMargin,
          decoration: BoxDecoration(
            color: color ?? AppColors.neutral50,
            borderRadius: BorderRadius.circular(effectiveRadius),
            border: Border.all(color: borderColor ?? AppColors.neutral100),
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: onTap,
              onLongPress: onLongPress,
              borderRadius: BorderRadius.circular(effectiveRadius),
              child: Padding(padding: effectivePadding, child: child),
            ),
          ),
        );
    }
  }
}
