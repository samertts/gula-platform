import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers/app_providers.dart';

class PatientProvider extends ChangeNotifier {
  List<Map<String, dynamic>> _patients = [];
  bool _isLoading = false;
  bool _hasError = false;
  String? _error;
  int _page = 1;
  int _totalPages = 1;
  int _totalItems = 0;
  String _searchQuery = '';

  List<Map<String, dynamic>> get patients => _patients;
  bool get isLoading => _isLoading;
  bool get hasError => _hasError;
  String? get error => _error;
  int get page => _page;
  int get totalPages => _totalPages;
  int get totalItems => _totalItems;
  String get searchQuery => _searchQuery;

  Future<void> loadPatients({int page = 1, String? search}) async {
    _isLoading = true;
    _hasError = false;
    _page = page;
    if (search != null) _searchQuery = search;
    notifyListeners();

    try {
      await Future.delayed(const Duration(milliseconds: 300));

      _patients = List.generate(20, (i) => {
        'id': '${i + 1}',
        'firstName': ['Ahmed', 'Ali', 'Sara', 'Mariam', 'Hussein', 'Zainab', 'Mohammed', 'Fatima', 'Omar', 'Noor'][i % 10],
        'fatherName': ['Jasim', 'Hassan', 'Khalid', 'Abbas', 'Hamza'][i % 5],
        'lastName': ['Al-Tamimi', 'Al-Jubouri', 'Al-Janabi', 'Al-Bayati', 'Al-Saadi'][i % 5],
        'gender': i % 2 == 0 ? 'm' : 'f',
        'dateOfBirth': '198${i % 9 + 1}-0${i % 9 + 1}-${(i % 28 + 1).toString().padLeft(2, '0')}',
        'nationalId': '${10000000000000 + i}',
        'phone': '0770${1000000 + i}',
        'bloodGroup': ['A+', 'B+', 'O+', 'AB+', 'A-'][i % 5],
      });
      _totalItems = 200;
      _totalPages = 10;
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _isLoading = false;
      _hasError = true;
      _error = e.toString();
      notifyListeners();
    }
  }

  Future<void> deletePatient(String id) async {
    _patients.removeWhere((p) => p['id'] == id);
    notifyListeners();
  }

  Future<void> search(String query) async {
    _searchQuery = query;
    await loadPatients(search: query);
  }

  @override
  void dispose() {
    super.dispose();
  }
}

final patientProvider = ChangeNotifierProvider<PatientProvider>((ref) {
  return PatientProvider();
});
