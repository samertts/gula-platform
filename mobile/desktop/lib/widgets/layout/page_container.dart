import 'package:flutter/material.dart';

import '../../core/theme/app_dimensions.dart';

class PageContainer extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;

  const PageContainer({super.key, required this.child, this.padding});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: padding ?? const EdgeInsets.all(AppDimensions.space4),
      child: child,
    );
  }
}
