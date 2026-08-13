import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../core/providers/app_providers.dart';
import '../../core/theme/theme_provider.dart';
import '../../core/utils/constants.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/layout/page_container.dart';
import '../../widgets/layout/section_header.dart';
import 'settings_provider.dart';

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
                    const Text('Appearance', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    const Divider(height: 24),
                    ListTile(
                      title: const Text('Theme'),
                      subtitle: Text(themeState.mode == AppThemeMode.light ? 'Light' : themeState.mode == AppThemeMode.dark ? 'Dark' : 'High Contrast'),
                      trailing: SegmentedButton<AppThemeMode>(
                        segments: const [
                          ButtonSegment(value: AppThemeMode.light, label: Text('Light'), icon: Icon(Icons.light_mode, size: 18)),
                          ButtonSegment(value: AppThemeMode.dark, label: Text('Dark'), icon: Icon(Icons.dark_mode, size: 18)),
                          ButtonSegment(value: AppThemeMode.highContrast, label: Text('HC'), icon: Icon(Icons.contrast, size: 18)),
                        ],
                        selected: {themeState.mode},
                        onSelectionChanged: (v) => themeState.setThemeMode(v.first),
                      ),
                    ),
                    const Divider(),
                    ListTile(
                      title: const Text('Language'),
                      subtitle: Text(themeState.locale.languageCode == 'ar' ? 'العربية' : 'English'),
                      trailing: SegmentedButton<Locale>(
                        segments: const [
                          ButtonSegment(value: Locale('ar'), label: Text('العربية')),
                          ButtonSegment(value: Locale('en'), label: Text('English')),
                        ],
                        selected: {themeState.locale},
                        onSelectionChanged: (v) => themeState.setLocale(v.first),
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
                    const Text('Notifications', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    const Divider(height: 24),
                    SwitchListTile(
                      title: const Text('Push Notifications'),
                      subtitle: const Text('Receive notifications for critical results and updates'),
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
                    const Text('Synchronization', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    const Divider(height: 24),
                    SwitchListTile(
                      title: const Text('Auto Sync'),
                      subtitle: const Text('Synchronize data with server'),
                      value: settingsState.autoSync,
                      onChanged: (v) => settingsState.setAutoSync(v),
                    ),
                    ListTile(
                      title: const Text('Sync Interval'),
                      subtitle: Text('Every ${settingsState.syncInterval} seconds'),
                      trailing: SizedBox(
                        width: 120,
                        child: DropdownButtonFormField<int>(
                          value: settingsState.syncInterval,
                          items: [15, 30, 60, 120].map((v) => DropdownMenuItem(value: v, child: Text('$v sec'))).toList(),
                          onChanged: (v) { if (v != null) settingsState.setSyncInterval(v); },
                          decoration: const InputDecoration(border: OutlineInputBorder(), contentPadding: EdgeInsets.symmetric(horizontal: 8)),
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
                    const Text('Printing', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    const Divider(height: 24),
                    SwitchListTile(
                      title: const Text('Auto-Print Labels'),
                      subtitle: const Text('Automatically print labels when collecting samples'),
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
              if (authProvider.userRole == 'labAdmin' || authProvider.userRole == 'masterAdmin')
                GulaCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Administration', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
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
                    const Text('About', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    const Divider(height: 24),
                    const ListTile(
                      title: Text('Version'),
                      subtitle: Text('${AppConstants.appVersion} (${AppConstants.appBuildNumber})'),
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
                          const SnackBar(content: Text('App is up to date'), backgroundColor: AppColors.success500),
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
