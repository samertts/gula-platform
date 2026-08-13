import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../lib/widgets/charts/kpi_card.dart';

void main() {
  testWidgets('KpiCard displays its label and value', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
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
}
