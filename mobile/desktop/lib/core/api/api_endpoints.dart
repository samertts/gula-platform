class ApiEndpoints {
  ApiEndpoints._();

  static const String baseUrl = '/api/v1';

  // Auth
  static const String login = '/login';
  static const String register = '/register';
  static const String logout = '/logout';
  static const String session = '/session';
  static const String myMemberships = '/niam/memberships/me';
  static const String workspaces = '/niam/workspaces';
  static String switchWorkspace(String workspaceId) =>
      '/niam/workspaces/$workspaceId/switch';
  static const String effectivePermissions = '/niam/roles/effective';
  static const String demoAccess = '/demo/access';
  static const String refreshToken = '/auth/refresh';
  static const String verifyMfa = '/auth/mfa/verify';
  static const String setupMfa = '/auth/mfa/setup';
  static const String forgotPassword = '/auth/forgot-password';
  static const String resetPassword = '/auth/reset-password';
  static const String changePassword = '/auth/change-password';
  static const String accountRequests = '/niam/account-requests/';
  static String accountSessions(String accountId) =>
      '/niam/sessions/account/$accountId';
  static String terminateAllSessions(String accountId) =>
      '/niam/sessions/account/$accountId/terminate-all';
  static const String mfaStatus = '/mfa/status';
  static const String mfaDevices = '/mfa/devices';
  static const String securityStatus = '/security/status';

  // Labs
  static const String myLab = '/labs/me';
  static String lab(int labId) => '/labs/$labId';
  static String labUsers(int labId) => '/labs/$labId/users';
  static const String registerStaff = '/register/staff';

  // Patients
  static const String patients = '/patients';
  static String patient(int patientId) => '/patients/$patientId';
  static String patientCard(int patientId) => '/patient-card/$patientId';
  static String patientCardQr(int patientId) =>
      '/patient-card/$patientId/qr.png';
  static const String scanPatientCard = '/patient-card/scan';
  static String patientHistory(int patientId) =>
      '/patient-card/$patientId/history';
  static String family(String familyId) => '/patients/family/$familyId';
  static String patientChildren(int patientId) =>
      '/patients/$patientId/children';

  // Orders
  static const String orders = '/results/orders';
  static String order(int orderId) => '/results/orders/$orderId';
  static String validateOrder(int orderId) =>
      '/results/orders/$orderId/validate';
  static String cancelOrder(int orderId) => '/results/orders/$orderId/cancel';
  static const String batchOrders = '/batch/orders';

  // Results
  static const String results = '/device-results/results';
  static String resultByToken(String token) => '/results/r/$token';
  static String resultPdf(String token) => '/results/r/$token/pdf';
  static const String testProfiles = '/results/test-profiles';
  static const String testResults = '/test-results';

  // Analytics
  static const String analyze = '/results/analyze';
  static String orderIntelligence(int orderId) =>
      '/results/orders/$orderId/intelligence';

  // AI
  static const String aiSuggest = '/ai/suggest';
  static const String aiPending = '/ai/pending';
  static String aiApprove(int approvalId) => '/ai/approve/$approvalId';
  static String aiReject(int approvalId) => '/ai/reject/$approvalId';
  static const String criticalAlerts = '/ai/critical-alerts';

  // Dashboard
  static const String dashboard = '/dashboard';
  static const String stats = '/stats';

  // Notifications
  static const String sendNotification = '/notifications/send';
  static String notificationHistory(int orderId) =>
      '/notifications/history/$orderId';

  // Edge
  static const String edgeDevices = '/edge/devices';
  static String edgeDevice(String deviceId) => '/edge/devices/$deviceId';
  static String quarantineDevice(String deviceId) =>
      '/edge/devices/$deviceId/quarantine';
  static String revokeDevice(String deviceId) =>
      '/edge/devices/$deviceId/revoke';
  static String reinstateDevice(String deviceId) =>
      '/edge/devices/$deviceId/reinstate';
  static const String edgeTasks = '/edge/tasks';
  static String edgeTask(String taskUid) => '/edge/tasks/$taskUid';
  static String cancelEdgeTask(String taskUid) => '/edge/tasks/$taskUid/cancel';
  static const String edgePolicy = '/edge/policy';
  static const String edgeFleetSummary = '/edge/fleet/summary';
  static const String edgeModels = '/edge/models';
  static String edgeModelStatus(String modelUid) =>
      '/edge/models/$modelUid/status';
  static String assignEdgeModel(String modelUid) =>
      '/edge/models/$modelUid/assign';
  static const String agentHeartbeat = '/edge/agent/heartbeat';
  static String agentTaskResult(String taskUid) =>
      '/edge/agent/tasks/$taskUid/result';
  static const String agentTelemetry = '/edge/agent/telemetry';

  // MPI
  static const String mpiResolve = '/mpi/resolve';
  static String citizen(String citizenUlid) => '/mpi/citizens/$citizenUlid';
  static const String mpiMerge = '/mpi/merge';
  static const String pendingReviews = '/mpi/review/pending';
  static String decideReview(int claimId) => '/mpi/review/$claimId/decide';

  // Quality Control
  static const String qualityControl = '/quality-control';
  static const String qcStatistics = '/quality-control/statistics';
  static const String leveyJennings = '/quality-control/levey-jennings';

  // Compliance
  static const String complianceInfo = '/compliance/info';
  static const String securityReport = '/compliance/security-report';
  static const String auditSummary = '/compliance/audit-summary';
  static String fhirPatient(int patientId) =>
      '/compliance/fhir/patient/$patientId';
  static String fhirReport(int orderId) =>
      '/compliance/fhir/diagnostic-report/$orderId';

  // National ID
  static const String verifyNationalId = '/national-id/verify';

  // Integrations
  static const String integrationStatuses = '/integrations/status';
  static String probeIntegration(String name) => '/integrations/$name/probe';

  // Tiers
  static const String tierMatrix = '/tiers';
  static const String mySubscription = '/tiers/my';
  static const String upgradeRequest = '/tiers/upgrade';
  static const String upgradeDemand = '/tiers/admin/demands';
  static String featureFlags(int labId) => '/tiers/flags?lab_id=$labId';

  // Consent
  static const String grantConsent = '/consent/grant';
  static const String revokeConsent = '/consent/revoke';
  static const String checkConsent = '/consent/check';

  // Claims
  static const String claims = '/claims';
  static String claim(int claimId) => '/claims/$claimId';

  // Health
  static const String health = '/health';
  static const String healthDeep = '/health/deep';
  static const String healthReady = '/health/ready';
  static const String healthStatus = '/health/status';

  // Users / Admin
  static const String users = '/users';
  static String user(int userId) => '/users/$userId';
  static const String auditLogs = '/audit/logs';
  static const String systemConfig = '/system/config';
}
