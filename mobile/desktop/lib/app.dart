import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app_router.dart';
import 'core/providers/app_providers.dart';
import 'core/theme/app_theme.dart';
import 'core/update/auto_updater.dart';
import 'l10n/l10n.dart';

class GulaApp extends ConsumerWidget {
  final AppRouter appRouter;
  final UpdatePolicy? updatePolicy;
  final Future<bool> Function()? onUpdate;

  const GulaApp({
    super.key,
    required this.appRouter,
    this.updatePolicy,
    this.onUpdate,
  });

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
        final content = Directionality(
          textDirection: isRtl ? TextDirection.rtl : TextDirection.ltr,
          child: child ?? const SizedBox.shrink(),
        );
        final policy = updatePolicy;
        if (policy?.forceUpdate == true) {
          return _UpdateRequiredOverlay(policy: policy!, onUpdate: onUpdate);
        }
        if (policy?.updateAvailable == true) {
          return Stack(
            children: [
              content,
              _OptionalUpdateBanner(policy: policy!, onUpdate: onUpdate),
            ],
          );
        }
        return content;
      },
    );
  }
}

class _UpdateRequiredOverlay extends StatelessWidget {
  final UpdatePolicy policy;
  final Future<bool> Function()? onUpdate;

  const _UpdateRequiredOverlay({required this.policy, required this.onUpdate});

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: ColoredBox(
        color: Colors.white,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'يلزم تحديث التطبيق للمتابعة',
                    style: Theme.of(context).textTheme.headlineSmall,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  Text(policy.messageAr, textAlign: TextAlign.center),
                  const SizedBox(height: 24),
                  FilledButton(
                    onPressed: onUpdate == null ? null : () => onUpdate!(),
                    child: const Text('تحديث الآن'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _OptionalUpdateBanner extends StatelessWidget {
  final UpdatePolicy policy;
  final Future<bool> Function()? onUpdate;

  const _OptionalUpdateBanner({required this.policy, required this.onUpdate});

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: 24,
      right: 24,
      bottom: 20,
      child: Material(
        elevation: 8,
        borderRadius: BorderRadius.circular(16),
        color: Colors.teal.shade900,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          child: Row(
            children: [
              const Expanded(
                child: Text(
                  'يتوفر إصدار أحدث من GULA.',
                  style: TextStyle(color: Colors.white),
                ),
              ),
              TextButton(
                onPressed: onUpdate == null ? null : () => onUpdate!(),
                child: const Text('تحديث الآن'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
