import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class NotificationProvider extends ChangeNotifier {
  List<Map<String, dynamic>> _notifications = [];
  int _unreadCount = 0;
  bool _isLoading = false;

  List<Map<String, dynamic>> get notifications => _notifications;
  int get unreadCount => _unreadCount;
  bool get isLoading => _isLoading;

  Future<void> loadNotifications() async {
    _isLoading = true;
    notifyListeners();
    await Future.delayed(const Duration(milliseconds: 300));
    _notifications = List.generate(
      20,
      (i) => {
        'id': '${i + 1}',
        'title': [
          'Critical Result',
          'Order Completed',
          'Sample Received',
          'System Update',
          'New Patient Registered',
        ][i % 5],
        'body': [
          'Hemoglobin result is critical for patient Ahmed Ali',
          'Order ORD-2025-${8900 + i} has been completed',
          'Sample BL20250321-${100 + i} has been received',
          'System maintenance scheduled tonight',
          'New patient registered: ${['Sara Mohammed', 'Ali Hameed', 'Noor Hasan'][i % 3]}',
        ][i % 5],
        'type': ['critical', 'result', 'order', 'system', 'patient'][i % 5],
        'severity': ['critical', 'info', 'info', 'warning', 'info'][i % 5],
        'isRead': i > 5 ? 1 : 0,
        'createdAt': DateTime.now()
            .subtract(Duration(minutes: i * 15))
            .toIso8601String(),
      },
    );
    _unreadCount = _notifications.where((n) => n['isRead'] == 0).length;
    _isLoading = false;
    notifyListeners();
  }

  Future<void> markAsRead(String id) async {
    final idx = _notifications.indexWhere((n) => n['id'] == id);
    if (idx != -1) {
      _notifications[idx]['isRead'] = 1;
      _unreadCount = _notifications.where((n) => n['isRead'] == 0).length;
      notifyListeners();
    }
  }

  Future<void> markAllAsRead() async {
    for (final n in _notifications) {
      n['isRead'] = 1;
    }
    _unreadCount = 0;
    notifyListeners();
  }
}

final notificationListProvider = ChangeNotifierProvider<NotificationProvider>((
  ref,
) {
  return NotificationProvider();
});
