import 'dart:async';

import 'package:esc_pos_bluetooth/esc_pos_bluetooth.dart';
import 'package:esc_pos_utils/esc_pos_utils.dart';
import 'package:flutter/foundation.dart';

import 'bluetooth_service.dart';

class BlePrinterService {
  PrinterBluetoothManager _printerManager = PrinterBluetoothManager();
  List<PrinterBluetooth> _printers = [];
  PrinterBluetooth? _selectedPrinter;

  final ValueNotifier<List<PrinterBluetooth>> printersNotifier =
      ValueNotifier([]);
  final ValueNotifier<bool> isConnectedNotifier = ValueNotifier(false);
  final ValueNotifier<String?> connectionError = ValueNotifier(null);

  List<PrinterBluetooth> get printers => _printers;
  PrinterBluetooth? get selectedPrinter => _selectedPrinter;
  bool get isConnected => isConnectedNotifier.value;

  Future<void> initialize() async {
    _printerManager = PrinterBluetoothManager();
    _printerManager.scanResults.listen((results) {
      _printers = results;
      printersNotifier.value = results;
    });
  }

  Future<void> startScan({Duration timeout = const Duration(seconds: 5)}) async {
    _printerManager.startScan(Duration(milliseconds: timeout.inMilliseconds));
    await Future.delayed(timeout);
    _printerManager.stopScan();
  }

  Future<void> stopScan() async {
    await _printerManager.stopScan();
  }

  Future<bool> connectToPrinter(PrinterBluetooth printer) async {
    try {
      await _printerManager.connect(printer, timeout: Duration(seconds: 10));
      _selectedPrinter = printer;
      isConnectedNotifier.value = true;
      connectionError.value = null;
      return true;
    } catch (e) {
      connectionError.value = 'Connection failed: $e';
      isConnectedNotifier.value = false;
      return false;
    }
  }

  Future<void> disconnect() async {
    if (_selectedPrinter != null) {
      await _printerManager.disconnect();
      _selectedPrinter = null;
      isConnectedNotifier.value = false;
    }
  }

  Future<bool> printTestReceipt() async {
    if (_selectedPrinter == null) return false;

    try {
      final profile = await CapabilityProfile.load();
      final generator = Generator(PosPaperSize.mm80, profile);

      final bytes = <int>[];
      bytes += generator.text('GULA Platform',
          styles: PosStyles(align: PosAlign.center, bold: true, height: PosTextSize.size2));
      bytes += generator.text('=' * 32);
      bytes += generator.text('Printer Test');
      bytes += generator.text('Date: ${DateTime.now().toString()}');
      bytes += generator.text('=' * 32);
      bytes += generator.text('Thank you!');
      bytes += generator.cut();

      await _printerManager.send(bytes);
      return true;
    } catch (e) {
      connectionError.value = 'Print error: $e';
      return false;
    }
  }

  Future<bool> printLabel({
    required String barcode,
    required String patientName,
    required String sampleType,
    required String date,
  }) async {
    if (_selectedPrinter == null) return false;

    try {
      final profile = await CapabilityProfile.load();
      final generator = Generator(PosPaperSize.mm80, profile);

      final bytes = <int>[];
      bytes += generator.text(patientName, styles: PosStyles(bold: true));
      bytes += generator.text('Type: $sampleType');
      bytes += generator.text('Date: $date');
      bytes += generator.barcode(barcode, Barcode.code128());
      bytes += generator.text(barcode);
      bytes += generator.cut();

      await _printerManager.send(bytes);
      return true;
    } catch (e) {
      connectionError.value = 'Label print error: $e';
      return false;
    }
  }

  Future<bool> printReceipt(Map<String, dynamic> data) async {
    if (_selectedPrinter == null) return false;

    try {
      final profile = await CapabilityProfile.load();
      final generator = Generator(PosPaperSize.mm80, profile);

      final bytes = <int>[];
      bytes += generator.text('GULA Platform',
          styles: PosStyles(align: PosAlign.center, bold: true, height: PosTextSize.size2));
      bytes += generator.text('Receipt #${data['receipt_number'] ?? ''}',
          styles: PosStyles(align: PosAlign.center));
      bytes += generator.text('-' * 32);

      final items = data['items'] as List? ?? [];
      for (final item in items) {
        bytes += generator.text(
          '${item['name'] ?? ''}   ${item['quantity'] ?? ''} x ${item['price'] ?? ''}',
        );
      }

      bytes += generator.text('-' * 32);
      bytes += generator.text('Total: ${data['total'] ?? ''} IQD',
          styles: PosStyles(bold: true));
      bytes += generator.text('');
      bytes += generator.text('Thank you!',
          styles: PosStyles(align: PosAlign.center));
      bytes += generator.cut();

      await _printerManager.send(bytes);
      return true;
    } catch (e) {
      connectionError.value = 'Receipt print error: $e';
      return false;
    }
  }

  void dispose() {
    _printerManager.disconnect();
    printersNotifier.dispose();
    isConnectedNotifier.dispose();
    connectionError.dispose();
  }
}
