package io.gula.android.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "patients",
    indices = [
        Index(value = ["full_name"], unique = false),
        Index(value = ["phone"], unique = false),
        Index(value = ["national_id"], unique = false),
    ]
)
data class PatientEntity(
    @PrimaryKey val id: Int,
    @ColumnInfo(name = "full_name") val fullName: String,
    @ColumnInfo(name = "phone") val phone: String,
    @ColumnInfo(name = "birth_date") val birthDate: String? = null,
    @ColumnInfo(name = "gender") val gender: String? = null,
    @ColumnInfo(name = "email") val email: String? = null,
    @ColumnInfo(name = "lab_id") val labId: Int? = null,
    @ColumnInfo(name = "national_id") val nationalId: String? = null,
    @ColumnInfo(name = "health_id") val healthId: String? = null,
    @ColumnInfo(name = "family_id") val familyId: String? = null,
    @ColumnInfo(name = "guardian_id") val guardianId: Int? = null,
    @ColumnInfo(name = "status") val status: String? = null,
    @ColumnInfo(name = "created_at") val createdAt: String? = null,
    @ColumnInfo(name = "updated_at") val updatedAt: String? = null,
    @ColumnInfo(name = "synced_at") val syncedAt: Long? = null,
)
