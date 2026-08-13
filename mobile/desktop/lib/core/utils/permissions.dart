import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:permission_handler/permission_handler.dart';

class AppPermissions {
  AppPermissions._();

  static Future<bool> requestCamera() => _request(Permission.camera);
  static Future<bool> requestMicrophone() => _request(Permission.microphone);
  static Future<bool> requestStorage() => _request(Permission.storage);
  static Future<bool> requestPhotos() => _request(Permission.photos);
  static Future<bool> requestLocation() => _request(Permission.location);
  static Future<bool> requestBluetooth() => _request(Permission.bluetooth);
  static Future<bool> requestBluetoothScan() =>
      _request(Permission.bluetoothScan);
  static Future<bool> requestBluetoothConnect() =>
      _request(Permission.bluetoothConnect);
  static Future<bool> requestNotification() =>
      _request(Permission.notification);
  static Future<bool> requestReminders() => _request(Permission.reminders);

  static Future<bool> requestPrint() async {
    if (Platform.isWindows || Platform.isLinux) return true;
    return true;
  }

  static Future<bool> _request(Permission permission) async {
    try {
      final status = await permission.request();
      return status.isGranted;
    } catch (e) {
      debugPrint('Permission request error: $e');
      return false;
    }
  }

  static Future<bool> checkCamera() => _check(Permission.camera);
  static Future<bool> checkMicrophone() => _check(Permission.microphone);
  static Future<bool> checkStorage() => _check(Permission.storage);
  static Future<bool> checkPhotos() => _check(Permission.photos);
  static Future<bool> checkLocation() => _check(Permission.location);
  static Future<bool> checkBluetooth() => _check(Permission.bluetooth);
  static Future<bool> checkNotification() => _check(Permission.notification);

  static Future<bool> _check(Permission permission) async {
    try {
      final status = await permission.status;
      return status.isGranted;
    } catch (e) {
      debugPrint('Permission check error: $e');
      return false;
    }
  }

  static Future<bool> openSettings() async {
    try {
      return await openAppSettings();
    } catch (e) {
      debugPrint('Open settings error: $e');
      return false;
    }
  }
}
