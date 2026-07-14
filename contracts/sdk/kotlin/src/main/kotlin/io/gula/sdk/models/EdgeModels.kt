package io.gula.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class RegisterDeviceRequest(
    @SerialName("public_key_pem") val publicKeyPem: String,
    @SerialName("role_mode") val roleMode: String? = null,
    @SerialName("display_name") val displayName: String? = null,
    @SerialName("agent_version") val agentVersion: String? = null,
    @SerialName("os_platform") val osPlatform: String? = null,
    val capabilities: Map<String, kotlinx.serialization.json.JsonElement>? = null,
    @SerialName("attestation_blob") val attestationBlob: String? = null,
)

@Serializable
data class RegisterDeviceResponse(
    @SerialName("device_id") val deviceId: String,
    val status: String,
    @SerialName("role_mode") val roleMode: String,
    @SerialName("trust_score") val trustScore: Double,
    @SerialName("cert_fingerprint") val certFingerprint: String,
    @SerialName("agent_token") val agentToken: String,
    val nonce: String,
)

@Serializable
data class DeviceSummary(
    @SerialName("device_id") val deviceId: String,
    @SerialName("display_name") val displayName: String? = null,
    @SerialName("role_mode") val roleMode: String,
    val status: String,
    @SerialName("trust_score") val trustScore: Double,
    @SerialName("last_seen_at") val lastSeenAt: String? = null,
    @SerialName("agent_version") val agentVersion: String? = null,
)

@Serializable
data class DeviceDetail(
    @SerialName("device_id") val deviceId: String,
    @SerialName("display_name") val displayName: String? = null,
    @SerialName("role_mode") val roleMode: String,
    val status: String,
    @SerialName("trust_score") val trustScore: Double,
    @SerialName("last_seen_at") val lastSeenAt: String? = null,
    @SerialName("agent_version") val agentVersion: String? = null,
    val capabilities: Map<String, kotlinx.serialization.json.JsonElement>? = null,
    @SerialName("registered_at") val registeredAt: String,
    @SerialName("revoked_at") val revokedAt: String? = null,
    @SerialName("quarantined_at") val quarantinedAt: String? = null,
    @SerialName("kill_switched") val killSwitched: Boolean = false,
    @SerialName("latest_telemetry") val latestTelemetry: TelemetrySnapshot? = null,
)

@Serializable
data class TelemetrySnapshot(
    @SerialName("cpu_pct") val cpuPct: Double? = null,
    @SerialName("mem_mb") val memMb: Double? = null,
    @SerialName("battery_pct") val batteryPct: Double? = null,
    @SerialName("on_battery") val onBattery: Boolean? = null,
    @SerialName("queue_depth") val queueDepth: Int? = null,
)

@Serializable
data class DeviceListResponse(
    val total: Int,
    val devices: List<DeviceSummary>,
)

@Serializable
data class TaskSubmitRequest(
    val kind: String,
    val payload: Map<String, kotlinx.serialization.json.JsonElement>? = null,
    val priority: Int = 5,
    @SerialName("privacy_level") val privacyLevel: String = "standard",
    @SerialName("device_id") val deviceId: String? = null,
    @SerialName("required_caps") val requiredCaps: List<String>? = null,
    @SerialName("min_trust") val minTrust: Double = 0.0,
    @SerialName("max_attempts") val maxAttempts: Int = 3,
    @SerialName("timeout_s") val timeoutS: Int = 60,
    @SerialName("idempotency_key") val idempotencyKey: String? = null,
)

@Serializable
data class TaskResponse(
    @SerialName("task_uid") val taskUid: String,
    val kind: String,
    val status: String,
    val priority: Int,
    @SerialName("device_id") val deviceId: String? = null,
    @SerialName("privacy_level") val privacyLevel: String,
    @SerialName("created_at") val createdAt: String,
    @SerialName("dispatched_at") val dispatchedAt: String? = null,
    @SerialName("completed_at") val completedAt: String? = null,
    @SerialName("expires_at") val expiresAt: String? = null,
    val result: Map<String, kotlinx.serialization.json.JsonElement>? = null,
    val error: String? = null,
)

@Serializable
data class TaskListResponse(
    val total: Int,
    val tasks: List<TaskResponse>,
)

@Serializable
data class EdgePolicyResponse(
    @SerialName("max_concurrent_per_device") val maxConcurrentPerDevice: Int = 2,
    @SerialName("max_devices_per_lab") val maxDevicesPerLab: Int = 50,
    @SerialName("idle_only") val idleOnly: Boolean = true,
    @SerialName("battery_floor_pct") val batteryFloorPct: Int = 30,
    @SerialName("cpu_cap_pct") val cpuCapPct: Int = 60,
    @SerialName("ram_cap_mb") val ramCapMb: Int = 2048,
    @SerialName("allow_kinds") val allowKinds: List<String>? = null,
    @SerialName("deny_kinds") val denyKinds: List<String>? = null,
    @SerialName("min_trust_score") val minTrustScore: Double = 50.0,
    @SerialName("offline_queue_max") val offlineQueueMax: Int = 500,
    @SerialName("kill_switch") val killSwitch: Boolean = false,
    @SerialName("updated_at") val updatedAt: String? = null,
)

@Serializable
data class EdgePolicyUpdate(
    @SerialName("idle_only") val idleOnly: Boolean? = null,
    @SerialName("battery_floor_pct") val batteryFloorPct: Int? = null,
    @SerialName("cpu_cap_pct") val cpuCapPct: Int? = null,
    @SerialName("ram_cap_mb") val ramCapMb: Int? = null,
    @SerialName("allow_kinds") val allowKinds: List<String>? = null,
    @SerialName("deny_kinds") val denyKinds: List<String>? = null,
    @SerialName("min_trust_score") val minTrustScore: Double? = null,
    @SerialName("offline_queue_max") val offlineQueueMax: Int? = null,
)

@Serializable
data class FleetSummaryResponse(
    val total: Int,
    val active: Int,
    val offline: Int,
    val quarantined: Int,
    val revoked: Int,
    @SerialName("avg_trust_score") val avgTrustScore: Double? = null,
    @SerialName("tasks_pending") val tasksPending: Int = 0,
    @SerialName("tasks_running") val tasksRunning: Int = 0,
    @SerialName("tasks_completed_24h") val tasksCompleted24h: Int = 0,
)

@Serializable
data class ModelRegisterRequest(
    val name: String,
    val version: String,
    val runtime: String = "ollama",
    val format: String = "gguf",
    val quantization: String? = null,
    @SerialName("size_mb") val sizeMb: Double? = null,
    @SerialName("min_ram_mb") val minRamMb: Double? = null,
    @SerialName("min_vram_mb") val minVramMb: Double? = null,
    val sha256: String? = null,
    @SerialName("source_url") val sourceUrl: String? = null,
)

@Serializable
data class ModelResponse(
    @SerialName("model_uid") val modelUid: String,
    val name: String,
    val version: String,
    val runtime: String,
    val format: String,
    val quantization: String? = null,
    @SerialName("size_mb") val sizeMb: Double? = null,
    val status: String,
    @SerialName("rollout_pct") val rolloutPct: Double = 0.0,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class ModelStatusUpdate(
    val status: String,
    @SerialName("rollout_pct") val rolloutPct: Double? = null,
)

@Serializable
data class ModelAssignRequest(
    @SerialName("device_id") val deviceId: String? = null,
    @SerialName("lab_id") val labId: Int? = null,
)

@Serializable
data class AgentHeartbeatRequest(
    @SerialName("device_id") val deviceId: String,
    @SerialName("uptime_s") val uptimeS: Int? = null,
    @SerialName("cpu_pct") val cpuPct: Double? = null,
    @SerialName("mem_mb") val memMb: Double? = null,
    @SerialName("battery_pct") val batteryPct: Double? = null,
    @SerialName("on_battery") val onBattery: Boolean? = null,
    @SerialName("queue_depth") val queueDepth: Int? = null,
    @SerialName("loaded_models") val loadedModels: List<String>? = null,
)

@Serializable
data class AgentHeartbeatResponse(
    val status: String,
    @SerialName("next_task") val nextTask: TaskResponse? = null,
    val config: Map<String, kotlinx.serialization.json.JsonElement>? = null,
)

@Serializable
data class TaskResultRequest(
    @SerialName("task_uid") val taskUid: String,
    val status: String,
    val result: Map<String, kotlinx.serialization.json.JsonElement>? = null,
    val error: String? = null,
)

@Serializable
data class AgentTelemetryRequest(
    @SerialName("device_id") val deviceId: String,
    @SerialName("cpu_pct") val cpuPct: Double? = null,
    @SerialName("mem_mb") val memMb: Double? = null,
    @SerialName("mem_total_mb") val memTotalMb: Double? = null,
    @SerialName("gpu_pct") val gpuPct: Double? = null,
    @SerialName("battery_pct") val batteryPct: Double? = null,
    @SerialName("on_battery") val onBattery: Boolean? = null,
    @SerialName("net_up_kbps") val netUpKbps: Double? = null,
    @SerialName("net_down_kbps") val netDownKbps: Double? = null,
    @SerialName("loaded_models") val loadedModels: List<String>? = null,
    @SerialName("queue_depth") val queueDepth: Int? = null,
)
