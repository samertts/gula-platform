import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class OrderProvider extends ChangeNotifier {
  List<Map<String, dynamic>> _orders = [];
  bool _isLoading = false;
  bool _hasError = false;
  String? _error;
  int _page = 1;
  int _totalPages = 1;

  List<Map<String, dynamic>> get orders => _orders;
  bool get isLoading => _isLoading;
  bool get hasError => _hasError;
  String? get error => _error;
  int get page => _page;
  int get totalPages => _totalPages;

  Future<void> loadOrders({int page = 1}) async {
    _isLoading = true;
    _hasError = false;
    _page = page;
    notifyListeners();

    try {
      await Future.delayed(const Duration(milliseconds: 300));
      _orders = List.generate(15, (i) => {
        'id': '${i + 1}',
        'orderNumber': 'ORD-2025-${(8900 + i)}',
        'patientName': ['Ahmed Ali', 'Sara Mohammed', 'Hussein Jassim', 'Noor Hasan', 'Zainab Khalid'][i % 5],
        'status': ['pending', 'completed', 'validated', 'cancelled'][i % 4],
        'testTypes': ['CBC, LFT, Lipid Profile', 'Thyroid Panel', 'Blood Glucose', 'Renal Function'][i % 4],
        'doctorName': 'Dr. ${['Ali', 'Hasan', 'Ammar', 'Layla'][i % 4]}',
        'createdAt': DateTime.now().subtract(Duration(hours: i * 3)).toIso8601String(),
      });
      _totalPages = 5;
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _isLoading = false;
      _hasError = true;
      _error = e.toString();
      notifyListeners();
    }
  }
}

final orderProvider = ChangeNotifierProvider<OrderProvider>((ref) {
  return OrderProvider();
});
