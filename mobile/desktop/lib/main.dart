import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:window_manager/window_manager.dart';
import 'package:system_tray/system_tray.dart';
import 'package:package_info_plus/package_info_plus.dart';

import 'app.dart';
import 'app_router.dart';
import 'core/auth/auth_provider.dart';
import 'core/observability/crash_reporter.dart';
import 'core/offline/connectivity_service.dart';
import 'core/offline/database.dart';
import 'core/offline/sync_engine.dart';
import 'core/providers/app_providers.dart';
import 'core/security/tamper_detection.dart';
import 'core/update/auto_updater.dart';
import 'core/utils/constants.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await _initializeApp();

  runApp(
    ProviderScope(
      child: _AppEntry(),
    ),
  );
}

Future<void> _initializeApp() async {
  try {
    await windowManager.ensureInitialized();

    const windowOptions = WindowOptions(
      size: Size(AppConstants.defaultDesktopWidth, AppConstants.defaultDesktopHeight),
      minimumSize: Size(AppConstants.minDesktopWidth, AppConstants.minDesktopHeight),
      center: true,
      backgroundColor: Colors.transparent,
      skipTaskbar: false,
      title: AppConstants.appName,
      titleBarStyle: TitleBarStyle.normal,
    );

    await windowManager.waitUntilReadyToShow(windowOptions, () async {
      await windowManager.show();
      await windowManager.focus();
      await windowManager.setPreventClose(true);
      await windowManager.setMinimumSize(
        const Size(AppConstants.minDesktopWidth, AppConstants.minDesktopHeight),
      );
    });

    SystemChrome.setPreferredOrientations([
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);

    SystemChrome.setSystemUIOverlayStyle(
      const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.dark,
      ),
    );

    await CrashReporter.initialize();
    await TamperDetection.initialize();
  } catch (e) {
    debugPrint('App initialization error: $e');
  }
}

class _AppEntry extends ConsumerStatefulWidget {
  @override
  ConsumerState<_AppEntry> createState() => _AppEntryState();
}

class _AppEntryState extends ConsumerState<_AppEntry> {
  final SystemTray _systemTray = SystemTray();
  final AutoUpdater _autoUpdater = AutoUpdater();
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _initApp();
  }

  Future<void> _initApp() async {
    const apiUrl = 'https://api.gula-platform.com/api/v1';

    final authProvider = ref.read(authProviderProvider);
    await authProvider.initialize(apiUrl: apiUrl);

    if (authProvider.isAuthenticated) {
      try {
        CrashReporter.setUser(
          id: authProvider.userId,
          email: authProvider.userEmail,
          username: authProvider.userName,
        );
        CrashReporter.setTag('lab_id', authProvider.labId ?? '');
        CrashReporter.setTag('role', authProvider.userRole ?? '');
      } catch (_) {}
    }

    try {
      final connectivity = ref.read(connectivityServiceProvider);
      await connectivity.initialize();

      final syncEngine = ref.read(syncEngineProvider);
      if (authProvider.isAuthenticated) {
        syncEngine.startPeriodicSync();
      }
    } catch (_) {}

    try {
      await _autoUpdater.initialize();
    } catch (_) {}

    try {
      _initSystemTray();
    } catch (_) {}

    setState(() => _initialized = true);
  }

  Future<void> _initSystemTray() async {
    await _systemTray.initSystemTray(
      iconPath: 'assets/icons/app_icon.png',
      toolTip: AppConstants.appName,
    );

    await _systemTray.setContextMenu(
      Menu(
        items: [
          MenuItem(label: 'Show', onClicked: (_) => windowManager.show()),
          MenuItem(label: 'Hide', onClicked: (_) => windowManager.hide()),
          Menu.separator(),
          MenuItem(label: 'Quit', onClicked: (_) => _quitApp()),
        ],
      ),
    );

    _systemTray.onSystemTrayClicked = (_) {
      windowManager.show();
      windowManager.focus();
    };
  }

  Future<void> _quitApp() async {
    try {
      ref.read(syncEngineProvider).dispose();
      ref.read(databaseProvider).close();
    } catch (_) {}
    await windowManager.destroy();
  }

  @override
  void dispose() {
    _autoUpdater.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = ref.watch(authProviderProvider);
    final authState = authProvider.isAuthenticated;

    final appRouter = AppRouter(authProvider: authProvider);

    return GulaApp(appRouter: appRouter);
  }
}
