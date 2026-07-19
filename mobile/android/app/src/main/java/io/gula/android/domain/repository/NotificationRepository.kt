package io.gula.android.domain.repository

import io.gula.android.domain.model.Notification
import io.gula.android.domain.model.NotificationPreferences
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow

interface NotificationRepository {
    fun getNotifications(page: Int = 1, limit: Int = 20): Flow<Resource<List<Notification>>>
    fun getUnreadCount(): Flow<Int>
    suspend fun markAsRead(id: Int): Resource<Unit>
    suspend fun markAllAsRead(): Resource<Unit>
    suspend fun deleteNotification(id: Int): Resource<Unit>
    suspend fun getPreferences(): Resource<NotificationPreferences>
    suspend fun updatePreferences(prefs: NotificationPreferences): Resource<Unit>
    suspend fun refreshNotifications()
}
