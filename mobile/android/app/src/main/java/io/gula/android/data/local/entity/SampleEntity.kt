package io.gula.android.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "samples",
    indices = [
        Index(value = ["barcode"], unique = true),
        Index(value = ["order_id"], unique = false),
        Index(value = ["status"], unique = false),
    ]
)
data class SampleEntity(
    @PrimaryKey val id: Int,
    @ColumnInfo(name = "barcode") val barcode: String,
    @ColumnInfo(name = "order_id") val orderId: Int,
    @ColumnInfo(name = "sample_type") val sampleType: String,
    @ColumnInfo(name = "status") val status: String = "collected",
    @ColumnInfo(name = "collected_by") val collectedBy: String? = null,
    @ColumnInfo(name = "collection_time") val collectionTime: String? = null,
    @ColumnInfo(name = "rejection_reason") val rejectionReason: String? = null,
    @ColumnInfo(name = "notes") val notes: String? = null,
    @ColumnInfo(name = "storage_location") val storageLocation: String? = null,
    @ColumnInfo(name = "created_at") val createdAt: String? = null,
    @ColumnInfo(name = "updated_at") val updatedAt: String? = null,
    @ColumnInfo(name = "synced_at") val syncedAt: Long? = null,
)
