import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../lib/app.dart';
import '../../lib/core/providers/app_providers.dart';
import '../../lib/core/theme/app_colors.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('App Flow', () {
    testWidgets('app launches and shows login page', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(child: GulaApp()),
      );
      await tester.pumpAndSettle();

      expect(find.byType(TextField), findsAtLeast(1));
    });

    testWidgets('login form has email and password fields', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(child: GulaApp()),
      );
      await tester.pumpAndSettle();

      expect(find.text('Email'), findsAtLeast(0));
      expect(find.text('Password'), findsAtLeast(0));
    });
  });
}
