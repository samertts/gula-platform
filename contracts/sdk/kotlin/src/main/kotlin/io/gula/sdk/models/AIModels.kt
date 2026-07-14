package io.gula.sdk.models

import io.gula.sdk.AIFeedbackSignal
import io.gula.sdk.AIStatus
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class AISuggestRequest(
    val operation: String,
    val payload: Map<String, kotlinx.serialization.json.JsonElement>? = null,
    @SerialName("entity_type") val entityType: String? = null,
    @SerialName("entity_id") val entityId: Int? = null,
    val confidence: Double? = null,
    val rationale: String? = null,
)

@Serializable
data class AISuggestResponse(
    val id: String,
    val operation: String,
    val suggestion: Map<String, kotlinx.serialization.json.JsonElement>? = null,
    val confidence: Double? = null,
    val rationale: String? = null,
    val status: String = "pending",
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class AIPendingResponse(
    val total: Int,
    val suggestions: List<AISuggestResponse>,
)

@Serializable
data class AIApproveResponse(
    val message: String,
    @SerialName("suggestion_id") val suggestionId: String,
    val status: String,
)

@Serializable
data class AIRejectRequest(
    val reason: String? = null,
)

@Serializable
data class AIRejectResponse(
    val message: String,
    @SerialName("suggestion_id") val suggestionId: String,
    val status: String,
)

@Serializable
data class AIExecuteResponse(
    val message: String,
    @SerialName("suggestion_id") val suggestionId: String,
    val result: Map<String, kotlinx.serialization.json.JsonElement>? = null,
)

@Serializable
data class AIChatRequest(
    val message: String,
    val context: String? = null,
)

@Serializable
data class AIChatResponse(
    val reply: String,
    @SerialName("sources") val sources: List<String>? = null,
)

@Serializable
data class AIInterpretResponse(
    val interpretation: String,
    val disclaimer: String? = null,
)

@Serializable
data class AICriticalAlertResponse(
    @SerialName("alert_id") val alertId: Int,
    @SerialName("patient_name") val patientName: String,
    @SerialName("test_name") val testName: String,
    val value: Double? = null,
    @SerialName("value_text") val valueText: String? = null,
    val unit: String? = null,
    @SerialName("normal_range") val normalRange: String? = null,
    @SerialName("flagged_at") val flaggedAt: String,
    val acknowledged: Boolean = false,
)

@Serializable
data class AIInteraction(
    val id: String,
    @SerialName("lab_id") val labId: Int,
    @SerialName("anonymous_session_id") val anonymousSessionId: String,
    val language: String? = null,
    val intent: String? = null,
    val status: AIStatus = AIStatus.ok,
    @SerialName("confidence_score") val confidenceScore: Double? = null,
    @SerialName("risk_level") val riskLevel: String? = null,
    @SerialName("latency_ms") val latencyMs: Int? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class AIFeedback(
    val id: String,
    @SerialName("interaction_id") val interactionId: String,
    val signal: AIFeedbackSignal,
    val notes: String? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class AIFeedbackRequest(
    @SerialName("interaction_id") val interactionId: String,
    val signal: AIFeedbackSignal,
    val notes: String? = null,
)

@Serializable
data class AIUnresolvedQuestion(
    val id: String,
    @SerialName("lab_id") val labId: Int,
    val question: String,
    val language: String? = null,
    val status: String = "open",
    @SerialName("created_at") val createdAt: String,
)
