import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';

enum GulaChipVariant { filled, outlined, light }

class GulaChip extends StatelessWidget {
  final String label;
  final IconData? icon;
  final Color? color;
  final Color? textColor;
  final GulaChipVariant variant;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;
  final bool isSelected;
  final double? height;
  final double? fontSize;

  const GulaChip({
    super.key,
    required this.label,
    this.icon,
    this.color,
    this.textColor,
    this.variant = GulaChipVariant.light,
    this.onTap,
    this.onDelete,
    this.isSelected = false,
    this.height,
    this.fontSize,
  });

  @override
  Widget build(BuildContext context) {
    final chipColor = color ?? AppColors.primary500;
    final effectiveHeight = height ?? AppDimensions.chipHeight;

    return RawChip(
      label: Text(
        label,
        style: TextStyle(
          fontSize: fontSize ?? 12,
          fontWeight: FontWeight.w500,
          color: _textColor(chipColor),
        ),
      ),
      avatar: icon != null
          ? Icon(icon, size: 16, color: _textColor(chipColor))
          : null,
      onPressed: onTap,
      onDeleted: onDelete,
      selected: isSelected,
      deleteIcon: onDelete != null
          ? Icon(Icons.close, size: 16, color: _textColor(chipColor))
          : null,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      labelPadding: const EdgeInsets.symmetric(horizontal: 4),
      selectedColor: chipColor.withOpacity(0.3),
      backgroundColor: _chipColor(chipColor),
      side: BorderSide(
        color: isSelected ? chipColor : chipColor.withOpacity(0.5),
        width: variant == GulaChipVariant.outlined ? 1.5 : 0,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusFull),
      ),
    );
  }

  Color _chipColor(Color chipColor) {
    switch (variant) {
      case GulaChipVariant.filled:
        return chipColor;
      case GulaChipVariant.outlined:
        return Colors.transparent;
      case GulaChipVariant.light:
        return chipColor.withOpacity(0.1);
    }
  }

  Color _textColor(Color chipColor) {
    switch (variant) {
      case GulaChipVariant.filled:
        return AppColors.textOnPrimary;
      case GulaChipVariant.outlined:
      case GulaChipVariant.light:
        return chipColor;
    }
  }
}
