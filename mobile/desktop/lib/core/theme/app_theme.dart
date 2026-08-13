import 'package:flutter/material.dart';
import 'package:flex_color_scheme/flex_color_scheme.dart';

import 'app_colors.dart';
import 'app_typography.dart';
import 'app_dimensions.dart';

class AppTheme {
  AppTheme._();

  static ThemeData get light => _buildLight();
  static ThemeData get dark => _buildDark();
  static ThemeData get highContrast => _buildHighContrast();

  static ThemeData _buildLight() {
    return FlexThemeData.light(
      scheme: FlexScheme.green,
      colors: FlexSchemeColor(
        primary: AppColors.primary600,
        primaryContainer: AppColors.primary100,
        secondary: AppColors.secondary500,
        secondaryContainer: AppColors.secondary50,
        tertiary: AppColors.accent500,
        tertiaryContainer: AppColors.accent100,
        appBarColor: AppColors.primary700,
        error: AppColors.error500,
        errorContainer: AppColors.error50,
      ),
      surfaceMode: FlexSurfaceMode.levelSurfacesLowScaffold,
      blendLevel: 15,
      appBarStyle: FlexAppBarStyle.primary,
      appBarOpacity: 1.0,
      tabBarStyle: FlexTabBarStyle.forBackground,
      tooltipsMatchBackground: true,
      bottomAppBarElevation: 2,
    ).copyWith(
      colorScheme: const ColorScheme(
        brightness: Brightness.light,
        primary: AppColors.primary600,
        onPrimary: AppColors.textOnPrimary,
        primaryContainer: AppColors.primary100,
        onPrimaryContainer: AppColors.primary900,
        secondary: AppColors.secondary500,
        onSecondary: AppColors.textOnPrimary,
        secondaryContainer: AppColors.secondary50,
        onSecondaryContainer: AppColors.secondary900,
        tertiary: AppColors.accent500,
        onTertiary: AppColors.textOnPrimary,
        tertiaryContainer: AppColors.accent100,
        onTertiaryContainer: AppColors.accent900,
        error: AppColors.error500,
        onError: AppColors.textOnPrimary,
        errorContainer: AppColors.error50,
        onErrorContainer: AppColors.error900,
        surface: AppColors.surfaceLight,
        onSurface: AppColors.textPrimary,
        onSurfaceVariant: AppColors.textSecondary,
        outline: AppColors.border,
        outlineVariant: AppColors.divider,
        shadow: Color(0x1A000000),
        scrim: Color(0x66000000),
        inverseSurface: Color(0xFF2C2C2C),
        onInverseSurface: Color(0xFFE0E0E0),
        inversePrimary: AppColors.primary200,
        surfaceTint: AppColors.primary500,
      ),
      textTheme: AppTypography.arabicTextTheme,
      primaryTextTheme: AppTypography.arabicTextTheme,
      inputDecorationTheme: _inputDecorationTheme(),
      elevatedButtonTheme: _elevatedButtonTheme(),
      outlinedButtonTheme: _outlinedButtonTheme(),
      textButtonTheme: _textButtonTheme(),
      cardTheme: _cardTheme(),
      chipTheme: _chipTheme(),
      bottomSheetTheme: _bottomSheetTheme(),
      dialogTheme: _dialogTheme(),
      appBarTheme: _appBarTheme(),
      navigationBarTheme: _navigationBarTheme(),
      navigationRailTheme: _navigationRailTheme(),
      dividerTheme: _dividerTheme(),
      checkboxTheme: _checkboxTheme(),
      radioTheme: _radioTheme(),
      switchTheme: _switchTheme(),
      sliderTheme: _sliderTheme(),
      tooltipTheme: _tooltipTheme(),
      menuTheme: _menuTheme(),
      popupMenuTheme: _popupMenuTheme(),
      badgeTheme: _badgeTheme(),
      expansionTileTheme: _expansionTileTheme(),
      listTileTheme: _listTileTheme(),
      floatingActionButtonTheme: _fabTheme(),
      progressIndicatorTheme: _progressIndicatorTheme(),
      scaffoldBackgroundColor: AppColors.neutral50,
    );
  }

  static ThemeData _buildDark() {
    return FlexThemeData.dark(
      scheme: FlexScheme.green,
      colors: FlexSchemeColor(
        primary: AppColors.primary400,
        primaryContainer: AppColors.primary800,
        secondary: AppColors.secondary300,
        secondaryContainer: AppColors.secondary800,
        tertiary: AppColors.accent400,
        tertiaryContainer: AppColors.accent800,
        appBarColor: AppColors.neutral900,
        error: AppColors.error400,
        errorContainer: AppColors.error800,
      ),
      surfaceMode: FlexSurfaceMode.levelSurfacesLowScaffold,
      blendLevel: 20,
      appBarStyle: FlexAppBarStyle.primary,
      appBarOpacity: 1.0,
      tooltipsMatchBackground: true,
    ).copyWith(
      colorScheme: const ColorScheme(
        brightness: Brightness.dark,
        primary: AppColors.primary400,
        onPrimary: Color(0xFF003300),
        primaryContainer: AppColors.primary800,
        onPrimaryContainer: AppColors.primary100,
        secondary: AppColors.secondary300,
        onSecondary: Color(0xFF003549),
        secondaryContainer: AppColors.secondary800,
        onSecondaryContainer: AppColors.secondary50,
        tertiary: AppColors.accent400,
        onTertiary: Color(0xFF4E2700),
        tertiaryContainer: AppColors.accent800,
        onTertiaryContainer: AppColors.accent50,
        error: AppColors.error400,
        onError: Color(0xFF601410),
        errorContainer: AppColors.error800,
        onErrorContainer: AppColors.error50,
        surface: AppColors.surfaceDark,
        onSurface: Color(0xFFE0E0E0),
        onSurfaceVariant: Color(0xFF9E9E9E),
        outline: Color(0xFF424242),
        outlineVariant: Color(0xFF333333),
        shadow: Color(0x33000000),
        scrim: Color(0x99000000),
        inverseSurface: Color(0xFFE0E0E0),
        onInverseSurface: Color(0xFF2C2C2C),
        inversePrimary: AppColors.primary600,
        surfaceTint: AppColors.primary400,
      ),
      textTheme: AppTypography.arabicTextTheme.apply(
        bodyColor: const Color(0xFFE0E0E0),
        displayColor: const Color(0xFFFFFFFF),
      ),
      primaryTextTheme: AppTypography.arabicTextTheme.apply(
        bodyColor: const Color(0xFFE0E0E0),
        displayColor: const Color(0xFFFFFFFF),
      ),
      inputDecorationTheme: _inputDecorationThemeDark(),
      elevatedButtonTheme: _elevatedButtonThemeDark(),
      outlinedButtonTheme: _outlinedButtonThemeDark(),
      textButtonTheme: _textButtonTheme(),
      cardTheme: _cardThemeDark(),
      chipTheme: _chipThemeDark(),
      bottomSheetTheme: _bottomSheetThemeDark(),
      dialogTheme: _dialogThemeDark(),
      appBarTheme: _appBarThemeDark(),
      navigationBarTheme: _navigationBarThemeDark(),
      navigationRailTheme: _navigationRailThemeDark(),
      dividerTheme: _dividerThemeDark(),
      checkboxTheme: _checkboxThemeDark(),
      radioTheme: _radioThemeDark(),
      switchTheme: _switchThemeDark(),
      sliderTheme: _sliderThemeDark(),
      tooltipTheme: _tooltipThemeDark(),
      menuTheme: _menuThemeDark(),
      popupMenuTheme: _popupMenuThemeDark(),
      badgeTheme: _badgeThemeDark(),
      expansionTileTheme: _expansionTileThemeDark(),
      listTileTheme: _listTileThemeDark(),
      floatingActionButtonTheme: _fabThemeDark(),
      progressIndicatorTheme: _progressIndicatorThemeDark(),
      scaffoldBackgroundColor: const Color(0xFF121212),
    );
  }

  static ThemeData _buildHighContrast() {
    final base = _buildLight();
    return base.copyWith(
      colorScheme: base.colorScheme.copyWith(
        primary: AppColors.primary900,
        onPrimary: AppColors.textOnPrimary,
        secondary: AppColors.secondary900,
        onSecondary: AppColors.textOnPrimary,
        error: AppColors.error900,
        onError: AppColors.textOnPrimary,
        surface: AppColors.surfaceLight,
        onSurface: AppColors.neutral950,
        outline: AppColors.neutral900,
      ),
      textTheme: AppTypography.arabicTextTheme.apply(
        bodyColor: AppColors.neutral950,
        displayColor: AppColors.neutral950,
      ),
      dividerTheme: const DividerThemeData(
        color: AppColors.neutral900,
        thickness: 2,
        space: 1,
      ),
      inputDecorationTheme: base.inputDecorationTheme.copyWith(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
          borderSide: const BorderSide(color: AppColors.neutral900, width: 2),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
          borderSide: const BorderSide(color: AppColors.neutral900, width: 2),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
          borderSide: const BorderSide(color: AppColors.primary900, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
          borderSide: const BorderSide(color: AppColors.error900, width: 2),
        ),
      ),
    );
  }

  // Light theme sub-component themes
  static InputDecorationTheme _inputDecorationTheme() {
    return InputDecorationTheme(
      filled: true,
      fillColor: AppColors.surfaceLight,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: AppDimensions.space3,
        vertical: AppDimensions.space2_5,
      ),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        borderSide: const BorderSide(color: AppColors.primary500, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        borderSide: const BorderSide(color: AppColors.error500),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        borderSide: const BorderSide(color: AppColors.error500, width: 2),
      ),
      disabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        borderSide: const BorderSide(color: AppColors.neutral200),
      ),
      labelStyle: const TextStyle(
        color: AppColors.textSecondary,
        fontSize: 14,
        fontWeight: FontWeight.w400,
      ),
      hintStyle: const TextStyle(
        color: AppColors.neutral400,
        fontSize: 14,
      ),
      errorStyle: const TextStyle(
        color: AppColors.error500,
        fontSize: 12,
      ),
      helperStyle: const TextStyle(
        color: AppColors.textSecondary,
        fontSize: 12,
      ),
      prefixStyle: const TextStyle(color: AppColors.textPrimary),
      suffixStyle: const TextStyle(color: AppColors.textPrimary),
    );
  }

  static ElevatedButtonThemeData _elevatedButtonTheme() {
    return ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        minimumSize: const Size(0, AppDimensions.buttonHeightMd),
        padding: const EdgeInsets.symmetric(
          horizontal: AppDimensions.space4,
          vertical: AppDimensions.space2,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        ),
        textStyle: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  static OutlinedButtonThemeData _outlinedButtonTheme() {
    return OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(0, AppDimensions.buttonHeightMd),
        padding: const EdgeInsets.symmetric(
          horizontal: AppDimensions.space4,
          vertical: AppDimensions.space2,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        ),
        side: const BorderSide(color: AppColors.primary500),
        textStyle: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  static TextButtonThemeData _textButtonTheme() {
    return TextButtonThemeData(
      style: TextButton.styleFrom(
        minimumSize: const Size(0, AppDimensions.buttonHeightMd),
        padding: const EdgeInsets.symmetric(
          horizontal: AppDimensions.space3,
          vertical: AppDimensions.space1_5,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        ),
        textStyle: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  static CardThemeData _cardTheme() {
    return CardThemeData(
      elevation: 1,
      margin: const EdgeInsets.all(AppDimensions.space2),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusLg),
        side: const BorderSide(color: AppColors.neutral100),
      ),
      clipBehavior: Clip.antiAlias,
    );
  }

  static ChipThemeData _chipTheme() {
    return ChipThemeData(
      padding: const EdgeInsets.symmetric(horizontal: AppDimensions.space2),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusFull),
      ),
      labelStyle: const TextStyle(fontSize: 12),
      secondaryLabelStyle: const TextStyle(fontSize: 12),
    );
  }

  static BottomSheetThemeData _bottomSheetTheme() {
    return const BottomSheetThemeData(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(AppDimensions.radiusXl),
        ),
      ),
      elevation: 2,
    );
  }

  static DialogThemeData _dialogTheme() {
    return DialogThemeData(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusXl),
      ),
      elevation: 4,
    );
  }

  static AppBarTheme _appBarTheme() {
    return const AppBarTheme(
      elevation: 0,
      centerTitle: false,
      titleSpacing: 0,
      toolbarHeight: AppDimensions.appBarHeight,
    );
  }

  static NavigationBarThemeData _navigationBarTheme() {
    return NavigationBarThemeData(
      height: 64,
      labelBehavior: NavigationDestinationLabelBehavior.onlyShowSelected,
      indicatorShape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusLg),
      ),
    );
  }

  static NavigationRailThemeData _navigationRailTheme() {
    return NavigationRailThemeData(
      minWidth: 72,
      groupAlignment: 0,
      labelType: NavigationRailLabelType.all,
    );
  }

  static DividerThemeData _dividerTheme() {
    return const DividerThemeData(
      color: AppColors.divider,
      thickness: 1,
      space: 1,
    );
  }

  static CheckboxThemeData _checkboxTheme() {
    return CheckboxThemeData(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusSm),
      ),
      checkColor: WidgetStateProperty.all(AppColors.textOnPrimary),
    );
  }

  static RadioThemeData _radioTheme() {
    return RadioThemeData(
      fillColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return AppColors.primary500;
        return AppColors.neutral500;
      }),
    );
  }

  static SwitchThemeData _switchTheme() {
    return SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return AppColors.primary500;
        return AppColors.neutral400;
      }),
      trackColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return AppColors.primary200;
        return AppColors.neutral300;
      }),
    );
  }

  static SliderThemeData _sliderTheme() {
    return SliderThemeData(
      activeTrackColor: AppColors.primary500,
      inactiveTrackColor: AppColors.primary100,
      thumbColor: AppColors.primary500,
      overlayColor: AppColors.primary50,
      valueIndicatorColor: AppColors.primary500,
      valueIndicatorTextStyle: const TextStyle(color: AppColors.textOnPrimary),
    );
  }

  static TooltipThemeData _tooltipTheme() {
    return TooltipThemeData(
      decoration: BoxDecoration(
        color: AppColors.neutral800,
        borderRadius: BorderRadius.circular(AppDimensions.radiusSm),
      ),
      textStyle: const TextStyle(color: AppColors.textOnDark, fontSize: 12),
      padding: const EdgeInsets.symmetric(
        horizontal: AppDimensions.space2,
        vertical: AppDimensions.space1,
      ),
    );
  }

  static MenuThemeData _menuTheme() {
    return MenuThemeData(
      style: MenuStyle(
        elevation: WidgetStateProperty.all(2),
        shape: WidgetStateProperty.all(
          RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
          ),
        ),
      ),
    );
  }

  static PopupMenuThemeData _popupMenuTheme() {
    return PopupMenuThemeData(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
      ),
    );
  }

  static BadgeThemeData _badgeTheme() {
    return BadgeThemeData(
      backgroundColor: AppColors.primary500,
      textColor: AppColors.textOnPrimary,
      smallSize: 8,
      largeSize: 20,
    );
  }

  static ExpansionTileThemeData _expansionTileTheme() {
    return ExpansionTileThemeData(
      iconColor: AppColors.textSecondary,
      collapsedIconColor: AppColors.textSecondary,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
      ),
      collapsedShape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
      ),
    );
  }

  static ListTileThemeData _listTileTheme() {
    return ListTileThemeData(
      contentPadding: const EdgeInsets.symmetric(
        horizontal: AppDimensions.space4,
        vertical: 0,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
      ),
    );
  }

  static FloatingActionButtonThemeData _fabTheme() {
    return FloatingActionButtonThemeData(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusXl),
      ),
    );
  }

  static ProgressIndicatorThemeData _progressIndicatorTheme() {
    return const ProgressIndicatorThemeData(
      color: AppColors.primary500,
      linearTrackColor: AppColors.primary100,
      circularTrackColor: AppColors.primary100,
    );
  }

  // Dark theme variants
  static InputDecorationTheme _inputDecorationThemeDark() {
    return _inputDecorationTheme().copyWith(
      fillColor: const Color(0xFF2C2C2C),
      border: const OutlineInputBorder(
        borderSide: BorderSide(color: Color(0xFF424242)),
      ),
      enabledBorder: const OutlineInputBorder(
        borderSide: BorderSide(color: Color(0xFF424242)),
      ),
    );
  }

  static ElevatedButtonThemeData _elevatedButtonThemeDark() {
    return ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary400,
        foregroundColor: const Color(0xFF003300),
        minimumSize: const Size(0, AppDimensions.buttonHeightMd),
        padding: const EdgeInsets.symmetric(
          horizontal: AppDimensions.space4,
          vertical: AppDimensions.space2,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        ),
      ),
    );
  }

  static OutlinedButtonThemeData _outlinedButtonThemeDark() {
    return OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.primary300,
        side: const BorderSide(color: AppColors.primary400),
        minimumSize: const Size(0, AppDimensions.buttonHeightMd),
        padding: const EdgeInsets.symmetric(
          horizontal: AppDimensions.space4,
          vertical: AppDimensions.space2,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        ),
      ),
    );
  }

  static CardThemeData _cardThemeDark() {
    return CardThemeData(
      elevation: 2,
      margin: const EdgeInsets.all(AppDimensions.space2),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusLg),
        side: const BorderSide(color: Color(0xFF333333)),
      ),
      clipBehavior: Clip.antiAlias,
      color: const Color(0xFF2C2C2C),
    );
  }

  static ChipThemeData _chipThemeDark() {
    return _chipTheme();
  }

  static BottomSheetThemeData _bottomSheetThemeDark() {
    return BottomSheetThemeData(
      backgroundColor: const Color(0xFF2C2C2C),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(AppDimensions.radiusXl),
        ),
      ),
      elevation: 2,
    );
  }

  static DialogThemeData _dialogThemeDark() {
    return DialogThemeData(
      backgroundColor: const Color(0xFF2C2C2C),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusXl),
      ),
      elevation: 4,
    );
  }

  static AppBarTheme _appBarThemeDark() {
    return const AppBarTheme(
      elevation: 0,
      centerTitle: false,
      titleSpacing: 0,
      toolbarHeight: AppDimensions.appBarHeight,
    );
  }

  static NavigationBarThemeData _navigationBarThemeDark() {
    return NavigationBarThemeData(
      backgroundColor: const Color(0xFF1E1E1E),
      indicatorColor: AppColors.primary800,
      height: 64,
      labelBehavior: NavigationDestinationLabelBehavior.onlyShowSelected,
    );
  }

  static NavigationRailThemeData _navigationRailThemeDark() {
    return NavigationRailThemeData(
      backgroundColor: const Color(0xFF1E1E1E),
      minWidth: 72,
      groupAlignment: 0,
      labelType: NavigationRailLabelType.all,
    );
  }

  static DividerThemeData _dividerThemeDark() {
    return const DividerThemeData(
      color: Color(0xFF333333),
      thickness: 1,
      space: 1,
    );
  }

  static CheckboxThemeData _checkboxThemeDark() {
    return CheckboxThemeData(
      fillColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return AppColors.primary400;
        return AppColors.neutral600;
      }),
      checkColor: WidgetStateProperty.all(const Color(0xFF003300)),
    );
  }

  static RadioThemeData _radioThemeDark() {
    return RadioThemeData(
      fillColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return AppColors.primary400;
        return AppColors.neutral500;
      }),
    );
  }

  static SwitchThemeData _switchThemeDark() {
    return SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return AppColors.primary400;
        return AppColors.neutral500;
      }),
      trackColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return AppColors.primary700;
        return AppColors.neutral600;
      }),
    );
  }

  static SliderThemeData _sliderThemeDark() {
    return SliderThemeData(
      activeTrackColor: AppColors.primary400,
      inactiveTrackColor: AppColors.primary800,
      thumbColor: AppColors.primary400,
      overlayColor: AppColors.primary700,
      valueIndicatorColor: AppColors.primary400,
      valueIndicatorTextStyle: const TextStyle(color: Color(0xFF003300)),
    );
  }

  static TooltipThemeData _tooltipThemeDark() {
    return TooltipThemeData(
      decoration: BoxDecoration(
        color: const Color(0xFF424242),
        borderRadius: BorderRadius.circular(AppDimensions.radiusSm),
      ),
      textStyle: const TextStyle(color: Color(0xFFE0E0E0), fontSize: 12),
      padding: const EdgeInsets.symmetric(
        horizontal: AppDimensions.space2,
        vertical: AppDimensions.space1,
      ),
    );
  }

  static MenuThemeData _menuThemeDark() {
    return MenuThemeData(
      style: MenuStyle(
        backgroundColor: WidgetStateProperty.all(const Color(0xFF2C2C2C)),
        elevation: WidgetStateProperty.all(4),
        shape: WidgetStateProperty.all(
          RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
          ),
        ),
      ),
    );
  }

  static PopupMenuThemeData _popupMenuThemeDark() {
    return PopupMenuThemeData(
      color: const Color(0xFF2C2C2C),
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
      ),
    );
  }

  static BadgeThemeData _badgeThemeDark() {
    return BadgeThemeData(
      backgroundColor: AppColors.primary400,
      textColor: const Color(0xFF003300),
      smallSize: 8,
      largeSize: 20,
    );
  }

  static ExpansionTileThemeData _expansionTileThemeDark() {
    return ExpansionTileThemeData(
      iconColor: const Color(0xFF9E9E9E),
      collapsedIconColor: const Color(0xFF9E9E9E),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
      ),
      collapsedShape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
      ),
    );
  }

  static ListTileThemeData _listTileThemeDark() {
    return ListTileThemeData(
      contentPadding: const EdgeInsets.symmetric(
        horizontal: AppDimensions.space4,
        vertical: 0,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
      ),
    );
  }

  static FloatingActionButtonThemeData _fabThemeDark() {
    return FloatingActionButtonThemeData(
      backgroundColor: AppColors.primary400,
      foregroundColor: const Color(0xFF003300),
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusXl),
      ),
    );
  }

  static ProgressIndicatorThemeData _progressIndicatorThemeDark() {
    return const ProgressIndicatorThemeData(
      color: AppColors.primary400,
      linearTrackColor: Color(0xFF1B5E20),
      circularTrackColor: Color(0xFF1B5E20),
    );
  }
}
