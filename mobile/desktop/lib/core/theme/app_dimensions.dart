class AppDimensions {
  AppDimensions._();

  // Spacing (in logical pixels, matching UAP spacing tokens)
  static const double space0 = 0;
  static const double spacePx = 1;
  static const double space0_5 = 2;
  static const double space1 = 4;
  static const double space1_5 = 6;
  static const double space2 = 8;
  static const double space2_5 = 10;
  static const double space3 = 12;
  static const double space3_5 = 14;
  static const double space4 = 16;
  static const double space5 = 20;
  static const double space6 = 24;
  static const double space7 = 28;
  static const double space8 = 32;
  static const double space9 = 36;
  static const double space10 = 40;
  static const double space11 = 44;
  static const double space12 = 48;
  static const double space14 = 56;
  static const double space16 = 64;
  static const double space20 = 80;
  static const double space24 = 96;
  static const double space28 = 112;
  static const double space32 = 128;
  static const double space36 = 144;
  static const double space40 = 160;
  static const double space44 = 176;
  static const double space48 = 192;
  static const double space52 = 208;
  static const double space56 = 224;
  static const double space60 = 240;
  static const double space64 = 256;
  static const double space72 = 288;
  static const double space80 = 320;
  static const double space96 = 384;

  // Border Radius
  static const double radiusNone = 0;
  static const double radiusSm = 2;
  static const double radiusDefault = 4;
  static const double radiusMd = 6;
  static const double radiusLg = 8;
  static const double radiusXl = 12;
  static const double radius2xl = 16;
  static const double radius3xl = 24;
  static const double radiusFull = 9999;

  // Breakpoints
  static const double breakpointXs = 480;
  static const double breakpointSm = 640;
  static const double breakpointMd = 768;
  static const double breakpointLg = 1024;
  static const double breakpointXl = 1280;
  static const double breakpoint2xl = 1536;

  // Desktop layout
  static const double sidebarWidth = 260;
  static const double sidebarCollapsedWidth = 64;
  static const double appBarHeight = 56;
  static const double statusBarHeight = 32;
  static const double minWindowWidth = 800;
  static const double minWindowHeight = 600;

  // Component sizes
  static const double buttonHeightSm = 32;
  static const double buttonHeightMd = 40;
  static const double buttonHeightLg = 48;
  static const double inputHeight = 40;
  static const double chipHeight = 32;
  static const double badgeHeight = 20;
  static const double iconSizeSm = 16;
  static const double iconSizeMd = 20;
  static const double iconSizeLg = 24;
  static const double iconSizeXl = 32;
  static const double avatarSizeSm = 32;
  static const double avatarSizeMd = 40;
  static const double avatarSizeLg = 48;
  static const double tableRowHeight = 48;
  static const double kpiCardMinWidth = 200;
  static const double kpiCardMinHeight = 120;

  // Z-Index (matching UAP)
  static const int zHide = -1;
  static const int zBase = 0;
  static const int zDocked = 10;
  static const int zDropdown = 100;
  static const int zSticky = 200;
  static const int zBanner = 300;
  static const int zOverlay = 400;
  static const int zModal = 500;
  static const int zPopover = 600;
  static const int zToast = 800;
  static const int zTooltip = 900;

  // Animation durations
  static const Duration durationInstant = Duration.zero;
  static const Duration durationFast = Duration(milliseconds: 150);
  static const Duration durationNormal = Duration(milliseconds: 300);
  static const Duration durationSlow = Duration(milliseconds: 500);
  static const Duration durationSlower = Duration(milliseconds: 700);
  static const Duration durationSlowest = Duration(seconds: 1);
}
