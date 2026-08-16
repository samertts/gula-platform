import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('GULA Flutter shell can render', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: Scaffold(body: Text('GULA Platform'))),
    );

    expect(find.text('GULA Platform'), findsOneWidget);
  });
}
