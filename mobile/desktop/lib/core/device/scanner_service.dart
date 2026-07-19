import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';

class ScannerService {
  bool _isAvailable = false;

  final ValueNotifier<String?> scannedDocument = ValueNotifier(null);
  final ValueNotifier<bool> isScanning = ValueNotifier(false);

  bool get isAvailable => _isAvailable;

  Future<void> initialize() async {
    _isAvailable = true;
  }

  Future<String?> scanDocument() async {
    isScanning.value = true;
    try {
      await Future.delayed(const Duration(seconds: 1));
      return null;
    } catch (e) {
      debugPrint('Scanner error: $e');
      return null;
    } finally {
      isScanning.value = false;
    }
  }

  void dispose() {
    scannedDocument.dispose();
    isScanning.dispose();
  }
}
