import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SettingsProvider extends ChangeNotifier {
  bool _enableNotifications = true;
  bool _enableSound = true;
  bool _autoPrintLabels = false;
  bool _autoSync = true;
  int _syncInterval = 30;
  double _textScale = 1.0;
  bool _highContrast = false;
  bool _reducedMotion = false;
  bool _screenReaderOptimized = false;
  bool _largerTouchTargets = false;
  bool _staticAlternatives = true;
  String _colorBlindMode = 'none';

  bool get enableNotifications => _enableNotifications;
  bool get enableSound => _enableSound;
  bool get autoPrintLabels => _autoPrintLabels;
  bool get autoSync => _autoSync;
  int get syncInterval => _syncInterval;
  double get textScale => _textScale;
  bool get highContrast => _highContrast;
  bool get reducedMotion => _reducedMotion;
  bool get screenReaderOptimized => _screenReaderOptimized;
  bool get largerTouchTargets => _largerTouchTargets;
  bool get staticAlternatives => _staticAlternatives;
  String get colorBlindMode => _colorBlindMode;

  void setNotifications(bool v) {
    _enableNotifications = v;
    notifyListeners();
  }

  void setSound(bool v) {
    _enableSound = v;
    notifyListeners();
  }

  void setAutoPrintLabels(bool v) {
    _autoPrintLabels = v;
    notifyListeners();
  }

  void setAutoSync(bool v) {
    _autoSync = v;
    notifyListeners();
  }

  void setTextScale(double v) {
    _textScale = v.clamp(0.85, 2.0).toDouble();
    notifyListeners();
  }

  void setHighContrast(bool v) {
    _highContrast = v;
    notifyListeners();
  }

  void setReducedMotion(bool v) {
    _reducedMotion = v;
    notifyListeners();
  }

  void setScreenReaderOptimized(bool v) {
    _screenReaderOptimized = v;
    notifyListeners();
  }

  void setLargerTouchTargets(bool v) {
    _largerTouchTargets = v;
    notifyListeners();
  }

  void setStaticAlternatives(bool v) {
    _staticAlternatives = v;
    notifyListeners();
  }

  void setColorBlindMode(String v) {
    const allowed = {
      'none',
      'protanopia',
      'deuteranopia',
      'tritanopia',
      'monochrome',
    };
    _colorBlindMode = allowed.contains(v) ? v : 'none';
    notifyListeners();
  }

  void setSyncInterval(int v) {
    _syncInterval = v;
    notifyListeners();
  }
}

final settingsProvider = ChangeNotifierProvider<SettingsProvider>((ref) {
  return SettingsProvider();
});
