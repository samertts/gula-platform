import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';

enum GulaButtonVariant { primary, secondary, outline, text, danger, ghost }

class GulaButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final GulaButtonVariant variant;
  final IconData? icon;
  final IconData? trailingIcon;
  final bool isLoading;
  final bool isFullWidth;
  final bool isDisabled;
  final double? height;
  final double? width;
  final EdgeInsets? padding;
  final double? borderRadius;
  final Color? color;
  final Color? textColor;
  final double? fontSize;
  final FontWeight? fontWeight;

  const GulaButton({
    super.key,
    required this.label,
    this.onPressed,
    this.variant = GulaButtonVariant.primary,
    this.icon,
    this.trailingIcon,
    this.isLoading = false,
    this.isFullWidth = false,
    this.isDisabled = false,
    this.height,
    this.width,
    this.padding,
    this.borderRadius,
    this.color,
    this.textColor,
    this.fontSize,
    this.fontWeight,
  });

  bool get _disabled => isDisabled || isLoading || onPressed == null;

  @override
  Widget build(BuildContext context) {
    final effectiveHeight = height ?? AppDimensions.buttonHeightMd;
    final effectiveRadius = borderRadius ?? AppDimensions.radiusMd;
    final isRtl = Directionality.of(context) == TextDirection.rtl;

    switch (variant) {
      case GulaButtonVariant.primary:
        return _buildElevated(effectiveHeight, effectiveRadius, isRtl);
      case GulaButtonVariant.secondary:
        return _buildSecondary(effectiveHeight, effectiveRadius, isRtl);
      case GulaButtonVariant.outline:
        return _buildOutline(effectiveHeight, effectiveRadius, isRtl);
      case GulaButtonVariant.text:
        return _buildText(effectiveHeight, effectiveRadius, isRtl);
      case GulaButtonVariant.danger:
        return _buildDanger(effectiveHeight, effectiveRadius, isRtl);
      case GulaButtonVariant.ghost:
        return _buildGhost(effectiveHeight, effectiveRadius, isRtl);
    }
  }

  Widget _buildElevated(double height, double radius, bool isRtl) {
    return SizedBox(
      width: isFullWidth ? double.infinity : width,
      height: height,
      child: ElevatedButton(
        onPressed: _disabled ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: color ?? AppColors.primary600,
          foregroundColor: textColor ?? AppColors.textOnPrimary,
          disabledBackgroundColor: AppColors.neutral300,
          disabledForegroundColor: AppColors.neutral500,
          padding: padding ?? const EdgeInsets.symmetric(horizontal: 20),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radius),
          ),
          elevation: 1,
          textStyle: TextStyle(
            fontSize: fontSize ?? 14,
            fontWeight: fontWeight ?? FontWeight.w500,
          ),
        ),
        child: _buildContent(isRtl),
      ),
    );
  }

  Widget _buildSecondary(double height, double radius, bool isRtl) {
    return SizedBox(
      width: isFullWidth ? double.infinity : width,
      height: height,
      child: ElevatedButton(
        onPressed: _disabled ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: color ?? AppColors.secondary500,
          foregroundColor: textColor ?? AppColors.textOnPrimary,
          disabledBackgroundColor: AppColors.neutral300,
          disabledForegroundColor: AppColors.neutral500,
          padding: padding ?? const EdgeInsets.symmetric(horizontal: 20),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radius),
          ),
          elevation: 1,
          textStyle: TextStyle(
            fontSize: fontSize ?? 14,
            fontWeight: fontWeight ?? FontWeight.w500,
          ),
        ),
        child: _buildContent(isRtl),
      ),
    );
  }

  Widget _buildOutline(double height, double radius, bool isRtl) {
    return SizedBox(
      width: isFullWidth ? double.infinity : width,
      height: height,
      child: OutlinedButton(
        onPressed: _disabled ? null : onPressed,
        style: OutlinedButton.styleFrom(
          foregroundColor: textColor ?? (color ?? AppColors.primary600),
          disabledForegroundColor: AppColors.neutral500,
          side: BorderSide(
            color: _disabled
                ? AppColors.neutral300
                : color ?? AppColors.primary500,
          ),
          padding: padding ?? const EdgeInsets.symmetric(horizontal: 20),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radius),
          ),
          textStyle: TextStyle(
            fontSize: fontSize ?? 14,
            fontWeight: fontWeight ?? FontWeight.w500,
          ),
        ),
        child: _buildContent(isRtl),
      ),
    );
  }

  Widget _buildText(double height, double radius, bool isRtl) {
    return SizedBox(
      width: isFullWidth ? double.infinity : width,
      height: height,
      child: TextButton(
        onPressed: _disabled ? null : onPressed,
        style: TextButton.styleFrom(
          foregroundColor: textColor ?? (color ?? AppColors.primary600),
          disabledForegroundColor: AppColors.neutral500,
          padding: padding ?? const EdgeInsets.symmetric(horizontal: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radius),
          ),
          textStyle: TextStyle(
            fontSize: fontSize ?? 14,
            fontWeight: fontWeight ?? FontWeight.w500,
          ),
        ),
        child: _buildContent(isRtl),
      ),
    );
  }

  Widget _buildDanger(double height, double radius, bool isRtl) {
    return SizedBox(
      width: isFullWidth ? double.infinity : width,
      height: height,
      child: ElevatedButton(
        onPressed: _disabled ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: color ?? AppColors.error500,
          foregroundColor: textColor ?? AppColors.textOnPrimary,
          disabledBackgroundColor: AppColors.neutral300,
          disabledForegroundColor: AppColors.neutral500,
          padding: padding ?? const EdgeInsets.symmetric(horizontal: 20),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radius),
          ),
          elevation: 1,
          textStyle: TextStyle(
            fontSize: fontSize ?? 14,
            fontWeight: fontWeight ?? FontWeight.w500,
          ),
        ),
        child: _buildContent(isRtl),
      ),
    );
  }

  Widget _buildGhost(double height, double radius, bool isRtl) {
    return SizedBox(
      width: isFullWidth ? double.infinity : width,
      height: height,
      child: TextButton(
        onPressed: _disabled ? null : onPressed,
        style: TextButton.styleFrom(
          foregroundColor: textColor ?? AppColors.textSecondary,
          disabledForegroundColor: AppColors.neutral500,
          padding: padding ?? const EdgeInsets.symmetric(horizontal: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radius),
          ),
          textStyle: TextStyle(
            fontSize: fontSize ?? 14,
            fontWeight: fontWeight ?? FontWeight.w400,
          ),
        ),
        child: _buildContent(isRtl),
      ),
    );
  }

  Widget _buildContent(bool isRtl) {
    if (isLoading) {
      return SizedBox(
        height: 20,
        width: 20,
        child: CircularProgressIndicator(
          strokeWidth: 2,
          valueColor: AlwaysStoppedAnimation<Color>(
            textColor ?? AppColors.textOnPrimary,
          ),
        ),
      );
    }

    if (icon == null && trailingIcon == null) {
      return Text(label);
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (icon != null && !isRtl) ...[
          Icon(icon, size: 18),
          const SizedBox(width: 8),
        ],
        if (icon != null && isRtl) ...[
          Icon(trailingIcon ?? icon, size: 18),
          const SizedBox(width: 8),
        ],
        Text(label),
        if (trailingIcon != null && !isRtl) ...[
          const SizedBox(width: 8),
          Icon(trailingIcon, size: 18),
        ],
        if (trailingIcon != null && isRtl) ...[
          const SizedBox(width: 8),
          Icon(icon ?? trailingIcon, size: 18),
        ],
      ],
    );
  }
}
