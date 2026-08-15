package io.gula.android.data.local.dao

import androidx.room.*
import io.gula.android.data.local.entity.SyncQueueEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface SyncQueueDao {
    @Query("SELECT * FROM sync_queue WHERE status = 'PENDING' ORDER BY created_at ASC LIMIT :limit")
    suspend fun getPendingItems(limit: Int = 50): List<SyncQueueEntity>

    @Query("SELECT * FROM sync_queue WHERE status = 'FAILED' ORDER BY created_at ASC")
    suspend fun getFailedItems(): List<SyncQueueEntity>

    @Query("SELECT COUNT(*) FROM sync_queue WHERE status = 'PENDING'")
    fun getPendingCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM sync_queue WHERE status = 'PENDING'")
    suspend fun getPendingCountOnce(): Int

    @Query("SELECT COUNT(*) FROM sync_queue WHERE status = 'FAILED'")
    suspend fun getFailedCountOnce(): Int

    @Query("SELECT COUNT(*) FROM sync_queue WHERE status = 'DEFERRED'")
    suspend fun getDeferredCountOnce(): Int

    @Query("SELECT COUNT(*) FROM sync_queue WHERE status = 'IN_PROGRESS'")
    suspend fun getInProgressCount(): Int

    @Insert
    suspend fun insert(item: SyncQueueEntity): Long

    @Insert
    suspend fun insertAll(items: List<SyncQueueEntity>)

    @Update
    suspend fun update(item: SyncQueueEntity)

    @Query("UPDATE sync_queue SET status = :status, retry_count = retry_count + 1, last_error = :error WHERE id = :id")
    suspend fun markFailed(id: Long, status: String = "FAILED", error: String? = null)

    @Query("UPDATE sync_queue SET status = 'COMPLETED' WHERE id = :id")
    suspend fun markCompleted(id: Long)

    @Query("UPDATE sync_queue SET status = 'IN_PROGRESS' WHERE id = :id")
    suspend fun markInProgress(id: Long)

    @Query("UPDATE sync_queue SET status = 'PENDING', retry_count = 0, last_error = NULL WHERE status IN ('FAILED', 'DEFERRED') AND retry_count < max_retries")
    suspend fun retryFailed()

    @Query("UPDATE sync_queue SET status = 'DEFERRED', last_error = :error WHERE status = 'IN_PROGRESS'")
    suspend fun recoverInProgress(error: String = "Recovered after an interrupted sync")

    @Query("UPDATE sync_queue SET status = 'DEFERRED', last_error = :error WHERE id = :id")
    suspend fun markDeferred(id: Long, error: String? = null)

    @Query("UPDATE sync_queue SET payload = :payload WHERE id = :id")
    suspend fun updatePayload(id: Long, payload: String)

    @Query("DELETE FROM sync_queue WHERE status = 'COMPLETED'")
    suspend fun deleteCompleted()

    @Query("DELETE FROM sync_queue WHERE status = 'FAILED' AND retry_count >= max_retries")
    suspend fun deletePermanentlyFailed()

    @Query("DELETE FROM sync_queue")
    suspend fun deleteAll()

    @Query("SELECT * FROM sync_queue WHERE id = :id")
    suspend fun getById(id: Long): SyncQueueEntity?

    @Query("SELECT MAX(created_at) FROM sync_queue WHERE status = 'COMPLETED'")
    suspend fun getLastSyncTime(): Long?
}
