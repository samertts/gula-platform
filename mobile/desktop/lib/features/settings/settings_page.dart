import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/providers/app_providers.dart';
import '../../core/theme/theme_provider.dart';
import '../../core/utils/constants.dart';
import '../../l10n/l10n.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/layout/page_container.dart';
import '../../widgets/layout/section_header.dart';
import 'settings_provider.dart';

String _languageLabel(Locale locale) => switch (locale.languageCode) {
  'ar' => 'العربية',
  'en' => 'English',
  'ku' => 'کوردی',
  'tk' => 'Türkmençe',
  'syr' => 'ܣܘܪܝܝܐ',
  'fa' => 'فارسی',
  _ => locale.languageCode,
};

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeState = ref.watch(themeProvider);
    final settingsState = ref.watch(settingsProvider);
    final authProvider = ref.watch(authProviderProvider);

    return PageContainer(
      child: SingleChildScrollView(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 800),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(title: 'Settings'),
              const SizedBox(height: 16),

              // Theme
              GulaCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Appearance',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const Divider(height: 24),
                    ListTile(
                      title: const Text('Theme'),
                      subtitle: Text(
                        themeState.mode == AppThemeMode.light
                            ? 'Light'
                            : themeState.mode == AppThemeMode.dark
                            ? 'Dark'
                            : 'High Contrast',
                      ),
                      trailing: SegmentedButton<AppThemeMode>(
                        segments: const [
                          ButtonSegment(
                            value: AppThemeMode.light,
                            label: Text('Light'),
                            icon: Icon(Icons.light_mode, size: 18),
                          ),
                          ButtonSegment(
                            value: AppThemeMode.dark,
                            label: Text('Dark'),
                            icon: Icon(Icons.dark_mode, size: 18),
                          ),
                          ButtonSegment(
                            value: AppThemeMode.highContrast,
                            label: Text('HC'),
                            icon: Icon(Icons.contrast, size: 18),
                          ),
                        ],
                        selected: {themeState.mode},
                        onSelectionChanged: (v) =>
                            themeState.setThemeMode(v.first),
                      ),
                    ),
                    const Divider(),
                    ListTile(
                      title: const Text('Language'),
                      subtitle: Text(_languageLabel(themeState.locale)),
                      trailing: DropdownButton<Locale>(
                        value: AppLocalization.supportedLocales.firstWhere(
                          (locale) => locale.languageCode == themeState.locale.languageCode,
                          orElse: () => AppLocalization.fallbackLocale,
                        ),
                        items: const [
                          DropdownMenuItem(value: Locale('ar', 'IQ'), child: Text('العربية')),
                          DropdownMenuItem(value: Locale('en', 'US'), child: Text('English')),
                          DropdownMenuItem(value: Locale('ku'), child: Text('کوردی')),
                          DropdownMenuItem(value: Locale('tk'), child: Text('Türkmençe')),
                          DropdownMenuItem(value: Locale('syr'), child: Text('ܣܘܪܝܝܐ')),
                          DropdownMenuItem(value: Locale('fa'), child: Text('فارسی')),
                        ],
                        onChanged: (value) { if (value != null) themeState.setLocale(value); },
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Accessibility
              GulaCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Accessibility',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const Divider(height: 24),
                    ListTile(
                      title: const Text('Text scale'),
                      subtitle: Text(
                        '${settingsState.textScale.toStringAsFixed(2)}×',
                      ),
                      trailing: SizedBox(
                        width: 180,
                        child: Slider(
                          value: settingsState.textScale,
                          min: 0.85,
                          max: 2.0,
                          divisions: 23,
                          onChanged: settingsState.setTextScale,
                        ),
                      ),
                    ),
                    SwitchListTile(
                      title: const Text('High contrast'),
                      subtitle: const Text(
                        'Keep status meaning visible beyond color alone',
                      ),
                      value: settingsState.highContrast,
                      onChanged: settingsState.setHighContrast,
                    ),
                    SwitchListTile(
                      title: const Text('Reduced motion and flashing'),
                      subtitle: const Text('Disable non-essential motion'),
                      value: settingsState.reducedMotion,
                      onChanged: settingsState.setReducedMotion,
                    ),
                    SwitchListTile(
                      title: const Text('Screen reader optimized'),
                      subtitle: const Text(
                        'Prefer semantic labels and predictable focus',
                      ),
                      value: settingsState.screenReaderOptimized,
                      onChanged: settingsState.setScreenReaderOptimized,
                    ),
                    SwitchListTile(
                      title: const Text('Larger touch targets'),
                      value: settingsState.largerTouchTargets,
                      onChanged: settingsState.setLargerTouchTargets,
                    ),
                    SwitchListTile(
                      title: const Text('Static alternatives'),
                      subtitle: const Text(
                        'Prefer static alternatives to moving content',
                      ),
                      value: settingsState.staticAlternatives,
                      onChanged: settingsState.setStaticAlternatives,
                    ),
                    ListTile(
                      title: const Text('Color blind safe palette'),
                      trailing: DropdownButton<String>(
                        value: settingsState.colorBlindMode,
                        items: const [
                          DropdownMenuItem(value: 'none', child: Text('None')),
                          DropdownMenuItem(
                            value: 'protanopia',
                            child: Text('Protanopia'),
                          ),
                          DropdownMenuItem(
                            value: 'deuteranopia',
                            child: Text('Deuteranopia'),
                          ),
                          DropdownMenuItem(
                            value: 'tritanopia',
                            child: Text('Tritanopia'),
                          ),
                          DropdownMenuItem(
                            value: 'monochrome',
                            child: Text('Monochrome'),
                          ),
                        ],
                        onChanged: (v) {
                          if (v != null) settingsState.setColorBlindMode(v);
                        },
                      ),
                    ),
                    const Padding(
                      padding: EdgeInsets.only(top: 8),
                      child: Text(
                        'Health Preferences are optional, consent-bound, and are not stored in this device local settings.',
                        style: TextStyle(fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Notifications
              GulaCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Notifications',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const Divider(height: 24),
                    SwitchListTile(
                      title: const Text('Push Notifications'),
                      subtitle: const Text(
                        'Receive notifications for critical results and updates',
                      ),
                      value: settingsState.enableNotifications,
                      onChanged: (v) => settingsState.setNotifications(v),
                    ),
                    SwitchListTile(
                      title: const Text('Sound'),
                      subtitle: const Text('Play sound for notifications'),
                      value: settingsState.enableSound,
                      onChanged: (v) => settingsState.setSound(v),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Sync
              GulaCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Synchronization',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const Divider(height: 24),
                    SwitchListTile(
                      title: const Text('Auto Sync'),
                      subtitle: const Text('Synchronize data with server'),
                      value: settingsState.autoSync,
                      onChanged: (v) => settingsState.setAutoSync(v),
                    ),
                    ListTile(
                      title: const Text('Sync Interval'),
                      subtitle: Text(
                        'Every ${settingsState.syncInterval} seconds',
                      ),
                      trailing: SizedBox(
                        width: 120,
                        child: DropdownButtonFormField<int>(
                          value: settingsState.syncInterval,
                          items: [15, 30, 60, 120]
                              .map(
                                (v) => DropdownMenuItem(
                                  value: v,
                                  child: Text('$v sec'),
                                ),
                              )
                              .toList(),
                          onChanged: (v) {
                            if (v != null) settingsState.setSyncInterval(v);
                          },
                          decoration: const InputDecoration(
                            border: OutlineInputBorder(),
                            contentPadding: EdgeInsets.symmetric(horizontal: 8),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Printing
              GulaCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Printing',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const Divider(height: 24),
                    SwitchListTile(
                      title: const Text('Auto-Print Labels'),
                      subtitle: const Text(
                        'Automatically print labels when collecting samples',
                      ),
                      value: settingsState.autoPrintLabels,
                      onChanged: (v) => settingsState.setAutoPrintLabels(v),
                    ),
                    const ListTile(
                      title: Text('Default Printer'),
                      subtitle: Text('Not configured'),
                      trailing: Icon(Icons.chevron_right),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Admin
              if (authProvider.userRole == 'labAdmin' ||
                  authProvider.userRole == 'masterAdmin')
                GulaCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Administration',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const Divider(height: 24),
                      ListTile(
                        leading: const Icon(Icons.people_outlined),
                        title: const Text('User Management'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => context.push('/settings/users'),
                      ),
                      ListTile(
                        leading: const Icon(Icons.history),
                        title: const Text('Audit Log'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => context.push('/settings/audit'),
                      ),
                      ListTile(
                        leading: const Icon(Icons.settings_outlined),
                        title: const Text('System Configuration'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => context.push('/settings/system'),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 16),

              // About
              GulaCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'About',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const Divider(height: 24),
                    const ListTile(
                      title: Text('Version'),
                      subtitle: Text(
                        '${AppConstants.appVersion} (${AppConstants.appBuildNumber})',
                      ),
                    ),
                    const ListTile(
                      title: Text('GULA Platform'),
                      subtitle: Text('Medical Laboratory Information System'),
                    ),
                    ListTile(
                      title: const Text('Check for Updates'),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('App is up to date'),
                            backgroundColor: AppColors.success500,
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Logout
              Center(
                child: GulaButton(
                  label: 'Logout',
                  variant: GulaButtonVariant.danger,
                  icon: Icons.logout,
                  onPressed: () async {
                    await authProvider.logout();
                    if (context.mounted) context.go('/login');
                  },
                ),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}
