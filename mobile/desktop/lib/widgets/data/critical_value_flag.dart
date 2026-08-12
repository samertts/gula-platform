import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';

class CriticalValueFlag extends StatelessWidget {
  final String flag;
  final double? size;

  const CriticalValueFlag({
    super.key,
    required this.flag,
    this.size,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size ?? 28,
      height: size ?? 28,
      decoration: BoxDecoration(
        color: _color,
        borderRadius: BorderRadius.circular(AppDimensions.radiusSm),
      ),
      child: Center(
        child: Text(
          _label,
          style: TextStyle(
            color: Colors.white,
            fontSize: (size ?? 28) * 0.45,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Color get _color {
    switch (flag) {
      case 'h':
        return AppColors.urgent;
      case 'l':
        return AppColors.info500;
      case 'critical':
        return AppColors.critical;
      case 'high':
        return AppColors.urgent;
      case 'low':
        return AppColors.info500;
      default:
        return AppColors.success500;
    }
  }

  String get _label {
    switch (flag) {
      case 'h':
      case 'high':
        return '↑';
      case 'l':
      case 'low':
        return '↓';
      case 'critical':
        return '!';
      default:
        return '';
    }
  }
}
