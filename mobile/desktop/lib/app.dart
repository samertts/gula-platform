import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app_router.dart';
import 'core/providers/app_providers.dart';
import 'core/theme/app_theme.dart';
import 'l10n/l10n.dart';

class GulaApp extends ConsumerWidget {
  final AppRouter appRouter;

  const GulaApp({super.key, required this.appRouter});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeState = ref.watch(themeProvider);
    final locale = themeState.locale;
    final isRtl = themeState.isRtl;

    return MaterialApp.router(
      title: 'GULA Platform',
      debugShowCheckedModeBanner: false,
      locale: locale,
      supportedLocales: AppLocalization.supportedLocales,
      localizationsDelegates: [
        AppLocalization.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      localeResolutionCallback: (locale, supportedLocales) {
        for (final supported in supportedLocales) {
          if (supported.languageCode == locale?.languageCode) {
            return supported;
          }
        }
        return AppLocalization.fallbackLocale;
      },
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: themeState.themeMode,
      routerConfig: appRouter.router,
      builder: (context, child) {
        return Directionality(
          textDirection: isRtl ? TextDirection.rtl : TextDirection.ltr,
          child: child ?? const SizedBox.shrink(),
        );
      },
    );
  }
}
