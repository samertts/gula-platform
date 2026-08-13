import 'package:flutter/material.dart';

import '../core/gula_sidebar.dart';
import '../core/gula_app_bar.dart';
import '../core/gula_offline_banner.dart';
import '../core/gula_sync_indicator.dart';
import '../../core/providers/app_providers.dart';

import 'package:flutter_riverpod/flutter_riverpod.dart';

class DesktopScaffold extends ConsumerStatefulWidget {
  final Widget child;

  const DesktopScaffold({super.key, required this.child});

  @override
  ConsumerState<DesktopScaffold> createState() => _DesktopScaffoldState();
}

class _DesktopScaffoldState extends ConsumerState<DesktopScaffold> {
  bool _sidebarCollapsed = false;

  @override
  Widget build(BuildContext context) {
    final syncProvider = ref.watch(syncProviderProvider);
    final authProvider = ref.watch(authProviderProvider);
    final isOffline = !syncProvider.isOnline;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            GulaOfflineBanner(isOffline: isOffline),
            Expanded(
              child: Row(
                children: [
                  GulaSidebar(
                    isCollapsed: _sidebarCollapsed,
                    onToggle: () =>
                        setState(() => _sidebarCollapsed = !_sidebarCollapsed),
                    userRole: authProvider.userRole ?? '',
                    userName: authProvider.userName ?? '',
                    userEmail: authProvider.userEmail ?? '',
                  ),
                  Expanded(
                    child: Column(
                      children: [
                        GulaAppBar(
                          onMenuTap: () => setState(
                            () => _sidebarCollapsed = !_sidebarCollapsed,
                          ),
                          syncIndicator: GulaSyncIndicator(
                            status: syncProvider.status,
                            progress: syncProvider.progress,
                            lastSync: syncProvider.lastSyncTime,
                            onSync: () => syncProvider.sync(),
                          ),
                          userName: authProvider.userName,
                          onLogout: () => authProvider.logout(),
                        ),
                        Expanded(child: widget.child),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
