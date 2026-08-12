package io.gula.sdk.models

import io.gula.sdk.OrderStatus
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ResultItem(
    @SerialName("test_name") val testName: String,
    val value: Double? = null,
    @SerialName("value_text") val valueText: String? = null,
    val unit: String? = null,
    @SerialName("normal_range_low") val normalRangeLow: Double? = null,
    @SerialName("normal_range_high") val normalRangeHigh: Double? = null,
)

@Serializable
data class CreateOrderRequest(
    @SerialName("patient_id") val patientId: Int,
    @SerialName("doctor_name") val doctorName: String? = null,
    @SerialName("doctor_user_id") val doctorUserId: Int? = null,
    val results: List<ResultItem>,
)

@Serializable
data class OrderResponse(
    val id: Int,
    @SerialName("patient_id") val patientId: Int,
    @SerialName("lab_id") val labId: Int,
    @SerialName("patient_name") val patientName: String? = null,
    @SerialName("doctor_name") val doctorName: String? = null,
    val status: OrderStatus,
    val version: Int? = null,
    @SerialName("created_at") val createdAt: String? = null,
    val results: List<ResultResponse>? = null,
)

@Serializable
data class ResultResponse(
    val id: Int,
    @SerialName("test_name") val testName: String,
    val value: Double? = null,
    @SerialName("value_text") val valueText: String? = null,
    val unit: String? = null,
    @SerialName("normal_range_low") val normalRangeLow: Double? = null,
    @SerialName("normal_range_high") val normalRangeHigh: Double? = null,
    val flag: String? = null,
    val token: String? = null,
    val version: Int? = null,
    @SerialName("created_at") val createdAt: String? = null,
)

@Serializable
data class OrderListResponse(
    val total: Int,
    val orders: List<OrderResponse>,
)

@Serializable
data class ValidateOrderResponse(
    val message: String,
    @SerialName("order_id") val orderId: Int,
    val status: OrderStatus,
)

@Serializable
data class OrderIntelligenceResponse(
    @SerialName("order_id") val orderId: Int,
    @SerialName("patterns_detected") val patternsDetected: Int,
    val patterns: List<ClinicalPattern>,
    @SerialName("flag_summary") val flagSummary: FlagSummary,
    @SerialName("has_critical_pattern") val hasCriticalPattern: Boolean,
)

@Serializable
data class ClinicalPattern(
    val pattern: String,
    val severity: String,
    val description: String? = null,
    val findings: List<String>? = null,
)

@Serializable
data class FlagSummary(
    val total: Int,
    val high: Int,
    val low: Int,
    val critical: Int,
    val normal: Int,
)

@Serializable
data class AnalyzeRequest(
    val results: List<ResultItem>,
)

@Serializable
data class AnalyzeResponse(
    @SerialName("patterns_detected") val patternsDetected: Int,
    val patterns: List<ClinicalPattern>,
    @SerialName("flag_summary") val flagSummary: FlagSummary,
    @SerialName("has_critical_pattern") val hasCriticalPattern: Boolean,
)

@Serializable
data class BatchResultItem(
    @SerialName("test_name") val testName: String,
    val value: Double? = null,
    @SerialName("value_text") val valueText: String? = null,
    val unit: String? = null,
    @SerialName("normal_range_low") val normalRangeLow: Double? = null,
    @SerialName("normal_range_high") val normalRangeHigh: Double? = null,
)

@Serializable
data class BatchOrderItem(
    @SerialName("patient_id") val patientId: Int,
    @SerialName("doctor_name") val doctorName: String? = null,
    val results: List<BatchResultItem>,
)

@Serializable
data class BatchOrderRequest(
    val orders: List<BatchOrderItem>,
)

@Serializable
data class BatchOrderResponse(
    val created: Int,
    val failed: Int,
    val errors: List<BatchOrderError>? = null,
)

@Serializable
data class BatchOrderError(
    val index: Int,
    val error: String,
    @SerialName("patient_id") val patientId: Int? = null,
)

@Serializable
data class PublicResultResponse(
    val order: OrderResponse,
    val patient: PatientBriefResponse,
)

@Serializable
data class PatientBriefResponse(
    @SerialName("full_name") val fullName: String,
    val phone: String? = null,
)

@Serializable
data class HomeTestResultCreate(
    @SerialName("health_id") val healthId: String,
    @SerialName("test_name") val testName: String,
    @SerialName("test_code") val testCode: String? = null,
    val value: Double? = null,
    @SerialName("value_text") val valueText: String? = null,
    val unit: String? = null,
    @SerialName("normal_range_low") val normalRangeLow: Double? = null,
    @SerialName("normal_range_high") val normalRangeHigh: Double? = null,
    @SerialName("sample_type") val sampleType: String? = null,
    @SerialName("doctor_name") val doctorName: String? = null,
    @SerialName("order_id") val orderId: Int? = null,
)

@Serializable
data class TestProfile(
    @SerialName("test_name") val testName: String,
    val unit: String? = null,
    @SerialName("normal_range_low") val normalRangeLow: Double? = null,
    @SerialName("normal_range_high") val normalRangeHigh: Double? = null,
)
