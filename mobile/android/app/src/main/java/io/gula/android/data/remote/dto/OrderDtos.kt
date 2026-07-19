package io.gula.android.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ResultItemDto(
    @Json(name = "test_name") val testName: String,
    @Json(name = "value") val value: Double? = null,
    @Json(name = "value_text") val valueText: String? = null,
    @Json(name = "unit") val unit: String? = null,
    @Json(name = "normal_range_low") val normalRangeLow: Double? = null,
    @Json(name = "normal_range_high") val normalRangeHigh: Double? = null,
)

@JsonClass(generateAdapter = true)
data class CreateOrderRequestDto(
    @Json(name = "patient_id") val patientId: Int,
    @Json(name = "doctor_name") val doctorName: String? = null,
    @Json(name = "doctor_user_id") val doctorUserId: Int? = null,
    @Json(name = "results") val results: List<ResultItemDto>,
)

@JsonClass(generateAdapter = true)
data class OrderResponseDto(
    @Json(name = "id") val id: Int,
    @Json(name = "patient_id") val patientId: Int,
    @Json(name = "patient_name") val patientName: String? = null,
    @Json(name = "lab_id") val labId: Int? = null,
    @Json(name = "doctor_name") val doctorName: String? = null,
    @Json(name = "doctor_user_id") val doctorUserId: Int? = null,
    @Json(name = "status") val status: String = "pending",
    @Json(name = "priority") val priority: String? = null,
    @Json(name = "version") val version: Int = 1,
    @Json(name = "visit_id") val visitId: Int? = null,
    @Json(name = "created_at") val createdAt: String? = null,
    @Json(name = "updated_at") val updatedAt: String? = null,
    @Json(name = "results") val results: List<ResultItemResponseDto>? = null,
)

@JsonClass(generateAdapter = true)
data class ResultItemResponseDto(
    @Json(name = "id") val id: Int,
    @Json(name = "order_id") val orderId: Int? = null,
    @Json(name = "test_name") val testName: String,
    @Json(name = "value") val value: Double? = null,
    @Json(name = "value_text") val valueText: String? = null,
    @Json(name = "unit") val unit: String? = null,
    @Json(name = "normal_range_low") val normalRangeLow: Double? = null,
    @Json(name = "normal_range_high") val normalRangeHigh: Double? = null,
    @Json(name = "status") val status: String? = null,
    @Json(name = "is_critical") val isCritical: Boolean = false,
    @Json(name = "is_abnormal") val isAbnormal: Boolean = false,
    @Json(name = "flag") val flag: String? = null,
    @Json(name = "version") val version: Int? = null,
    @Json(name = "created_at") val createdAt: String? = null,
)

@JsonClass(generateAdapter = true)
data class OrderListResponseDto(
    @Json(name = "items") val items: List<OrderResponseDto>,
    @Json(name = "total") val total: Int,
    @Json(name = "page") val page: Int = 1,
    @Json(name = "limit") val limit: Int = 20,
    @Json(name = "pages") val pages: Int = 1,
)

@JsonClass(generateAdapter = true)
data class BatchOrderItemDto(
    @Json(name = "patient_id") val patientId: Int,
    @Json(name = "doctor_name") val doctorName: String? = null,
    @Json(name = "results") val results: List<ResultItemDto>,
)

@JsonClass(generateAdapter = true)
data class BatchOrderRequestDto(
    @Json(name = "orders") val orders: List<BatchOrderItemDto>,
)

@JsonClass(generateAdapter = true)
data class BatchOrderResponseDto(
    @Json(name = "created") val created: Int,
    @Json(name = "failed") val failed: Int,
    @Json(name = "errors") val errors: List<String>? = null,
)

@JsonClass(generateAdapter = true)
data class AnalyzeRequestDto(
    @Json(name = "results") val results: List<ResultItemDto>,
)

@JsonClass(generateAdapter = true)
data class AnalyzeResponseDto(
    @Json(name = "patterns_detected") val patternsDetected: Int,
    @Json(name = "patterns") val patterns: List<ClinicalPatternDto>,
    @Json(name = "flag_summary") val flagSummary: FlagSummaryDto,
    @Json(name = "has_critical_pattern") val hasCriticalPattern: Boolean,
)

@JsonClass(generateAdapter = true)
data class ClinicalPatternDto(
    @Json(name = "pattern") val pattern: String,
    @Json(name = "severity") val severity: String,
    @Json(name = "description") val description: String? = null,
    @Json(name = "findings") val findings: List<String>? = null,
)

@JsonClass(generateAdapter = true)
data class FlagSummaryDto(
    @Json(name = "total") val total: Int,
    @Json(name = "high") val high: Int,
    @Json(name = "low") val low: Int,
    @Json(name = "critical") val critical: Int,
    @Json(name = "normal") val normal: Int,
)

@JsonClass(generateAdapter = true)
data class OrderIntelligenceResponseDto(
    @Json(name = "order_id") val orderId: Int,
    @Json(name = "patterns_detected") val patternsDetected: Int,
    @Json(name = "patterns") val patterns: List<ClinicalPatternDto>,
    @Json(name = "flag_summary") val flagSummary: FlagSummaryDto,
    @Json(name = "has_critical_pattern") val hasCriticalPattern: Boolean,
)
