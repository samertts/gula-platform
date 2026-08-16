import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'core/auth/auth_provider.dart';
import 'core/auth/identity_state.dart';
import 'features/auth/login_page.dart';
import 'features/auth/mfa_page.dart';
import 'features/auth/forgot_password_page.dart';
import 'features/auth/account_request_page.dart';
import 'features/dashboard/dashboard_page.dart';
import 'features/patients/patient_list_page.dart';
import 'features/patients/patient_detail_page.dart';
import 'features/patients/patient_form_page.dart';
import 'features/orders/order_list_page.dart';
import 'features/orders/order_detail_page.dart';
import 'features/orders/order_create_page.dart';
import 'features/samples/sample_list_page.dart';
import 'features/samples/sample_detail_page.dart';
import 'features/samples/sample_collection_page.dart';
import 'features/results/result_list_page.dart';
import 'features/results/result_detail_page.dart';
import 'features/results/result_entry_page.dart';
import 'features/results/result_validation_page.dart';
import 'features/reports/report_list_page.dart';
import 'features/reports/report_viewer_page.dart';
import 'features/reports/report_generator_page.dart';
import 'features/notifications/notification_list_page.dart';
import 'features/inventory/inventory_page.dart';
import 'features/billing/billing_page.dart';
import 'features/pharmacy/pharmacy_page.dart';
import 'features/radiology/radiology_page.dart';
import 'features/bloodbank/bloodbank_page.dart';
import 'features/emergency/emergency_page.dart';
import 'features/settings/settings_page.dart';
import 'features/identity/memberships_page.dart';
import 'features/identity/workspace_page.dart';
import 'features/identity/security_center_page.dart';
import 'features/search/global_search_page.dart';
import 'features/admin/user_management_page.dart';
import 'features/admin/audit_log_page.dart';
import 'features/admin/system_config_page.dart';
import 'widgets/layout/desktop_scaffold.dart';

class AppRouter {
  final AuthProvider authProvider;

  AppRouter({required this.authProvider});

  late final GoRouter router = GoRouter(
    initialLocation: '/dashboard',
    refreshListenable: authProvider,
    redirect: _guardRoutes,
    routes: [
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const LoginPage(),
      ),
      GoRoute(
        path: '/mfa',
        name: 'mfa',
        builder: (context, state) => const MfaPage(),
      ),
      GoRoute(
        path: '/forgot-password',
        name: 'forgotPassword',
        builder: (context, state) => const ForgotPasswordPage(),
      ),
      GoRoute(
        path: '/account-request',
        name: 'accountRequest',
        builder: (context, state) => const AccountRequestPage(),
      ),
      ShellRoute(
        builder: (context, state, child) => DesktopScaffold(child: child),
        routes: [
          GoRoute(
            path: '/dashboard',
            name: 'dashboard',
            builder: (context, state) => const DashboardPage(),
          ),
          GoRoute(
            path: '/patients',
            name: 'patients',
            builder: (context, state) => const PatientListPage(),
            routes: [
              GoRoute(
                path: 'new',
                name: 'patientNew',
                builder: (context, state) => const PatientFormPage(),
              ),
              GoRoute(
                path: ':patientId',
                name: 'patientDetail',
                builder: (context, state) => PatientDetailPage(
                  patientId: state.pathParameters['patientId']!,
                ),
              ),
              GoRoute(
                path: ':patientId/edit',
                name: 'patientEdit',
                builder: (context, state) => PatientFormPage(
                  patientId: state.pathParameters['patientId'],
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/orders',
            name: 'orders',
            builder: (context, state) => const OrderListPage(),
            routes: [
              GoRoute(
                path: 'new',
                name: 'orderNew',
                builder: (context, state) => const OrderCreatePage(),
              ),
              GoRoute(
                path: ':orderId',
                name: 'orderDetail',
                builder: (context, state) =>
                    OrderDetailPage(orderId: state.pathParameters['orderId']!),
              ),
            ],
          ),
          GoRoute(
            path: '/samples',
            name: 'samples',
            builder: (context, state) => const SampleListPage(),
            routes: [
              GoRoute(
                path: 'collect',
                name: 'sampleCollect',
                builder: (context, state) => const SampleCollectionPage(),
              ),
              GoRoute(
                path: ':sampleId',
                name: 'sampleDetail',
                builder: (context, state) => SampleDetailPage(
                  sampleId: state.pathParameters['sampleId']!,
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/results',
            name: 'results',
            builder: (context, state) => const ResultListPage(),
            routes: [
              GoRoute(
                path: 'entry',
                name: 'resultEntry',
                builder: (context, state) => const ResultEntryPage(),
              ),
              GoRoute(
                path: 'validation',
                name: 'resultValidation',
                builder: (context, state) => const ResultValidationPage(),
              ),
              GoRoute(
                path: ':resultId',
                name: 'resultDetail',
                builder: (context, state) => ResultDetailPage(
                  resultId: state.pathParameters['resultId']!,
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/reports',
            name: 'reports',
            builder: (context, state) => const ReportListPage(),
            routes: [
              GoRoute(
                path: 'generate',
                name: 'reportGenerate',
                builder: (context, state) => const ReportGeneratorPage(),
              ),
              GoRoute(
                path: ':reportId',
                name: 'reportView',
                builder: (context, state) => ReportViewerPage(
                  reportId: state.pathParameters['reportId']!,
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/memberships',
            name: 'memberships',
            builder: (context, state) => const MembershipsPage(),
          ),
          GoRoute(
            path: '/workspace',
            name: 'workspace',
            builder: (context, state) => const WorkspacePage(),
          ),
          GoRoute(
            path: '/security',
            name: 'security',
            builder: (context, state) => const SecurityCenterPage(),
          ),
          GoRoute(
            path: '/notifications',
            name: 'notifications',
            builder: (context, state) => const NotificationListPage(),
          ),
          GoRoute(
            path: '/inventory',
            name: 'inventory',
            builder: (context, state) => const InventoryPage(),
          ),
          GoRoute(
            path: '/billing',
            name: 'billing',
            builder: (context, state) => const BillingPage(),
          ),
          GoRoute(
            path: '/pharmacy',
            name: 'pharmacy',
            builder: (context, state) => const PharmacyPage(),
          ),
          GoRoute(
            path: '/radiology',
            name: 'radiology',
            builder: (context, state) => const RadiologyPage(),
          ),
          GoRoute(
            path: '/bloodbank',
            name: 'bloodbank',
            builder: (context, state) => const BloodBankPage(),
          ),
          GoRoute(
            path: '/emergency',
            name: 'emergency',
            builder: (context, state) => const EmergencyPage(),
          ),
          GoRoute(
            path: '/settings',
            name: 'settings',
            builder: (context, state) => const SettingsPage(),
            routes: [
              GoRoute(
                path: 'users',
                name: 'userManagement',
                builder: (context, state) => const UserManagementPage(),
              ),
              GoRoute(
                path: 'audit',
                name: 'auditLog',
                builder: (context, state) => const AuditLogPage(),
              ),
              GoRoute(
                path: 'system',
                name: 'systemConfig',
                builder: (context, state) => const SystemConfigPage(),
              ),
            ],
          ),
          GoRoute(
            path: '/search',
            name: 'search',
            builder: (context, state) => const GlobalSearchPage(),
          ),
        ],
      ),
    ],
  );

  String? _guardRoutes(BuildContext context, GoRouterState state) {
    if (authProvider.identityState == IdentityState.unknown ||
        authProvider.identityState == IdentityState.loading) {
      return null;
    }
    final isAuthenticated = authProvider.isAuthenticated;
    final isMfaRequired = authProvider.isMfaRequired;
    final isLoginRoute = state.matchedLocation == '/login';
    final isMfaRoute = state.matchedLocation == '/mfa';
    final isForgotPasswordRoute = state.matchedLocation == '/forgot-password';
    final isAccountRequestRoute = state.matchedLocation == '/account-request';
    final isIdentityPublicRoute =
        isLoginRoute ||
        isForgotPasswordRoute ||
        isAccountRequestRoute ||
        isMfaRoute;

    if (!isAuthenticated && !isLoginRoute && !isIdentityPublicRoute) {
      return '/login';
    }

    if (isAuthenticated && isLoginRoute) {
      return '/dashboard';
    }

    if (isMfaRequired && !isMfaRoute && !isLoginRoute) {
      return '/mfa';
    }

    final workspaceRoute = state.matchedLocation == '/workspace';
    final identityRoute =
        state.matchedLocation == '/memberships' ||
        state.matchedLocation == '/security';
    if (authProvider.identityState == IdentityState.workspaceRequired &&
        !workspaceRoute &&
        !identityRoute) {
      return '/workspace';
    }

    return null;
  }
}
