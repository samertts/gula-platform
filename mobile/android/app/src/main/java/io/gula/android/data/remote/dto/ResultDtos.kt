package io.gula.android.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class TestResultCreateDto(
    @Json(name = "order_id") val orderId: Int? = null,
    @Json(name = "patient_id") val patientId: Int? = null,
    @Json(name = "lab_id") val labId: Int? = null,
    @Json(name = "test_code") val testCode: String,
    @Json(name = "test_name_en") val testNameEn: String,
    @Json(name = "test_name_ar") val testNameAr: String,
    @Json(name = "category") val category: String? = null,
    @Json(name = "result_value") val resultValue: Double? = null,
    @Json(name = "result_text") val resultText: String? = null,
    @Json(name = "unit") val unit: String? = null,
    @Json(name = "reference_min") val referenceMin: Double? = null,
    @Json(name = "reference_max") val referenceMax: Double? = null,
    @Json(name = "status") val status: String = "pending",
    @Json(name = "is_critical") val isCritical: Boolean = false,
    @Json(name = "is_abnormal") val isAbnormal: Boolean = false,
    @Json(name = "abnormality_direction") val abnormalityDirection: String? = null,
    @Json(name = "sample_collected_at") val sampleCollectedAt: String? = null,
    @Json(name = "sample_barcode") val sampleBarcode: String? = null,
    @Json(name = "ordering_physician") val orderingPhysician: String? = null,
    @Json(name = "clinical_notes") val clinicalNotes: String? = null,
)

@JsonClass(generateAdapter = true)
data class TestResultResponseDto(
    @Json(name = "id") val id: Int,
    @Json(name = "order_id") val orderId: Int? = null,
    @Json(name = "patient_id") val patientId: Int? = null,
    @Json(name = "lab_id") val labId: Int? = null,
    @Json(name = "device_id") val deviceId: Int? = null,
    @Json(name = "test_code") val testCode: String,
    @Json(name = "test_name_en") val testNameEn: String,
    @Json(name = "test_name_ar") val testNameAr: String,
    @Json(name = "category") val category: String? = null,
    @Json(name = "result_value") val resultValue: Double? = null,
    @Json(name = "result_text") val resultText: String? = null,
    @Json(name = "unit") val unit: String? = null,
    @Json(name = "reference_min") val referenceMin: Double? = null,
    @Json(name = "reference_max") val referenceMax: Double? = null,
    @Json(name = "status") val status: String = "pending",
    @Json(name = "is_critical") val isCritical: Boolean = false,
    @Json(name = "is_abnormal") val isAbnormal: Boolean = false,
    @Json(name = "abnormality_direction") val abnormalityDirection: String? = null,
    @Json(name = "sample_collected_at") val sampleCollectedAt: String? = null,
    @Json(name = "result_completed_at") val resultCompletedAt: String? = null,
    @Json(name = "verified_at") val verifiedAt: String? = null,
    @Json(name = "verified_by") val verifiedBy: String? = null,
    @Json(name = "sample_barcode") val sampleBarcode: String? = null,
    @Json(name = "ordering_physician") val orderingPhysician: String? = null,
    @Json(name = "clinical_notes") val clinicalNotes: String? = null,
    @Json(name = "created_at") val createdAt: String? = null,
    @Json(name = "updated_at") val updatedAt: String? = null,
)

@JsonClass(generateAdapter = true)
data class ResultListResponseDto(
    @Json(name = "items") val items: List<TestResultResponseDto>,
    @Json(name = "total") val total: Int,
    @Json(name = "page") val page: Int = 1,
    @Json(name = "limit") val limit: Int = 20,
)

@JsonClass(generateAdapter = true)
data class CriticalAlertDto(
    @Json(name = "id") val id: Int,
    @Json(name = "lab_id") val labId: Int,
    @Json(name = "result_id") val resultId: Int? = null,
    @Json(name = "patient_name") val patientName: String,
    @Json(name = "test_name") val testName: String,
    @Json(name = "value") val value: String,
    @Json(name = "severity") val severity: String,
    @Json(name = "status") val status: String,
    @Json(name = "acknowledged_at") val acknowledgedAt: String? = null,
    @Json(name = "resolved_at") val resolvedAt: String? = null,
    @Json(name = "created_at") val createdAt: String,
)

@JsonClass(generateAdapter = true)
data class CriticalAlertListDto(
    @Json(name = "items") val items: List<CriticalAlertDto>,
    @Json(name = "total") val total: Int,
)

@JsonClass(generateAdapter = true)
data class ValidateResultRequestDto(
    @Json(name = "test_name") val testName: String,
    @Json(name = "test_code") val testCode: String? = null,
    @Json(name = "value") val value: Double? = null,
    @Json(name = "unit") val unit: String? = null,
    @Json(name = "normal_range_low") val normalRangeLow: Double? = null,
    @Json(name = "normal_range_high") val normalRangeHigh: Double? = null,
)
