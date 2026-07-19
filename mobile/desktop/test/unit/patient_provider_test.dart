import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import '../../lib/features/patients/patient_provider.dart';
import '../../lib/core/offline/database.dart';

import 'patient_provider_test.mocks.dart';

@GenerateMocks([PatientDao])
void main() {
  late MockPatientDao mockPatientDao;
  late PatientProvider patientProvider;

  setUp(() {
    mockPatientDao = MockPatientDao();
    patientProvider = PatientProvider(patientDao: mockPatientDao);
  });

  group('PatientProvider', () {
    test('initial state is empty list', () {
      expect(patientProvider.patients, isEmpty);
      expect(patientProvider.isLoading, false);
    });

    test('loadPatients populates list', () async {
      final patients = List.generate(3, (i) => Patient(
        id: i,
        fullName: 'Patient $i',
        phone: '0770123456$i',
      ));
      when(mockPatientDao.getAll()).thenAnswer((_) async => patients);

      await patientProvider.loadPatients();
      expect(patientProvider.patients.length, 3);
    });

    test('search filters patients', () async {
      final patients = List.generate(3, (i) => Patient(
        id: i,
        fullName: 'Patient $i',
        phone: '0770123456$i',
      ));
      when(mockPatientDao.searchByName(any)).thenAnswer((_) async => [patients[0]]);

      await patientProvider.searchPatients('Patient 0');
      expect(patientProvider.patients.length, 1);
    });
  });
}
