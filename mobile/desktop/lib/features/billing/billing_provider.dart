import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class BillingProvider extends ChangeNotifier {
  List<Map<String, dynamic>> _invoices = [];
  bool _isLoading = false;

  List<Map<String, dynamic>> get invoices => _invoices;
  bool get isLoading => _isLoading;

  Future<void> loadInvoices() async {
    _isLoading = true;
    notifyListeners();
    await Future.delayed(const Duration(milliseconds: 300));
    _invoices = List.generate(10, (i) => {
      'id': '${i + 1}',
      'invoiceNumber': 'INV-2025-${(1000 + i)}',
      'patientName': ['Ahmed Ali', 'Sara Mohammed', 'Hussein Jassim'][i % 3],
      'amount': (50.0 + i * 25.0).toStringAsFixed(2),
      'status': ['paid', 'pending', 'overdue', 'cancelled'][i % 4],
      'date': DateTime.now().subtract(Duration(days: i * 2)).toIso8601String(),
    });
    _isLoading = false;
    notifyListeners();
  }
}

final billingProvider = ChangeNotifierProvider<BillingProvider>((ref) {
  return BillingProvider();
});
