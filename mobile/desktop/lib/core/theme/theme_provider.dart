import 'package:flutter/material.dart';

enum AppThemeMode { light, dark, highContrast }

class ThemeProvider extends ChangeNotifier {
  AppThemeMode _mode = AppThemeMode.light;
  Locale _locale = const Locale('ar', 'IQ');
  bool _isRtl = true;

  AppThemeMode get mode => _mode;
  Locale get locale => _locale;
  bool get isRtl => _isRtl;
  ThemeMode get themeMode {
    switch (_mode) {
      case AppThemeMode.light:
        return ThemeMode.light;
      case AppThemeMode.dark:
        return ThemeMode.dark;
      case AppThemeMode.highContrast:
        return ThemeMode.light;
    }
  }

  void setThemeMode(AppThemeMode mode) {
    _mode = mode;
    notifyListeners();
  }

  void toggleTheme() {
    switch (_mode) {
      case AppThemeMode.light:
        _mode = AppThemeMode.dark;
      case AppThemeMode.dark:
        _mode = AppThemeMode.light;
      case AppThemeMode.highContrast:
        _mode = AppThemeMode.light;
    }
    notifyListeners();
  }

  void setLocale(Locale locale) {
    _locale = locale;
    _isRtl = locale.languageCode == 'ar';
    notifyListeners();
  }

  void toggleRtl() {
    _isRtl = !_isRtl;
    notifyListeners();
  }
}
