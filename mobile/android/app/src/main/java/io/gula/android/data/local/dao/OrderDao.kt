package io.gula.android.data.local.dao

import androidx.room.*
import io.gula.android.data.local.entity.OrderEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface OrderDao {
    @Query("""
        SELECT * FROM orders 
        WHERE (:search IS NULL OR patient_name LIKE '%' || :search || '%' OR doctor_name LIKE '%' || :search || '%')
        ORDER BY created_at DESC 
        LIMIT :limit OFFSET :offset
    """)
    fun getOrders(search: String? = null, limit: Int = 20, offset: Int = 0): Flow<List<OrderEntity>>

    @Query("SELECT * FROM orders WHERE id = :id")
    fun getOrderById(id: Int): Flow<OrderEntity?>

    @Query("SELECT * FROM orders WHERE patient_id = :patientId ORDER BY created_at DESC")
    fun getOrdersByPatientId(patientId: Int): Flow<List<OrderEntity>>

    @Query("SELECT * FROM orders WHERE status = :status ORDER BY created_at DESC")
    fun getOrdersByStatus(status: String): Flow<List<OrderEntity>>

    @Query("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
    fun getPendingCount(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(orders: List<OrderEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(order: OrderEntity)

    @Update
    suspend fun update(order: OrderEntity)

    @Delete
    suspend fun delete(order: OrderEntity)

    @Query("DELETE FROM orders WHERE id = :id")
    suspend fun deleteById(id: Int)

    @Query("DELETE FROM orders")
    suspend fun deleteAll()

    @Query("UPDATE orders SET synced_at = :syncedAt WHERE id = :id")
    suspend fun updateSyncStatus(id: Int, syncedAt: Long)
}
