package io.gula.android.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "orders",
    indices = [
        Index(value = ["patient_id"], unique = false),
        Index(value = ["status"], unique = false),
    ]
)
data class OrderEntity(
    @PrimaryKey val id: Int,
    @ColumnInfo(name = "patient_id") val patientId: Int,
    @ColumnInfo(name = "patient_name") val patientName: String? = null,
    @ColumnInfo(name = "lab_id") val labId: Int? = null,
    @ColumnInfo(name = "doctor_name") val doctorName: String? = null,
    @ColumnInfo(name = "doctor_user_id") val doctorUserId: Int? = null,
    @ColumnInfo(name = "status") val status: String = "pending",
    @ColumnInfo(name = "priority") val priority: String? = null,
    @ColumnInfo(name = "version") val version: Int = 1,
    @ColumnInfo(name = "visit_id") val visitId: Int? = null,
    @ColumnInfo(name = "created_at") val createdAt: String? = null,
    @ColumnInfo(name = "updated_at") val updatedAt: String? = null,
    @ColumnInfo(name = "synced_at") val syncedAt: Long? = null,
)
