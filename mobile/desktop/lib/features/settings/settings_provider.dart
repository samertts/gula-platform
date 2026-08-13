import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SettingsProvider extends ChangeNotifier {
  bool _enableNotifications = true;
  bool _enableSound = true;
  bool _autoPrintLabels = false;
  bool _autoSync = true;
  int _syncInterval = 30;

  bool get enableNotifications => _enableNotifications;
  bool get enableSound => _enableSound;
  bool get autoPrintLabels => _autoPrintLabels;
  bool get autoSync => _autoSync;
  int get syncInterval => _syncInterval;

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

  void setSyncInterval(int v) {
    _syncInterval = v;
    notifyListeners();
  }
}

final settingsProvider = ChangeNotifierProvider<SettingsProvider>((ref) {
  return SettingsProvider();
});
