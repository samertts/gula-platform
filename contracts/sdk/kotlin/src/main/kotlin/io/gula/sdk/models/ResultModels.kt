package io.gula.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class TestResultRead(
    val id: Int,
    @SerialName("citizen_id") val citizenId: Int? = null,
    @SerialName("lab_id") val labId: Int? = null,
    @SerialName("device_id") val deviceId: Int? = null,
    @SerialName("test_code") val testCode: String,
    @SerialName("test_name_en") val testNameEn: String,
    @SerialName("test_name_ar") val testNameAr: String,
    val category: String? = null,
    @SerialName("result_value") val resultValue: Double? = null,
    @SerialName("result_text") val resultText: String? = null,
    val unit: String? = null,
    @SerialName("reference_min") val referenceMin: Double? = null,
    @SerialName("reference_max") val referenceMax: Double? = null,
    val status: String,
    @SerialName("is_critical") val isCritical: Boolean = false,
    @SerialName("is_abnormal") val isAbnormal: Boolean = false,
    @SerialName("abnormality_direction") val abnormalityDirection: String? = null,
    @SerialName("sample_collected_at") val sampleCollectedAt: String,
    @SerialName("result_completed_at") val resultCompletedAt: String? = null,
    @SerialName("verified_at") val verifiedAt: String? = null,
    @SerialName("verified_by") val verifiedBy: String? = null,
    @SerialName("sample_barcode") val sampleBarcode: String,
    @SerialName("ordering_physician") val orderingPhysician: String? = null,
    @SerialName("clinical_notes") val clinicalNotes: String? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("updated_at") val updatedAt: String,
)

@Serializable
data class TestResultBrief(
    val id: Int,
    @SerialName("test_code") val testCode: String,
    @SerialName("test_name_en") val testNameEn: String,
    @SerialName("test_name_ar") val testNameAr: String,
    @SerialName("result_value") val resultValue: Double? = null,
    @SerialName("result_text") val resultText: String? = null,
    val unit: String? = null,
    val status: String,
    @SerialName("is_abnormal") val isAbnormal: Boolean = false,
    @SerialName("is_critical") val isCritical: Boolean = false,
    @SerialName("sample_collected_at") val sampleCollectedAt: String,
)

@Serializable
data class TestResultValidateRequest(
    @SerialName("test_name") val testName: String,
    @SerialName("test_code") val testCode: String? = null,
    val value: Double? = null,
    val unit: String? = null,
    @SerialName("normal_range_low") val normalRangeLow: Double? = null,
    @SerialName("normal_range_high") val normalRangeHigh: Double? = null,
)

@Serializable
data class DeviceResult(
    @SerialName("test_name") val testName: String,
    val value: Double? = null,
    @SerialName("value_text") val valueText: String? = null,
    val unit: String? = null,
    @SerialName("normal_range_low") val normalRangeLow: Double? = null,
    @SerialName("normal_range_high") val normalRangeHigh: Double? = null,
)

@Serializable
data class DeviceSubmission(
    val barcode: String,
    @SerialName("device_id") val deviceId: String? = null,
    val results: List<DeviceResult>,
)

@Serializable
data class DeviceSubmissionResponse(
    val processed: Int,
    val failed: Int,
    val errors: List<String>? = null,
    @SerialName("order_id") val orderId: Int? = null,
)
