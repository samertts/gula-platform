import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';

import 'src/enums.dart';
import 'src/exceptions.dart';
import 'src/models/ai.dart';
import 'src/models/auth.dart';
import 'src/models/claim.dart';
import 'src/models/consent.dart';
import 'src/models/edge.dart';
import 'src/models/fhir.dart';
import 'src/models/governance.dart';
import 'src/models/lab.dart';
import 'src/models/lims.dart';
import 'src/models/mpi.dart';
import 'src/models/notification.dart';
import 'src/models/order.dart';
import 'src/models/patient.dart';
import 'src/models/qc.dart';
import 'src/models/result.dart';
import 'src/models/subscription.dart';
import 'src/sync/offline_sync.dart';

class GulaClient {
  final Dio _dio;
  final String _baseUrl;
  String? _token;
  String? _refreshToken;
  final Uuid _uuid = const Uuid();
  late final OfflineSyncManager offlineSync;
  final ValueNotifier<bool> isOnline;

  GulaClient({
    required String baseUrl,
    String? token,
    String? refreshToken,
    Dio? dio,
    bool enableOfflineSync = false,
  })  : _baseUrl = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl,
        _token = token,
        _refreshToken = refreshToken,
        _dio = dio ?? Dio(),
        isOnline = ValueNotifier(true) {
    _dio.options.baseUrl = _baseUrl;
    _dio.options.connectTimeout = const Duration(seconds: 15);
    _dio.options.receiveTimeout = const Duration(seconds: 30);
    _dio.options.sendTimeout = const Duration(seconds: 15);

    _dio.interceptors.add(_AuthInterceptor(this));
    _dio.interceptors.add(_RetryInterceptor(dio: _dio));
    _dio.interceptors.add(_LoggingInterceptor());

    if (enableOfflineSync) {
      offlineSync = OfflineSyncManager(dio: _dio);
      offlineSync.init();
      isOnline = offlineSync.isOnline;
    }
  }

  String? get token => _token;

  void setToken(String token) {
    _token = token;
  }

  void setTokens({required String token, String? refreshToken}) {
    _token = token;
    if (refreshToken != null) _refreshToken = refreshToken;
  }

  void clearToken() {
    _token = null;
    _refreshToken = null;
  }

  Uri _buildUri(String path, [Map<String, dynamic>? queryParams]) {
    final uri = Uri.parse('$_baseUrl$path');
    if (queryParams != null && queryParams.isNotEmpty) {
      return uri.replace(queryParameters: queryParams.map(
        (k, v) => MapEntry(k, v.toString()),
      ));
    }
    return uri;
  }

  Map<String, dynamic> _idempotencyHeaders() {
    return {'Idempotency-Key': _uuid.v4()};
  }

  Future<Response<T>> _request<T>(
    String method,
    String path, {
    Map<String, dynamic>? queryParams,
    dynamic data,
    bool idempotent = false,
  }) async {
    try {
      final options = Options(method: method);
      if (idempotent && (method == 'POST' || method == 'PATCH' || method == 'PUT')) {
        options.extra ??= {};
        options.extra!['idempotency_key'] = _uuid.v4();
      }
      final uri = _buildUri(path, queryParams);
      return await _dio.request<T>(
        uri.toString(),
        data: data,
        options: options,
      );
    } on DioException catch (e) {
      _handleDioError(e);
    }
  }

  Never _handleDioError(DioException e) {
    final data = e.response?.data;
    final map = data is Map<String, dynamic> ? data : null;
    throw parseDioError(map, e.response?.statusCode);
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Auth
  // ───────────────────────────────────────────────────────────────────────────
  Future<LoginResponse> login({required String email, required String password}) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/login',
      data: LoginRequest(email: email, password: password).toJson(),
    );
    final loginRes = LoginResponse.fromJson(res.data!);
    _token = loginRes.token;
    _refreshToken = loginRes.refreshToken;
    return loginRes;
  }

  Future<void> logout() async {
    try {
      await _request('POST', '/logout');
    } finally {
      clearToken();
    }
  }

  Future<LoginResponse> register(RegisterRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/register',
      data: request.toJson(),
    );
    final loginRes = LoginResponse.fromJson(res.data!);
    _token = loginRes.token;
    _refreshToken = loginRes.refreshToken;
    return loginRes;
  }

  Future<RefreshTokenResponse> refreshToken(String refreshToken) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/auth/refresh',
      data: RefreshTokenRequest(refreshToken: refreshToken).toJson(),
    );
    final refreshRes = RefreshTokenResponse.fromJson(res.data!);
    _token = refreshRes.token;
    _refreshToken = refreshRes.refreshToken;
    return refreshRes;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Labs
  // ───────────────────────────────────────────────────────────────────────────
  Future<Lab> getMyLab() async {
    final res = await _request<Map<String, dynamic>>('GET', '/labs/me');
    return Lab.fromJson(res.data!);
  }

  Future<Lab> updateLab(int labId, LabUpdateRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'PUT',
      '/labs/$labId',
      data: request.toJson(),
    );
    return Lab.fromJson(res.data!);
  }

  Future<List<LabUser>> getLabUsers(int labId) async {
    final res = await _request<List>('GET', '/labs/$labId/users');
    return res.data!.map((e) => LabUser.fromJson(e)).toList();
  }

  Future<LabUser> createStaff(StaffCreateRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/register/staff',
      data: request.toJson(),
    );
    return LabUser.fromJson(res.data!);
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Patients
  // ───────────────────────────────────────────────────────────────────────────
  Future<List<Patient>> getPatients({
    int? labId,
    String? search,
    int page = 1,
    int perPage = 50,
  }) async {
    final params = <String, dynamic>{
      'page': page,
      'per_page': perPage,
      if (labId != null) 'lab_id': labId,
      if (search != null) 'search': search,
    };
    final res = await _request<List>('GET', '/patients', queryParams: params);
    return res.data!.map((e) => Patient.fromJson(e)).toList();
  }

  Future<Patient> getPatient(int patientId) async {
    final res = await _request<Map<String, dynamic>>('GET', '/patients/$patientId');
    return Patient.fromJson(res.data!);
  }

  Future<Patient> createPatient(PatientCreateRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/patients',
      data: request.toJson(),
      idempotent: true,
    );
    return Patient.fromJson(res.data!);
  }

  Future<Patient> updatePatient(int patientId, PatientUpdateRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'PUT',
      '/patients/$patientId',
      data: request.toJson(),
    );
    return Patient.fromJson(res.data!);
  }

  Future<List<Patient>> getFamily(String familyId) async {
    final res = await _request<List>('GET', '/patients/family/$familyId');
    return res.data!.map((e) => Patient.fromJson(e)).toList();
  }

  Future<List<Patient>> getPatientChildren(int patientId) async {
    final res = await _request<List>('GET', '/patients/$patientId/children');
    return res.data!.map((e) => Patient.fromJson(e)).toList();
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Patient Card (QR)
  // ───────────────────────────────────────────────────────────────────────────
  Future<PatientCardResponse> getPatientCard(int patientId) async {
    final res = await _request<Map<String, dynamic>>('GET', '/patient-card/$patientId');
    return PatientCardResponse.fromJson(res.data!);
  }

  Future<Uint8List> getPatientCardQr(int patientId) async {
    final res = await _request<List<int>>(
      'GET',
      '/patient-card/$patientId/qr.png',
    );
    return Uint8List.fromList(res.data!);
  }

  Future<Patient> scanPatientCard(String token) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/patient-card/scan',
      data: {'token': token},
    );
    return Patient.fromJson(res.data!);
  }

  Future<List<LabOrder>> getPatientHistory(int patientId) async {
    final res = await _request<List>('GET', '/patient-card/$patientId/history');
    return res.data!.map((e) => LabOrder.fromJson(e)).toList();
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Orders
  // ───────────────────────────────────────────────────────────────────────────
  Future<List<LabOrder>> getOrders({
    int? labId,
    int? patientId,
    OrderStatus? status,
    int page = 1,
    int perPage = 50,
  }) async {
    final params = <String, dynamic>{
      'page': page,
      'per_page': perPage,
      if (labId != null) 'lab_id': labId,
      if (patientId != null) 'patient_id': patientId,
      if (status != null) 'status': status.name,
    };
    final res = await _request<List>('GET', '/results/orders', queryParams: params);
    return res.data!.map((e) => LabOrder.fromJson(e)).toList();
  }

  Future<LabOrder> getOrder(int orderId) async {
    final res = await _request<Map<String, dynamic>>('GET', '/results/orders/$orderId');
    return LabOrder.fromJson(res.data!);
  }

  Future<LabOrder> createOrder(OrderCreateRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/results/orders',
      data: request.toJson(),
      idempotent: true,
    );
    return LabOrder.fromJson(res.data!);
  }

  Future<List<LabOrder>> batchCreateOrders(BatchOrderRequest request) async {
    final res = await _request<List>(
      'POST',
      '/batch/orders',
      data: request.toJson(),
      idempotent: true,
    );
    return res.data!.map((e) => LabOrder.fromJson(e)).toList();
  }

  Future<LabOrder> validateOrder(int orderId, OrderValidateRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/results/orders/$orderId/validate',
      data: request.toJson(),
    );
    return LabOrder.fromJson(res.data!);
  }

  Future<LabOrder> cancelOrder(int orderId) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/results/orders/$orderId/cancel',
    );
    return LabOrder.fromJson(res.data!);
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Results
  // ───────────────────────────────────────────────────────────────────────────
  Future<LabResult> createResult(ResultCreateRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/device-results/results',
      data: request.toJson(),
      idempotent: true,
    );
    return LabResult.fromJson(res.data!);
  }

  Future<LabResult> getResultByToken(String token) async {
    final res = await _request<Map<String, dynamic>>('GET', '/results/r/$token');
    return LabResult.fromJson(res.data!);
  }

  Future<Uint8List> getResultPdf(String token) async {
    final res = await _request<List<int>>('GET', '/results/r/$token/pdf');
    return Uint8List.fromList(res.data!);
  }

  Future<List<TestType>> getTestProfiles() async {
    final res = await _request<List>('GET', '/results/test-profiles');
    return res.data!.map((e) => TestType.fromJson(e)).toList();
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Test Results (CMD-008)
  // ───────────────────────────────────────────────────────────────────────────
  Future<TestResult> createTestResult(Map<String, dynamic> payload) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/test-results',
      data: payload,
      idempotent: true,
    );
    return TestResult.fromJson(res.data!);
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Analytics / Intelligence
  // ───────────────────────────────────────────────────────────────────────────
  Future<AnalyzeResponse> analyzeOrder(int orderId) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/results/analyze',
      data: AnalyzeRequest(orderId: orderId).toJson(),
    );
    return AnalyzeResponse.fromJson(res.data!);
  }

  Future<OrderIntelligence> getOrderIntelligence(int orderId) async {
    final res = await _request<Map<String, dynamic>>(
      'GET',
      '/results/orders/$orderId/intelligence',
    );
    return OrderIntelligence.fromJson(res.data!);
  }

  // ───────────────────────────────────────────────────────────────────────────
  // AI
  // ───────────────────────────────────────────────────────────────────────────
  Future<AiSuggestionResponse> getAiSuggestion(AiSuggestionRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/ai/suggest',
      data: request.toJson(),
    );
    return AiSuggestionResponse.fromJson(res.data!);
  }

  Future<List<AiPendingApproval>> getAiPendingApprovals() async {
    final res = await _request<List>('GET', '/ai/pending');
    return res.data!.map((e) => AiPendingApproval.fromJson(e)).toList();
  }

  Future<void> approveAiSuggestion(int approvalId) async {
    await _request('POST', '/ai/approve/$approvalId');
  }

  Future<void> rejectAiSuggestion(int approvalId) async {
    await _request('POST', '/ai/reject/$approvalId');
  }

  Future<List<AiCriticalAlert>> getCriticalAlerts() async {
    final res = await _request<List>('GET', '/ai/critical-alerts');
    return res.data!.map((e) => AiCriticalAlert.fromJson(e)).toList();
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Consent
  // ───────────────────────────────────────────────────────────────────────────
  Future<GrantResponse> grantConsent(ConsentGrantRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/consent/grant',
      data: request.toJson(),
      idempotent: true,
    );
    return GrantResponse.fromJson(res.data!);
  }

  Future<RevokeResponse> revokeConsent(RevokeRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/consent/revoke',
      data: request.toJson(),
    );
    return RevokeResponse.fromJson(res.data!);
  }

  Future<CheckResponse> checkConsent(CheckRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'GET',
      '/consent/check',
      queryParams: request.toJson().map((k, v) => MapEntry(k, v.toString())),
    );
    return CheckResponse.fromJson(res.data!);
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Claims
  // ───────────────────────────────────────────────────────────────────────────
  Future<Claim> createClaim(ClaimCreateRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/claims',
      data: request.toJson(),
      idempotent: true,
    );
    return Claim.fromJson(res.data!);
  }

  Future<Claim> getClaim(int claimId) async {
    final res = await _request<Map<String, dynamic>>('GET', '/claims/$claimId');
    return Claim.fromJson(res.data!);
  }

  Future<List<Claim>> getClaims({
    int? labId,
    int? patientId,
    ClaimStatus? status,
    int page = 1,
    int perPage = 50,
  }) async {
    final params = <String, dynamic>{
      'page': page,
      'per_page': perPage,
      if (labId != null) 'lab_id': labId,
      if (patientId != null) 'patient_id': patientId,
      if (status != null) 'status': status.name,
    };
    final res = await _request<List>('GET', '/claims', queryParams: params);
    return res.data!.map((e) => Claim.fromJson(e)).toList();
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Edge Platform
  // ───────────────────────────────────────────────────────────────────────────
  Future<List<EdgeDeviceSummary>> getEdgeDevices() async {
    final res = await _request<List>('GET', '/edge/devices');
    return res.data!.map((e) => EdgeDeviceSummary.fromJson(e)).toList();
  }

  Future<EdgeDeviceDetail> getEdgeDevice(String deviceId) async {
    final res = await _request<Map<String, dynamic>>('GET', '/edge/devices/$deviceId');
    return EdgeDeviceDetail.fromJson(res.data!);
  }

  Future<void> quarantineEdgeDevice(String deviceId) async {
    await _request('POST', '/edge/devices/$deviceId/quarantine');
  }

  Future<void> revokeEdgeDevice(String deviceId) async {
    await _request('POST', '/edge/devices/$deviceId/revoke');
  }

  Future<void> reinstateEdgeDevice(String deviceId) async {
    await _request('POST', '/edge/devices/$deviceId/reinstate');
  }

  Future<void> toggleEdgeKillSwitch(String deviceId) async {
    await _request('POST', '/edge/devices/$deviceId/kill_switch');
  }

  Future<EdgeTask> createEdgeTask(EdgeTaskCreateRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/edge/tasks',
      data: request.toJson(),
      idempotent: request.idempotencyKey != null,
    );
    return EdgeTask.fromJson(res.data!);
  }

  Future<List<EdgeTaskSummary>> getEdgeTasks({
    String? deviceId,
    EdgeTaskStatus? status,
    int page = 1,
    int perPage = 50,
  }) async {
    final params = <String, dynamic>{
      'page': page,
      'per_page': perPage,
      if (deviceId != null) 'device_id': deviceId,
      if (status != null) 'status': status.name,
    };
    final res = await _request<List>('GET', '/edge/tasks', queryParams: params);
    return res.data!.map((e) => EdgeTaskSummary.fromJson(e)).toList();
  }

  Future<EdgeTask> getEdgeTask(String taskUid) async {
    final res = await _request<Map<String, dynamic>>('GET', '/edge/tasks/$taskUid');
    return EdgeTask.fromJson(res.data!);
  }

  Future<void> cancelEdgeTask(String taskUid) async {
    await _request('POST', '/edge/tasks/$taskUid/cancel');
  }

  Future<EdgePolicy> getEdgePolicy() async {
    final res = await _request<Map<String, dynamic>>('GET', '/edge/policy');
    return EdgePolicy.fromJson(res.data!);
  }

  Future<EdgePolicy> updateEdgePolicy(EdgePolicy policy) async {
    final res = await _request<Map<String, dynamic>>(
      'PUT',
      '/edge/policy',
      data: policy.toJson(),
    );
    return EdgePolicy.fromJson(res.data!);
  }

  Future<FleetSummary> getEdgeFleetSummary() async {
    final res = await _request<Map<String, dynamic>>('GET', '/edge/fleet/summary');
    return FleetSummary.fromJson(res.data!);
  }

  Future<EdgeModel> createEdgeModel(Map<String, dynamic> payload) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/edge/models',
      data: payload,
      idempotent: true,
    );
    return EdgeModel.fromJson(res.data!);
  }

  Future<List<EdgeModel>> getEdgeModels() async {
    final res = await _request<List>('GET', '/edge/models');
    return res.data!.map((e) => EdgeModel.fromJson(e)).toList();
  }

  Future<void> updateEdgeModelStatus(String modelUid, String status) async {
    await _request('POST', '/edge/models/$modelUid/status', data: {'status': status});
  }

  Future<void> assignEdgeModel(String modelUid, Map<String, dynamic> assignment) async {
    await _request('POST', '/edge/models/$modelUid/assign', data: assignment);
  }

  Future<HeartbeatResponse> agentHeartbeat(HeartbeatRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/edge/agent/heartbeat',
      data: request.toJson(),
    );
    return HeartbeatResponse.fromJson(res.data!);
  }

  Future<void> agentSubmitResult(String taskUid, Map<String, dynamic> result) async {
    await _request('POST', '/edge/agent/tasks/$taskUid/result', data: result);
  }

  Future<void> agentSubmitTelemetry(Map<String, dynamic> telemetry) async {
    await _request('POST', '/edge/agent/telemetry', data: telemetry);
  }

  // ───────────────────────────────────────────────────────────────────────────
  // MPI
  // ───────────────────────────────────────────────────────────────────────────
  Future<MpiResolveResponse> resolveIdentity(MpiResolveRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/mpi/resolve',
      data: request.toJson(),
    );
    return MpiResolveResponse.fromJson(res.data!);
  }

  Future<CitizenResponse> getCitizen(String citizenUlid) async {
    final res = await _request<Map<String, dynamic>>('GET', '/mpi/citizens/$citizenUlid');
    return CitizenResponse.fromJson(res.data!);
  }

  Future<MpiMergeResponse> mergeIdentities(MpiMergeRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/mpi/merge',
      data: request.toJson(),
    );
    return MpiMergeResponse.fromJson(res.data!);
  }

  Future<PendingReviewPage> getPendingReviews({int page = 1, int perPage = 50}) async {
    final params = <String, dynamic>{'page': page, 'per_page': perPage};
    final res = await _request<Map<String, dynamic>>(
      'GET',
      '/mpi/review/pending',
      queryParams: params,
    );
    return PendingReviewPage.fromJson(res.data!);
  }

  Future<void> decideReview(int claimId, ResolveDecision decision) async {
    await _request('POST', '/mpi/review/$claimId/decide', data: decision.toJson());
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Quality Control
  // ───────────────────────────────────────────────────────────────────────────
  Future<QualityControl> createQcRecord(QcCreateRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/quality-control',
      data: request.toJson(),
      idempotent: true,
    );
    return QualityControl.fromJson(res.data!);
  }

  Future<List<QualityControl>> getQcRecords({
    int? labId,
    String? testCode,
    int page = 1,
    int perPage = 50,
  }) async {
    final params = <String, dynamic>{
      'page': page,
      'per_page': perPage,
      if (labId != null) 'lab_id': labId,
      if (testCode != null) 'test_code': testCode,
    };
    final res = await _request<List>('GET', '/quality-control', queryParams: params);
    return res.data!.map((e) => QualityControl.fromJson(e)).toList();
  }

  Future<QcStatistics> getQcStatistics({
    required int labId,
    required String testCode,
  }) async {
    final params = <String, dynamic>{'lab_id': labId, 'test_code': testCode};
    final res = await _request<Map<String, dynamic>>(
      'GET',
      '/quality-control/statistics',
      queryParams: params,
    );
    return QcStatistics.fromJson(res.data!);
  }

  Future<List<LeveyJenningsPoint>> getLeveyJenningsChart({
    required int labId,
    required String testCode,
    int days = 30,
  }) async {
    final params = <String, dynamic>{
      'lab_id': labId,
      'test_code': testCode,
      'days': days,
    };
    final res = await _request<List>(
      'GET',
      '/quality-control/levey-jennings',
      queryParams: params,
    );
    return res.data!.map((e) => LeveyJenningsPoint.fromJson(e)).toList();
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Notifications
  // ───────────────────────────────────────────────────────────────────────────
  Future<NotificationSendResponse> sendNotification(NotificationSendRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/notifications/send',
      data: request.toJson(),
    );
    return NotificationSendResponse.fromJson(res.data!);
  }

  Future<List<NotificationHistoryItem>> getNotificationHistory(int orderId) async {
    final res = await _request<List>('GET', '/notifications/history/$orderId');
    return res.data!.map((e) => NotificationHistoryItem.fromJson(e)).toList();
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Subscription / Tiers
  // ───────────────────────────────────────────────────────────────────────────
  Future<List<TierMatrix>> getTierMatrix() async {
    final res = await _request<List>('GET', '/tiers');
    return res.data!.map((e) => TierMatrix.fromJson(e)).toList();
  }

  Future<LabSubscription> getMySubscription() async {
    final res = await _request<Map<String, dynamic>>('GET', '/tiers/my');
    return LabSubscription.fromJson(res.data!);
  }

  Future<UpgradeRequest> requestUpgrade(TierUpgradeRequest request) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/tiers/upgrade',
      data: request.toJson(),
    );
    return UpgradeRequest.fromJson(res.data!);
  }

  Future<UpgradeDemandScore> getUpgradeDemand(int labId) async {
    final res = await _request<Map<String, dynamic>>('GET', '/tiers/admin/demands');
    return UpgradeDemandScore.fromJson(res.data!);
  }

  Future<List<FeatureFlag>> getFeatureFlags(int labId) async {
    final res = await _request<List>('GET', '/tiers/flags', queryParams: {'lab_id': labId});
    return res.data!.map((e) => FeatureFlag.fromJson(e)).toList();
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Dashboard / Stats
  // ───────────────────────────────────────────────────────────────────────────
  Future<DashboardResponse> getDashboard() async {
    final res = await _request<Map<String, dynamic>>('GET', '/dashboard');
    return DashboardResponse.fromJson(res.data!);
  }

  Future<StatsResponse> getStats({
    int? labId,
    String? from,
    String? to,
  }) async {
    final params = <String, dynamic>{
      if (labId != null) 'lab_id': labId,
      if (from != null) 'from': from,
      if (to != null) 'to': to,
    };
    final res = await _request<Map<String, dynamic>>('GET', '/stats', queryParams: params);
    return StatsResponse.fromJson(res.data!);
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Compliance / FHIR
  // ───────────────────────────────────────────────────────────────────────────
  Future<ComplianceReport> getComplianceInfo() async {
    final res = await _request<Map<String, dynamic>>('GET', '/compliance/info');
    return ComplianceReport.fromJson(res.data!);
  }

  Future<SecurityReport> getSecurityReport() async {
    final res = await _request<Map<String, dynamic>>('GET', '/compliance/security-report');
    return SecurityReport.fromJson(res.data!);
  }

  Future<List<AuditLogEntry>> getAuditSummary({
    int page = 1,
    int perPage = 50,
  }) async {
    final params = <String, dynamic>{'page': page, 'per_page': perPage};
    final res = await _request<List>(
      'GET',
      '/compliance/audit-summary',
      queryParams: params,
    );
    return res.data!.map((e) => AuditLogEntry.fromJson(e)).toList();
  }

  Future<FhirPatient> getFhirPatient(int patientId) async {
    final res = await _request<Map<String, dynamic>>(
      'GET',
      '/compliance/fhir/patient/$patientId',
    );
    return FhirPatient.fromJson(res.data!);
  }

  Future<FhirDiagnosticReport> getFhirDiagnosticReport(int orderId) async {
    final res = await _request<Map<String, dynamic>>(
      'GET',
      '/compliance/fhir/diagnostic-report/$orderId',
    );
    return FhirDiagnosticReport.fromJson(res.data!);
  }

  // ───────────────────────────────────────────────────────────────────────────
  // National Identity
  // ───────────────────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> verifyNationalId(String nationalId) async {
    final res = await _request<Map<String, dynamic>>(
      'POST',
      '/national-id/verify',
      data: {'national_id': nationalId},
    );
    return res.data!;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Integrations
  // ───────────────────────────────────────────────────────────────────────────
  Future<List<IntegrationStatus>> getIntegrationStatuses() async {
    final res = await _request<List>('GET', '/integrations/status');
    return res.data!.map((e) => IntegrationStatus.fromJson(e)).toList();
  }

  Future<Map<String, dynamic>> probeIntegration(String name) async {
    final res = await _request<Map<String, dynamic>>('POST', '/integrations/$name/probe');
    return res.data!;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Health
  // ───────────────────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> health() async {
    final res = await _request<Map<String, dynamic>>('GET', '/health');
    return res.data!;
  }

  Future<Map<String, dynamic>> healthDeep() async {
    final res = await _request<Map<String, dynamic>>('GET', '/health/deep');
    return res.data!;
  }

  void dispose() {
    _dio.close();
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Interceptors
// ─────────────────────────────────────────────────────────────────────────────

class _AuthInterceptor extends Interceptor {
  final GulaClient _client;

  _AuthInterceptor(this._client);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (_client._token != null) {
      options.headers['Authorization'] = 'Bearer ${_client._token}';
    }
    options.headers['Accept'] = 'application/json';
    options.headers['Content-Type'] = 'application/json';

    final idemKey = options.extra['idempotency_key'] as String?;
    if (idemKey != null) {
      options.headers['Idempotency-Key'] = idemKey;
    }

    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401 && _client._refreshToken != null) {
      try {
        await _client.refreshToken(_client._refreshToken!);
        final opts = err.requestOptions;
        opts.headers['Authorization'] = 'Bearer ${_client._token}';
        final response = await _client._dio.fetch(opts);
        handler.resolve(response);
        return;
      } catch (_) {
        _client.clearToken();
      }
    }
    handler.next(err);
  }
}

class _RetryInterceptor extends Interceptor {
  final Dio dio;
  final int maxRetries;

  _RetryInterceptor({required this.dio, this.maxRetries = 3});

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (_isRetryable(err) && (err.requestOptions.extra['retryCount'] ?? 0) < maxRetries) {
      err.requestOptions.extra['retryCount'] = (err.requestOptions.extra['retryCount'] ?? 0) + 1;
      await Future.delayed(Duration(seconds: 1 * (err.requestOptions.extra['retryCount'] as int)));
      try {
        final response = await dio.fetch(err.requestOptions);
        handler.resolve(response);
        return;
      } catch (_) {}
    }
    handler.next(err);
  }

  bool _isRetryable(DioException err) {
    return err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.connectionError ||
        (err.response != null && err.response!.statusCode! >= 500 && err.response!.statusCode! <= 599);
  }
}

class _LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    debugPrint('[GULA →] ${options.method} ${options.uri}');
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    debugPrint('[GULA ←] ${response.statusCode} ${response.requestOptions.uri}');
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    debugPrint('[GULA ✗] ${err.response?.statusCode} ${err.requestOptions.uri}: ${err.message}');
    handler.next(err);
  }
}
