package io.gula.android.domain.model

data class Order(
    val id: Int,
    val patientId: Int,
    val patientName: String? = null,
    val labId: Int? = null,
    val doctorName: String? = null,
    val doctorUserId: Int? = null,
    val status: String = "pending",
    val priority: String? = null,
    val version: Int = 1,
    val visitId: Int? = null,
    val createdAt: String? = null,
    val updatedAt: String? = null,
    val results: List<ResultItem> = emptyList(),
)

data class ResultItem(
    val id: Int? = null,
    val testName: String,
    val value: Double? = null,
    val valueText: String? = null,
    val unit: String? = null,
    val normalRangeLow: Double? = null,
    val normalRangeHigh: Double? = null,
    val status: String? = null,
    val isCritical: Boolean = false,
    val isAbnormal: Boolean = false,
    val flag: String? = null,
    val createdAt: String? = null,
)

data class CreateOrderRequest(
    val patientId: Int,
    val doctorName: String? = null,
    val doctorUserId: Int? = null,
    val results: List<ResultItemInput>,
)

data class ResultItemInput(
    val testName: String,
    val value: Double? = null,
    val valueText: String? = null,
    val unit: String? = null,
    val normalRangeLow: Double? = null,
    val normalRangeHigh: Double? = null,
)

data class BatchOrderRequest(
    val orders: List<BatchOrderItem>,
)

data class BatchOrderItem(
    val patientId: Int,
    val doctorName: String? = null,
    val results: List<ResultItemInput>,
)

data class BatchOrderResult(
    val created: Int,
    val failed: Int,
    val errors: List<String>? = null,
)

data class OrderIntelligence(
    val orderId: Int,
    val patternsDetected: Int,
    val patterns: List<ClinicalPattern>,
    val flagSummary: FlagSummary,
    val hasCriticalPattern: Boolean,
)

data class ClinicalPattern(
    val pattern: String,
    val severity: String,
    val description: String? = null,
    val findings: List<String>? = null,
)

data class FlagSummary(
    val total: Int,
    val high: Int,
    val low: Int,
    val critical: Int,
    val normal: Int,
)
