package io.gula.android.data.local.dao

import androidx.room.*
import io.gula.android.data.local.entity.SampleEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface SampleDao {
    @Query("""
        SELECT * FROM samples 
        WHERE (:status IS NULL OR status = :status)
        ORDER BY created_at DESC 
        LIMIT :limit OFFSET :offset
    """)
    fun getSamples(status: String? = null, limit: Int = 20, offset: Int = 0): Flow<List<SampleEntity>>

    @Query("SELECT * FROM samples WHERE barcode = :barcode")
    fun getSampleByBarcode(barcode: String): Flow<SampleEntity?>

    @Query("SELECT * FROM samples WHERE order_id = :orderId")
    fun getSamplesByOrderId(orderId: Int): Flow<List<SampleEntity>>

    @Query("SELECT * FROM samples WHERE status = :status")
    fun getSamplesByStatus(status: String): Flow<List<SampleEntity>>

    @Query("SELECT COUNT(*) FROM samples WHERE status = 'collected'")
    fun getCollectedCount(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(samples: List<SampleEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(sample: SampleEntity)

    @Update
    suspend fun update(sample: SampleEntity)

    @Delete
    suspend fun delete(sample: SampleEntity)

    @Query("DELETE FROM samples WHERE barcode = :barcode")
    suspend fun deleteByBarcode(barcode: String)

    @Query("DELETE FROM samples")
    suspend fun deleteAll()

    @Query("UPDATE samples SET synced_at = :syncedAt WHERE barcode = :barcode")
    suspend fun updateSyncStatus(barcode: String, syncedAt: Long)
}
