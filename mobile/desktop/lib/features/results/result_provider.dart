import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ResultProvider extends ChangeNotifier {
  List<Map<String, dynamic>> _results = [];
  bool _isLoading = false;
  int _page = 1;
  int _totalPages = 1;

  List<Map<String, dynamic>> get results => _results;
  bool get isLoading => _isLoading;
  int get page => _page;
  int get totalPages => _totalPages;

  Future<void> loadResults({int page = 1}) async {
    _isLoading = true;
    _page = page;
    notifyListeners();

    await Future.delayed(const Duration(milliseconds: 300));
    _results = List.generate(20, (i) => {
      'id': '${i + 1}',
      'testName': ['Hemoglobin', 'WBC', 'Glucose', 'Creatinine', 'ALT', 'AST', 'Cholesterol', 'Triglycerides'][i % 8],
      'result': ['14.2', '8.5', '95', '0.9', '25', '30', '180', '150'][i % 8],
      'unit': ['g/dL', 'K/uL', 'mg/dL', 'mg/dL', 'U/L', 'U/L', 'mg/dL', 'mg/dL'][i % 8],
      'referenceRange': ['13.5-17.5', '4.5-11.0', '70-100', '0.6-1.2', '10-40', '10-40', '<200', '<150'][i % 8],
      'flag': ['normal', 'normal', 'normal', 'normal', 'h', 'normal', 'h', 'normal'][i % 8],
      'patientName': ['Ahmed Ali', 'Sara Mohammed', 'Hussein Jassim'][i % 3],
      'status': ['pending', 'completed', 'verified'][i % 3],
      'createdAt': DateTime.now().subtract(Duration(hours: i * 2)).toIso8601String(),
    });
    _totalPages = 5;
    _isLoading = false;
    notifyListeners();
  }
}

final resultProvider = ChangeNotifierProvider<ResultProvider>((ref) {
  return ResultProvider();
});
