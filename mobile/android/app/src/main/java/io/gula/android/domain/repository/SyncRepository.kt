package io.gula.android.domain.repository

import io.gula.android.domain.model.SyncAction
import io.gula.android.domain.model.SyncStatus
import kotlinx.coroutines.flow.Flow

interface SyncRepository {
    val syncStatus: Flow<SyncStatus>

    suspend fun enqueue(entityType: String, entityId: String?, action: SyncAction, payload: String)
    suspend fun processQueue(): SyncStatus
    suspend fun getPendingCount(): Int
    suspend fun getFailedCount(): Int
    suspend fun retryFailed()
    suspend fun clearCompleted()
    suspend fun getLastSyncTime(): String?
}
