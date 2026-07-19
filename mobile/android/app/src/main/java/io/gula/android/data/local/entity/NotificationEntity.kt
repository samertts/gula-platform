package io.gula.android.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "notifications",
    indices = [
        Index(value = ["read"], unique = false),
        Index(value = ["created_at"], unique = false),
    ]
)
data class NotificationEntity(
    @PrimaryKey val id: Int,
    @ColumnInfo(name = "user_id") val userId: Int,
    @ColumnInfo(name = "title") val title: String,
    @ColumnInfo(name = "body") val body: String,
    @ColumnInfo(name = "type") val type: String = "info",
    @ColumnInfo(name = "read") val read: Boolean = false,
    @ColumnInfo(name = "data_json") val dataJson: String? = null,
    @ColumnInfo(name = "created_at") val createdAt: String? = null,
    @ColumnInfo(name = "synced_at") val syncedAt: Long? = null,
)
