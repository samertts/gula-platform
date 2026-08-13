import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AdminProvider extends ChangeNotifier {
  List<Map<String, dynamic>> _users = [];
  List<Map<String, dynamic>> _auditLogs = [];
  bool _isLoadingUsers = false;
  bool _isLoadingAudit = false;

  List<Map<String, dynamic>> get users => _users;
  List<Map<String, dynamic>> get auditLogs => _auditLogs;
  bool get isLoadingUsers => _isLoadingUsers;
  bool get isLoadingAudit => _isLoadingAudit;

  Future<void> loadUsers() async {
    _isLoadingUsers = true;
    notifyListeners();
    await Future.delayed(const Duration(milliseconds: 300));
    _users = List.generate(
      10,
      (i) => {
        'id': '${i + 1}',
        'name': [
          'Dr. Ali Hasan',
          'Fatima Ahmed',
          'Ahmed Khalid',
          'Layla Jassim',
          'Omar Hussein',
        ][i % 5],
        'email': [
          'ali@lab.com',
          'fatima@lab.com',
          'ahmed@lab.com',
          'layla@lab.com',
          'omar@lab.com',
        ][i % 5],
        'role': [
          'labAdmin',
          'labStaff',
          'labStaff',
          'doctor',
          'labAdmin',
        ][i % 5],
        'status': ['active', 'active', 'active', 'inactive', 'active'][i % 5],
        'lastLogin': DateTime.now()
            .subtract(Duration(days: i * 3))
            .toIso8601String(),
      },
    );
    _isLoadingUsers = false;
    notifyListeners();
  }

  Future<void> loadAuditLogs() async {
    _isLoadingAudit = true;
    notifyListeners();
    await Future.delayed(const Duration(milliseconds: 300));
    _auditLogs = List.generate(
      20,
      (i) => {
        'id': '${i + 1}',
        'action': ['CREATE', 'UPDATE', 'DELETE', 'VIEW', 'LOGIN'][i % 5],
        'entity': ['Patient', 'Order', 'Result', 'Sample', 'User'][i % 5],
        'entityId': '${1000 + i}',
        'user': ['admin', 'tech.ali', 'nurse.fatima'][i % 3],
        'timestamp': DateTime.now()
            .subtract(Duration(hours: i * 2))
            .toIso8601String(),
        'details':
            'Performed ${['create', 'update', 'delete', 'view', 'login'][i % 5]} on ${['patient', 'order', 'result', 'sample', 'user'][i % 5]} ${1000 + i}',
      },
    );
    _isLoadingAudit = false;
    notifyListeners();
  }
}

final adminProvider = ChangeNotifierProvider<AdminProvider>((ref) {
  return AdminProvider();
});
