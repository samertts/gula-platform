import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SampleProvider extends ChangeNotifier {
  List<Map<String, dynamic>> _samples = [];
  bool _isLoading = false;
  int _page = 1;
  int _totalPages = 1;

  List<Map<String, dynamic>> get samples => _samples;
  bool get isLoading => _isLoading;
  int get page => _page;
  int get totalPages => _totalPages;

  Future<void> loadSamples({int page = 1}) async {
    _isLoading = true;
    _page = page;
    notifyListeners();

    await Future.delayed(const Duration(milliseconds: 300));
    _samples = List.generate(
      15,
      (i) => {
        'id': '${i + 1}',
        'barcode': 'BL20250321-${(100 + i).toString().padLeft(3, '0')}',
        'sampleType': ['Blood', 'Urine', 'Stool', 'Serum', 'Plasma'][i % 5],
        'status': [
          'collected',
          'received',
          'processing',
          'analyzed',
          'rejected',
        ][i % 5],
        'patientName': ['Ahmed Ali', 'Sara Mohammed', 'Hussein Jassim'][i % 3],
        'collectedAt': DateTime.now()
            .subtract(Duration(hours: i * 2))
            .toIso8601String(),
      },
    );
    _totalPages = 5;
    _isLoading = false;
    notifyListeners();
  }
}

final sampleProvider = ChangeNotifierProvider<SampleProvider>((ref) {
  return SampleProvider();
});
