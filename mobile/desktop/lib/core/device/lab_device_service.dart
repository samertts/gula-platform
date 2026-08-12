import 'dart:async';

import 'package:flutter/foundation.dart';

class LabDeviceInfo {
  final String id;
  final String name;
  final String model;
  final String manufacturer;
  final String connectionType;
  final String status;
  final Map<String, dynamic> capabilities;

  LabDeviceInfo({
    required this.id,
    required this.name,
    required this.model,
    required this.manufacturer,
    this.connectionType = 'bluetooth',
    this.status = 'disconnected',
    this.capabilities = const {},
  });
}

class LabDeviceReading {
  final String deviceId;
  final String testCode;
  final String testName;
  final dynamic value;
  final String unit;
  final DateTime timestamp;
  final Map<String, dynamic> raw;

  LabDeviceReading({
    required this.deviceId,
    required this.testCode,
    required this.testName,
    required this.value,
    required this.unit,
    required this.timestamp,
    this.raw = const {},
  });
}

class LabDeviceService {
  final List<LabDeviceInfo> _connectedDevices = [];
  final ValueNotifier<List<LabDeviceInfo>> connectedDevicesNotifier =
      ValueNotifier([]);
  final ValueNotifier<LabDeviceReading?> latestReading = ValueNotifier(null);
  final ValueNotifier<bool> isListening = ValueNotifier(false);

  StreamController<LabDeviceReading>? _readingController;
  StreamSubscription? _deviceSubscription;

  Stream<LabDeviceReading>? get readings => _readingController?.stream;

  Future<List<LabDeviceInfo>> discoverDevices() async {
    await Future.delayed(const Duration(seconds: 2));
    return [];
  }

  Future<bool> connectToDevice(LabDeviceInfo device) async {
    try {
      await Future.delayed(const Duration(seconds: 1));
      _connectedDevices.add(device);
      connectedDevicesNotifier.value = List.from(_connectedDevices);
      return true;
    } catch (e) {
      debugPrint('Device connect error: $e');
      return false;
    }
  }

  Future<void> disconnectDevice(String deviceId) async {
    _connectedDevices.removeWhere((d) => d.id == deviceId);
    connectedDevicesNotifier.value = List.from(_connectedDevices);
  }

  Future<void> startListening(String deviceId) async {
    _readingController = StreamController<LabDeviceReading>.broadcast();
    isListening.value = true;
  }

  Future<void> stopListening() async {
    await _readingController?.close();
    _readingController = null;
    isListening.value = false;
  }

  void dispose() {
    _readingController?.close();
    connectedDevicesNotifier.dispose();
    latestReading.dispose();
    isListening.dispose();
  }
}
