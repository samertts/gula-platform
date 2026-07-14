import 'package:json_annotation/json_annotation.dart';
import '../enums.dart';

part 'edge.g.dart';

@JsonSerializable()
class EdgeDevice {
  final int id;
  final String deviceId;
  final int labId;
  final int? ownerUserId;
  final String? displayName;
  final EdgeRoleMode roleMode;
  final EdgeDeviceStatus status;
  final double trustScore;
  final String? publicKeyPem;
  final String? certFingerprint;
  final String? attestationBlob;
  final String? agentVersion;
  final String? osPlatform;
  final Map<String, dynamic>? capabilities;
  final DateTime? lastSeenAt;
  final DateTime? registeredAt;
  final DateTime? revokedAt;
  final DateTime? quarantinedAt;
  final bool killSwitched;
  final String? notes;

  const EdgeDevice({
    required this.id,
    required this.deviceId,
    required this.labId,
    this.ownerUserId,
    this.displayName,
    required this.roleMode,
    required this.status,
    required this.trustScore,
    this.publicKeyPem,
    this.certFingerprint,
    this.attestationBlob,
    this.agentVersion,
    this.osPlatform,
    this.capabilities,
    this.lastSeenAt,
    this.registeredAt,
    this.revokedAt,
    this.quarantinedAt,
    required this.killSwitched,
    this.notes,
  });

  factory EdgeDevice.fromJson(Map<String, dynamic> json) => _$EdgeDeviceFromJson(json);
  Map<String, dynamic> toJson() => _$EdgeDeviceToJson(this);
}

@JsonSerializable()
class EdgeDeviceSummary {
  final String deviceId;
  final String? displayName;
  final String status;
  final String? osPlatform;
  final String? agentVersion;
  final DateTime? lastSeenAt;
  final double trustScore;

  const EdgeDeviceSummary({
    required this.deviceId,
    this.displayName,
    required this.status,
    this.osPlatform,
    this.agentVersion,
    this.lastSeenAt,
    required this.trustScore,
  });

  factory EdgeDeviceSummary.fromJson(Map<String, dynamic> json) =>
      _$EdgeDeviceSummaryFromJson(json);
  Map<String, dynamic> toJson() => _$EdgeDeviceSummaryToJson(this);
}

@JsonSerializable()
class EdgeDeviceDetail {
  final EdgeDevice device;
  final List<EdgeTask>? activeTasks;
  final EdgeTelemetry? lastTelemetry;

  const EdgeDeviceDetail({
    required this.device,
    this.activeTasks,
    this.lastTelemetry,
  });

  factory EdgeDeviceDetail.fromJson(Map<String, dynamic> json) =>
      _$EdgeDeviceDetailFromJson(json);
  Map<String, dynamic> toJson() => _$EdgeDeviceDetailToJson(this);
}

@JsonSerializable()
class EdgeTask {
  final int id;
  final String taskUid;
  final String? idempotencyKey;
  final int labId;
  final String? deviceId;
  final String kind;
  final int priority;
  final EdgeTaskStatus status;
  final EdgeTaskPrivacy privacyLevel;
  final Map<String, dynamic>? payload;
  final String? payloadSig;
  final Map<String, dynamic>? requiredCaps;
  final double minTrust;
  final int attempts;
  final int maxAttempts;
  final int timeoutS;
  final DateTime? createdAt;
  final DateTime? dispatchedAt;
  final DateTime? completedAt;
  final DateTime? expiresAt;
  final Map<String, dynamic>? result;
  final String? error;
  final int? submittedByUserId;

  const EdgeTask({
    required this.id,
    required this.taskUid,
    this.idempotencyKey,
    required this.labId,
    this.deviceId,
    required this.kind,
    required this.priority,
    required this.status,
    required this.privacyLevel,
    this.payload,
    this.payloadSig,
    this.requiredCaps,
    required this.minTrust,
    required this.attempts,
    required this.maxAttempts,
    required this.timeoutS,
    this.createdAt,
    this.dispatchedAt,
    this.completedAt,
    this.expiresAt,
    this.result,
    this.error,
    this.submittedByUserId,
  });

  factory EdgeTask.fromJson(Map<String, dynamic> json) => _$EdgeTaskFromJson(json);
  Map<String, dynamic> toJson() => _$EdgeTaskToJson(this);
}

@JsonSerializable()
class EdgeTaskCreateRequest {
  final String? idempotencyKey;
  final int labId;
  final String? deviceId;
  final String kind;
  final int priority;
  final String privacyLevel;
  final Map<String, dynamic>? payload;
  final Map<String, dynamic>? requiredCaps;
  final double minTrust;
  final int maxAttempts;
  final int timeoutS;
  final DateTime? expiresAt;

  const EdgeTaskCreateRequest({
    this.idempotencyKey,
    required this.labId,
    this.deviceId,
    required this.kind,
    this.priority = 5,
    this.privacyLevel = 'standard',
    this.payload,
    this.requiredCaps,
    this.minTrust = 0.0,
    this.maxAttempts = 3,
    this.timeoutS = 60,
    this.expiresAt,
  });

  factory EdgeTaskCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$EdgeTaskCreateRequestFromJson(json);
  Map<String, dynamic> toJson() => _$EdgeTaskCreateRequestToJson(this);
}

@JsonSerializable()
class EdgeTaskSummary {
  final String taskUid;
  final String kind;
  final int priority;
  final String status;
  final String? deviceId;
  final DateTime? createdAt;
  final DateTime? completedAt;

  const EdgeTaskSummary({
    required this.taskUid,
    required this.kind,
    required this.priority,
    required this.status,
    this.deviceId,
    this.createdAt,
    this.completedAt,
  });

  factory EdgeTaskSummary.fromJson(Map<String, dynamic> json) =>
      _$EdgeTaskSummaryFromJson(json);
  Map<String, dynamic> toJson() => _$EdgeTaskSummaryToJson(this);
}

@JsonSerializable()
class HeartbeatRequest {
  final String deviceId;
  final String? agentVersion;
  final double? cpuPct;
  final double? memMb;
  final double? batteryPct;
  final bool? onBattery;
  final List<String>? loadedModels;
  final int? queueDepth;

  const HeartbeatRequest({
    required this.deviceId,
    this.agentVersion,
    this.cpuPct,
    this.memMb,
    this.batteryPct,
    this.onBattery,
    this.loadedModels,
    this.queueDepth,
  });

  factory HeartbeatRequest.fromJson(Map<String, dynamic> json) =>
      _$HeartbeatRequestFromJson(json);
  Map<String, dynamic> toJson() => _$HeartbeatRequestToJson(this);
}

@JsonSerializable()
class HeartbeatResponse {
  final bool killSwitched;
  final List<Map<String, dynamic>>? pendingTasks;
  final DateTime serverTime;

  const HeartbeatResponse({
    required this.killSwitched,
    this.pendingTasks,
    required this.serverTime,
  });

  factory HeartbeatResponse.fromJson(Map<String, dynamic> json) =>
      _$HeartbeatResponseFromJson(json);
  Map<String, dynamic> toJson() => _$HeartbeatResponseToJson(this);
}

@JsonSerializable()
class EdgeTelemetry {
  final int id;
  final String deviceId;
  final int labId;
  final DateTime ts;
  final double? cpuPct;
  final double? memMb;
  final double? memTotalMb;
  final double? gpuPct;
  final double? batteryPct;
  final bool? onBattery;
  final int? idleS;
  final double? netUpKbps;
  final double? netDownKbps;
  final Map<String, dynamic>? loadedModels;
  final int? queueDepth;
  final int? agentUptimeS;
  final int? taskCompletedTotal;
  final int? taskFailedTotal;

  const EdgeTelemetry({
    required this.id,
    required this.deviceId,
    required this.labId,
    required this.ts,
    this.cpuPct,
    this.memMb,
    this.memTotalMb,
    this.gpuPct,
    this.batteryPct,
    this.onBattery,
    this.idleS,
    this.netUpKbps,
    this.netDownKbps,
    this.loadedModels,
    this.queueDepth,
    this.agentUptimeS,
    this.taskCompletedTotal,
    this.taskFailedTotal,
  });

  factory EdgeTelemetry.fromJson(Map<String, dynamic> json) => _$EdgeTelemetryFromJson(json);
  Map<String, dynamic> toJson() => _$EdgeTelemetryToJson(this);
}

@JsonSerializable()
class EdgeModel {
  final int id;
  final String modelUid;
  final String name;
  final String version;
  final String runtime;
  final String format;
  final String? quantization;
  final double? sizeMb;
  final double? minRamMb;
  final double? minVramMb;
  final String? sha256;
  final String? sourceUrl;
  final EdgeModelStatus status;
  final double rolloutPct;
  final DateTime? createdAt;
  final DateTime? retiredAt;
  final Map<String, dynamic>? metadataJson;

  const EdgeModel({
    required this.id,
    required this.modelUid,
    required this.name,
    required this.version,
    this.runtime = 'ollama',
    this.format = 'gguf',
    this.quantization,
    this.sizeMb,
    this.minRamMb,
    this.minVramMb,
    this.sha256,
    this.sourceUrl,
    required this.status,
    required this.rolloutPct,
    this.createdAt,
    this.retiredAt,
    this.metadataJson,
  });

  factory EdgeModel.fromJson(Map<String, dynamic> json) => _$EdgeModelFromJson(json);
  Map<String, dynamic> toJson() => _$EdgeModelToJson(this);
}

@JsonSerializable()
class EdgePolicy {
  final int id;
  final int? labId;
  final int maxConcurrentPerDevice;
  final int maxDevicesPerLab;
  final bool idleOnly;
  final int batteryFloorPct;
  final int cpuCapPct;
  final int ramCapMb;
  final List<String>? allowKinds;
  final List<String>? denyKinds;
  final double minTrustScore;
  final int offlineQueueMax;
  final bool killSwitch;
  final DateTime? updatedAt;
  final int? updatedByUserId;

  const EdgePolicy({
    required this.id,
    this.labId,
    required this.maxConcurrentPerDevice,
    required this.maxDevicesPerLab,
    required this.idleOnly,
    required this.batteryFloorPct,
    required this.cpuCapPct,
    required this.ramCapMb,
    this.allowKinds,
    this.denyKinds,
    required this.minTrustScore,
    required this.offlineQueueMax,
    required this.killSwitch,
    this.updatedAt,
    this.updatedByUserId,
  });

  factory EdgePolicy.fromJson(Map<String, dynamic> json) => _$EdgePolicyFromJson(json);
  Map<String, dynamic> toJson() => _$EdgePolicyToJson(this);
}

@JsonSerializable()
class FleetSummary {
  final int total;
  final int active;
  final int offline;
  final int quarantined;
  final Map<String, int> statusCounts;

  const FleetSummary({
    required this.total,
    required this.active,
    required this.offline,
    required this.quarantined,
    required this.statusCounts,
  });

  factory FleetSummary.fromJson(Map<String, dynamic> json) => _$FleetSummaryFromJson(json);
  Map<String, dynamic> toJson() => _$FleetSummaryToJson(this);
}

@JsonSerializable()
class EdgeEvent {
  final int id;
  final DateTime ts;
  final int? labId;
  final String? deviceId;
  final String eventType;
  final EdgeEventSeverity severity;
  final int? actorUserId;
  final Map<String, dynamic>? details;

  const EdgeEvent({
    required this.id,
    required this.ts,
    this.labId,
    this.deviceId,
    required this.eventType,
    required this.severity,
    this.actorUserId,
    this.details,
  });

  factory EdgeEvent.fromJson(Map<String, dynamic> json) => _$EdgeEventFromJson(json);
  Map<String, dynamic> toJson() => _$EdgeEventToJson(this);
}
