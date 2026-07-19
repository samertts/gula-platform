import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:barcode/barcode.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/rendering.dart';
import 'package:qr_flutter/qr_flutter.dart';

class BarcodeService {
  static Uint8List? generateCode128(String data, {int width = 200, int height = 80}) {
    try {
      final barcode = Barcode.code128();
      final svg = barcode.toSvg(data, width: width, height: height);
      return svg.codeUnits;
    } catch (e) {
      debugPrint('Barcode generation error: $e');
      return null;
    }
  }

  static Uint8List? generateEan13(String data, {int width = 200, int height = 80}) {
    try {
      final barcode = Barcode.ean13();
      final svg = barcode.toSvg(data, width: width, height: height);
      return svg.codeUnits;
    } catch (e) {
      debugPrint('EAN-13 generation error: $e');
      return null;
    }
  }

  static Uint8List? generateQrCode(String data, {int size = 200}) {
    try {
      final qr = Barcode.qrCode();
      final svg = qr.toSvg(data, width: size, height: size);
      return svg.codeUnits;
    } catch (e) {
      debugPrint('QR generation error: $e');
      return null;
    }
  }

  static bool isValidBarcode(String barcode) {
    if (barcode.isEmpty) return false;
    return RegExp(r'^[A-Z0-9]{6,20}$').hasMatch(barcode);
  }
}
