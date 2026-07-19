import 'package:flutter/material.dart';

import '../../core/theme/app_dimensions.dart';

enum ScreenSize { mobile, tablet, desktop }

class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget? tablet;
  final Widget? desktop;

  const ResponsiveLayout({
    super.key,
    required this.mobile,
    this.tablet,
    this.desktop,
  });

  static ScreenSize getScreenSize(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    if (width < AppDimensions.breakpointMd) return ScreenSize.mobile;
    if (width < AppDimensions.breakpointLg) return ScreenSize.tablet;
    return ScreenSize.desktop;
  }

  static bool isMobile(BuildContext context) =>
      getScreenSize(context) == ScreenSize.mobile;

  static bool isTablet(BuildContext context) =>
      getScreenSize(context) == ScreenSize.tablet;

  static bool isDesktop(BuildContext context) =>
      getScreenSize(context) == ScreenSize.desktop;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= AppDimensions.breakpointLg) {
          return desktop ?? tablet ?? mobile;
        } else if (constraints.maxWidth >= AppDimensions.breakpointMd) {
          return tablet ?? mobile;
        } else {
          return mobile;
        }
      },
    );
  }
}

class ResponsiveBuilder extends StatelessWidget {
  final Widget Function(BuildContext context, ScreenSize size) builder;

  const ResponsiveBuilder({super.key, required this.builder});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        ScreenSize size;
        if (constraints.maxWidth >= AppDimensions.breakpointLg) {
          size = ScreenSize.desktop;
        } else if (constraints.maxWidth >= AppDimensions.breakpointMd) {
          size = ScreenSize.tablet;
        } else {
          size = ScreenSize.mobile;
        }
        return builder(context, size);
      },
    );
  }
}
