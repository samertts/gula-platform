package io.gula.android.domain.model

data class TestResult(
    val id: Int,
    val testCode: String,
    val testNameEn: String,
    val testNameAr: String,
    val category: String? = null,
    val resultValue: Double? = null,
    val resultText: String? = null,
    val unit: String? = null,
    val referenceMin: Double? = null,
    val referenceMax: Double? = null,
    val status: String = "pending",
    val isCritical: Boolean = false,
    val isAbnormal: Boolean = false,
    val abnormalityDirection: String? = null,
    val sampleCollectedAt: String,
    val resultCompletedAt: String? = null,
    val verifiedAt: String? = null,
    val verifiedBy: String? = null,
    val sampleBarcode: String? = null,
    val orderingPhysician: String? = null,
    val clinicalNotes: String? = null,
    val patientId: Int? = null,
    val labId: Int? = null,
    val orderId: Int? = null,
    val createdAt: String? = null,
    val updatedAt: String? = null,
)

data class TestResultBrief(
    val id: Int,
    val testCode: String,
    val testNameEn: String,
    val testNameAr: String,
    val resultValue: Double? = null,
    val resultText: String? = null,
    val unit: String? = null,
    val status: String,
    val isAbnormal: Boolean = false,
    val isCritical: Boolean = false,
    val sampleCollectedAt: String,
)

data class ResultValidation(
    val testName: String,
    val testCode: String? = null,
    val value: Double? = null,
    val unit: String? = null,
    val normalRangeLow: Double? = null,
    val normalRangeHigh: Double? = null,
)

data class CriticalAlert(
    val id: Int,
    val labId: Int,
    val resultId: Int? = null,
    val patientName: String,
    val testName: String,
    val value: String,
    val severity: String,
    val status: String,
    val acknowledgedAt: String? = null,
    val resolvedAt: String? = null,
    val createdAt: String,
)
