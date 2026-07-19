package io.gula.android.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "sync_queue",
    indices = [
        Index(value = ["status"], unique = false),
        Index(value = ["entity_type"], unique = false),
    ]
)
data class SyncQueueEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "entity_type") val entityType: String,
    @ColumnInfo(name = "entity_id") val entityId: String? = null,
    @ColumnInfo(name = "action") val action: String,
    @ColumnInfo(name = "payload") val payload: String,
    @ColumnInfo(name = "created_at") val createdAt: Long = System.currentTimeMillis(),
    @ColumnInfo(name = "retry_count") val retryCount: Int = 0,
    @ColumnInfo(name = "max_retries") val maxRetries: Int = 3,
    @ColumnInfo(name = "last_error") val lastError: String? = null,
    @ColumnInfo(name = "status") val status: String = "PENDING",
)
