import 'dart:async';


class CameraService {
  bool _isInitialized = false;

  bool get isInitialized => _isInitialized;

  Future<void> initialize() async {
    _isInitialized = true;
  }

  Future<void> dispose() async {
    _isInitialized = false;
  }
}
