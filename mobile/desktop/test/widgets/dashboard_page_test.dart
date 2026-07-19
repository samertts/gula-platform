import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../lib/widgets/charts/kpi_card.dart';
import '../../lib/features/dashboard/dashboard_provider.dart';

class MockDashboardProvider extends ChangeNotifier implements DashboardProvider {
  @override
  DashboardState get state => _state;
  DashboardState _state = DashboardState(
    isLoading: false,
    totalPatients: 1542,
    totalOrdersToday: 89,
    pendingOrders: 23,
    criticalResults: 2,
    ordersByStatus: {},
    weeklyTrend: [],
    recentActivity: [],
  );

  @override
  Future<void> loadDashboard() async {}

  set state(DashboardState value) {
    _state = value;
    notifyListeners();
  }
}

void main() {
  testWidgets('KpiCard displays number and label', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: KpiCard(
            title: 'Total Patients',
            value: '1,542',
            icon: Icons.people,
            color: Colors.blue,
          ),
        ),
      ),
    );

    expect(find.text('1,542'), findsOneWidget);
    expect(find.text('Total Patients'), findsOneWidget);
  });

  testWidgets('KpiCard shows trend indicator', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: KpiCard(
            title: 'Growth',
            value: '+12.5%',
            icon: Icons.trending_up,
            color: Colors.green,
          ),
        ),
      ),
    );

    expect(find.text('+12.5%'), findsOneWidget);
  });
}
