import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';

class BluetoothDeviceInfo {
  final String id;
  final String name;
  final int rssi;
  final List<String> serviceUuids;

  BluetoothDeviceInfo({
    required this.id,
    required this.name,
    this.rssi = 0,
    this.serviceUuids = const [],
  });
}

class BluetoothService {
  bool _isScanning = false;
  bool _isAvailable = false;

  final List<BluetoothDeviceInfo> _discoveredDevices = [];
  final ValueNotifier<List<BluetoothDeviceInfo>> discoveredDevicesNotifier =
      ValueNotifier([]);
  final ValueNotifier<bool> isScanningNotifier = ValueNotifier(false);
  final ValueNotifier<bool> isAvailableNotifier = ValueNotifier(false);

  StreamSubscription? _scanSubscription;

  bool get isScanning => _isScanning;
  bool get isAvailable => _isAvailable;
  List<BluetoothDeviceInfo> get discoveredDevices =>
      List.unmodifiable(_discoveredDevices);

  Future<void> initialize() async {
    try {
      await FlutterBluePlus.instance.adapterState.where((s) => s == BluetoothAdapterState.on).first;
      _isAvailable = true;
      isAvailableNotifier.value = true;
    } catch (e) {
      debugPrint('Bluetooth init error: $e');
      _isAvailable = false;
      isAvailableNotifier.value = false;
    }
  }

  Future<void> startScan({Duration timeout = const Duration(seconds: 10)}) async {
    if (_isScanning) return;
    if (!_isAvailable) return;

    _isScanning = true;
    isScanningNotifier.value = true;
    _discoveredDevices.clear();

    try {
      await FlutterBluePlus.instance.startScan(timeout: timeout);

      _scanSubscription = FlutterBluePlus.instance.scanResults.listen((results) {
        _discoveredDevices.clear();
        for (final result in results) {
          _discoveredDevices.add(BluetoothDeviceInfo(
            id: result.device.remoteId.str,
            name: result.device.platformName.isEmpty
                ? 'Unknown Device'
                : result.device.platformName,
            rssi: result.rssi,
            serviceUuids: result.advertisementData.serviceUuids ?? [],
          ));
        }
        discoveredDevicesNotifier.value = List.from(_discoveredDevices);
      });
    } catch (e) {
      debugPrint('Bluetooth scan error: $e');
    }
  }

  Future<void> stopScan() async {
    try {
      await FlutterBluePlus.instance.stopScan();
    } catch (_) {}
    _isScanning = false;
    isScanningNotifier.value = false;
    await _scanSubscription?.cancel();
    _scanSubscription = null;
  }

  Future<bool> connectToDevice(String deviceId) async {
    try {
      final device = FlutterBluePlus.instance.knownDevices
          .where((d) => d.remoteId.str == deviceId)
          .firstOrNull;
      if (device == null) return false;
      await device.connect();
      return true;
    } catch (e) {
      debugPrint('Bluetooth connect error: $e');
      return false;
    }
  }

  Future<void> disconnectFromDevice(String deviceId) async {
    try {
      final device = FlutterBluePlus.instance.knownDevices
          .where((d) => d.remoteId.str == deviceId)
          .firstOrNull;
      if (device != null) {
        await device.disconnect();
      }
    } catch (e) {
      debugPrint('Bluetooth disconnect error: $e');
    }
  }

  Future<void> dispose() async {
    await stopScan();
  }
}
