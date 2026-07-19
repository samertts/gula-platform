package io.gula.android.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "results",
    indices = [
        Index(value = ["order_id"], unique = false),
        Index(value = ["status"], unique = false),
        Index(value = ["is_critical"], unique = false),
    ]
)
data class ResultEntity(
    @PrimaryKey val id: Int,
    @ColumnInfo(name = "order_id") val orderId: Int? = null,
    @ColumnInfo(name = "patient_id") val patientId: Int? = null,
    @ColumnInfo(name = "lab_id") val labId: Int? = null,
    @ColumnInfo(name = "test_code") val testCode: String,
    @ColumnInfo(name = "test_name_en") val testNameEn: String,
    @ColumnInfo(name = "test_name_ar") val testNameAr: String,
    @ColumnInfo(name = "category") val category: String? = null,
    @ColumnInfo(name = "result_value") val resultValue: Double? = null,
    @ColumnInfo(name = "result_text") val resultText: String? = null,
    @ColumnInfo(name = "unit") val unit: String? = null,
    @ColumnInfo(name = "reference_min") val referenceMin: Double? = null,
    @ColumnInfo(name = "reference_max") val referenceMax: Double? = null,
    @ColumnInfo(name = "status") val status: String = "pending",
    @ColumnInfo(name = "is_critical") val isCritical: Boolean = false,
    @ColumnInfo(name = "is_abnormal") val isAbnormal: Boolean = false,
    @ColumnInfo(name = "abnormality_direction") val abnormalityDirection: String? = null,
    @ColumnInfo(name = "sample_collected_at") val sampleCollectedAt: String? = null,
    @ColumnInfo(name = "result_completed_at") val resultCompletedAt: String? = null,
    @ColumnInfo(name = "verified_at") val verifiedAt: String? = null,
    @ColumnInfo(name = "verified_by") val verifiedBy: String? = null,
    @ColumnInfo(name = "sample_barcode") val sampleBarcode: String? = null,
    @ColumnInfo(name = "ordering_physician") val orderingPhysician: String? = null,
    @ColumnInfo(name = "clinical_notes") val clinicalNotes: String? = null,
    @ColumnInfo(name = "created_at") val createdAt: String? = null,
    @ColumnInfo(name = "updated_at") val updatedAt: String? = null,
    @ColumnInfo(name = "synced_at") val syncedAt: Long? = null,
)
