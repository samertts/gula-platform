import 'package:flutter_test/flutter_test.dart';

import '../../lib/features/patients/patient_provider.dart';

void main() {
  group('PatientProvider', () {
    test('starts with an empty non-loading state', () {
      final provider = PatientProvider();

      expect(provider.patients, isEmpty);
      expect(provider.isLoading, isFalse);
      expect(provider.hasError, isFalse);
    });

    test('loads the deterministic patient page', () async {
      final provider = PatientProvider();

      await provider.loadPatients(page: 2, search: 'Ahmed');

      expect(provider.isLoading, isFalse);
      expect(provider.page, 2);
      expect(provider.searchQuery, 'Ahmed');
      expect(provider.patients, hasLength(20));
      expect(provider.totalItems, 200);
      expect(provider.totalPages, 10);
    });

    test('deletes a patient from the loaded page', () async {
      final provider = PatientProvider();
      await provider.loadPatients();

      final id = provider.patients.first['id'] as String;
      await provider.deletePatient(id);

      expect(provider.patients.any((patient) => patient['id'] == id), isFalse);
      expect(provider.patients, hasLength(19));
    });
  });
}
