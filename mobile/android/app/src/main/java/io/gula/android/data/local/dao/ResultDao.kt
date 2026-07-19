package io.gula.android.data.local.dao

import androidx.room.*
import io.gula.android.data.local.entity.ResultEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ResultDao {
    @Query("SELECT * FROM results ORDER BY created_at DESC LIMIT :limit OFFSET :offset")
    fun getResults(limit: Int = 20, offset: Int = 0): Flow<List<ResultEntity>>

    @Query("SELECT * FROM results WHERE id = :id")
    fun getResultById(id: Int): Flow<ResultEntity?>

    @Query("SELECT * FROM results WHERE order_id = :orderId")
    fun getResultsByOrderId(orderId: Int): Flow<List<ResultEntity>>

    @Query("SELECT * FROM results WHERE is_critical = 1")
    fun getCriticalResults(): Flow<List<ResultEntity>>

    @Query("SELECT * FROM results WHERE status = :status")
    fun getResultsByStatus(status: String): Flow<List<ResultEntity>>

    @Query("SELECT COUNT(*) FROM results WHERE status = 'pending'")
    fun getPendingCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM results WHERE is_critical = 1 AND (verified_at IS NULL OR verified_at = '')")
    fun getUnresolvedCriticalCount(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(results: List<ResultEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(result: ResultEntity)

    @Update
    suspend fun update(result: ResultEntity)

    @Delete
    suspend fun delete(result: ResultEntity)

    @Query("DELETE FROM results WHERE id = :id")
    suspend fun deleteById(id: Int)

    @Query("DELETE FROM results")
    suspend fun deleteAll()

    @Query("UPDATE results SET synced_at = :syncedAt WHERE id = :id")
    suspend fun updateSyncStatus(id: Int, syncedAt: Long)
}
