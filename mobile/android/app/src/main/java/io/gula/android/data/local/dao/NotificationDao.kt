package io.gula.android.data.local.dao

import androidx.room.*
import io.gula.android.data.local.entity.NotificationEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface NotificationDao {
    @Query("SELECT * FROM notifications ORDER BY created_at DESC LIMIT :limit OFFSET :offset")
    fun getNotifications(limit: Int = 20, offset: Int = 0): Flow<List<NotificationEntity>>

    @Query("SELECT * FROM notifications WHERE id = :id")
    fun getNotificationById(id: Int): Flow<NotificationEntity?>

    @Query("SELECT COUNT(*) FROM notifications WHERE read = 0")
    fun getUnreadCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM notifications WHERE read = 0")
    suspend fun getUnreadCountOnce(): Int

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(notifications: List<NotificationEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(notification: NotificationEntity)

    @Query("UPDATE notifications SET read = 1 WHERE id = :id")
    suspend fun markAsRead(id: Int)

    @Query("UPDATE notifications SET read = 1")
    suspend fun markAllAsRead()

    @Delete
    suspend fun delete(notification: NotificationEntity)

    @Query("DELETE FROM notifications WHERE id = :id")
    suspend fun deleteById(id: Int)

    @Query("DELETE FROM notifications")
    suspend fun deleteAll()
}
