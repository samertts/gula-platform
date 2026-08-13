import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';


class DashboardState {
  final bool isLoading;
  final bool hasError;
  final String? error;
  final int totalPatients;
  final int totalOrders;
  final int totalSamples;
  final int criticalResults;
  final int pendingResults;
  final int todayOrders;
  final int todaySamples;
  final List<RecentActivity> recentActivities;
  final List<Map<String, dynamic>> ordersByDay;
  final List<Map<String, dynamic>> resultsByStatus;

  DashboardState({
    this.isLoading = false,
    this.hasError = false,
    this.error,
    this.totalPatients = 0,
    this.totalOrders = 0,
    this.totalSamples = 0,
    this.criticalResults = 0,
    this.pendingResults = 0,
    this.todayOrders = 0,
    this.todaySamples = 0,
    this.recentActivities = const [],
    this.ordersByDay = const [],
    this.resultsByStatus = const [],
  });

  DashboardState copyWith({
    bool? isLoading,
    bool? hasError,
    String? error,
    int? totalPatients,
    int? totalOrders,
    int? totalSamples,
    int? criticalResults,
    int? pendingResults,
    int? todayOrders,
    int? todaySamples,
    List<RecentActivity>? recentActivities,
    List<Map<String, dynamic>>? ordersByDay,
    List<Map<String, dynamic>>? resultsByStatus,
  }) {
    return DashboardState(
      isLoading: isLoading ?? this.isLoading,
      hasError: hasError ?? this.hasError,
      error: error ?? this.error,
      totalPatients: totalPatients ?? this.totalPatients,
      totalOrders: totalOrders ?? this.totalOrders,
      totalSamples: totalSamples ?? this.totalSamples,
      criticalResults: criticalResults ?? this.criticalResults,
      pendingResults: pendingResults ?? this.pendingResults,
      todayOrders: todayOrders ?? this.todayOrders,
      todaySamples: todaySamples ?? this.todaySamples,
      recentActivities: recentActivities ?? this.recentActivities,
      ordersByDay: ordersByDay ?? this.ordersByDay,
      resultsByStatus: resultsByStatus ?? this.resultsByStatus,
    );
  }
}

class RecentActivity {
  final String id;
  final String type;
  final String title;
  final String? subtitle;
  final DateTime timestamp;

  RecentActivity({
    required this.id,
    required this.type,
    required this.title,
    this.subtitle,
    required this.timestamp,
  });
}

class DashboardProvider extends ChangeNotifier {
  DashboardState _state = DashboardState();

  DashboardState get state => _state;

  Future<void> loadDashboard() async {
    _state = _state.copyWith(isLoading: true, hasError: false);
    notifyListeners();

    try {
      await Future.delayed(const Duration(milliseconds: 500));

      _state = _state.copyWith(
        isLoading: false,
        totalPatients: 1250,
        totalOrders: 890,
        totalSamples: 2100,
        criticalResults: 3,
        pendingResults: 15,
        todayOrders: 28,
        todaySamples: 35,
        recentActivities: [
          RecentActivity(id: '1', type: 'result', title: 'Critical result: Hemoglobin', subtitle: 'Patient: Ali Ahmed', timestamp: DateTime.now().subtract(const Duration(minutes: 5))),
          RecentActivity(id: '2', type: 'order', title: 'New order created', subtitle: 'Order #ORD-2025-0891', timestamp: DateTime.now().subtract(const Duration(minutes: 15))),
          RecentActivity(id: '3', type: 'sample', title: 'Sample collected', subtitle: 'Barcode: BL20250321-001', timestamp: DateTime.now().subtract(const Duration(minutes: 30))),
          RecentActivity(id: '4', type: 'patient', title: 'New patient registered', subtitle: 'Sarah Mohammed', timestamp: DateTime.now().subtract(const Duration(hours: 1))),
          RecentActivity(id: '5', type: 'result', title: 'Results validated', subtitle: 'Order #ORD-2025-0885', timestamp: DateTime.now().subtract(const Duration(hours: 2))),
        ],
        ordersByDay: [
          {'day': 'Mon', 'orders': 12},
          {'day': 'Tue', 'orders': 18},
          {'day': 'Wed', 'orders': 15},
          {'day': 'Thu', 'orders': 22},
          {'day': 'Fri', 'orders': 8},
          {'day': 'Sat', 'orders': 14},
          {'day': 'Sun', 'orders': 20},
        ],
        resultsByStatus: [
          {'status': 'Completed', 'count': 45},
          {'status': 'Pending', 'count': 15},
          {'status': 'Validated', 'count': 30},
          {'status': 'Critical', 'count': 3},
        ],
      );
    } catch (e) {
      _state = _state.copyWith(
        isLoading: false,
        hasError: true,
        error: e.toString(),
      );
      notifyListeners();
    }
  }

  @override
  void dispose() {
    super.dispose();
  }
}

final dashboardProvider = ChangeNotifierProvider<DashboardProvider>((ref) {
  return DashboardProvider();
});
