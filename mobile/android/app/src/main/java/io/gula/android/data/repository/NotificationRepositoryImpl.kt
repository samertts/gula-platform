package io.gula.android.data.repository

import io.gula.android.data.local.dao.NotificationDao
import io.gula.android.data.local.entity.NotificationEntity
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.NotificationPreferencesDto
import io.gula.android.data.remote.dto.NotificationResponseDto
import io.gula.android.domain.model.Notification
import io.gula.android.domain.model.NotificationPreferences
import io.gula.android.domain.repository.NotificationRepository
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NotificationRepositoryImpl @Inject constructor(
    private val notificationDao: NotificationDao,
    private val gulaApi: GulaApi,
) : NotificationRepository {

    override fun getNotifications(page: Int, limit: Int): Flow<Resource<List<Notification>>> {
        return notificationDao.getNotifications(limit, (page - 1) * limit).map { entities ->
            Resource.success(entities.map { it.toDomain() })
        }
    }

    override fun getUnreadCount(): Flow<Int> = notificationDao.getUnreadCount()

    override suspend fun markAsRead(id: Int): Resource<Unit> {
        return try {
            val response = gulaApi.markNotificationRead(id)
            if (response.isSuccessful) {
                notificationDao.markAsRead(id)
                Resource.success(Unit)
            } else {
                Resource.error("Failed to mark notification as read")
            }
        } catch (e: Exception) {
            notificationDao.markAsRead(id)
            Resource.success(Unit)
        }
    }

    override suspend fun markAllAsRead(): Resource<Unit> {
        return try {
            val response = gulaApi.markAllNotificationsRead()
            if (response.isSuccessful || true) {
                notificationDao.markAllAsRead()
                Resource.success(Unit)
            } else {
                Resource.error("Failed to mark notifications as read")
            }
        } catch (e: Exception) {
            notificationDao.markAllAsRead()
            Resource.success(Unit)
        }
    }

    override suspend fun deleteNotification(id: Int): Resource<Unit> {
        return try {
            val response = gulaApi.deleteNotification(id)
            if (response.isSuccessful) {
                notificationDao.deleteById(id)
                Resource.success(Unit)
            } else {
                Resource.error("Failed to delete notification")
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun getPreferences(): Resource<NotificationPreferences> {
        return try {
            val response = gulaApi.getNotificationPreferences()
            if (response.isSuccessful) {
                val dto = response.body()!!
                Resource.success(dto.toDomain())
            } else {
                Resource.success(NotificationPreferences())
            }
        } catch (e: Exception) {
            Resource.success(NotificationPreferences())
        }
    }

    override suspend fun updatePreferences(prefs: NotificationPreferences): Resource<Unit> {
        return try {
            val response = gulaApi.updateNotificationPreferences(
                NotificationPreferencesDto(
                    email = prefs.email,
                    sms = prefs.sms,
                    push = prefs.push,
                    whatsapp = prefs.whatsapp,
                )
            )
            if (response.isSuccessful) Resource.success(Unit)
            else Resource.error("Failed to update preferences")
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun refreshNotifications() {
        try {
            val response = gulaApi.getNotifications(limit = 50)
            if (response.isSuccessful) {
                notificationDao.insertAll(
                    response.body()!!.items.map { it.toDomain().toEntity() }
                )
            }
        } catch (_: Exception) { }
    }
}

private fun NotificationResponseDto.toDomain() = Notification(
    id = id,
    userId = userId,
    title = title,
    body = body,
    type = type,
    read = read,
    dataJson = dataJson,
    createdAt = createdAt,
)

private fun Notification.toEntity() = NotificationEntity(
    id = id,
    userId = userId,
    title = title,
    body = body,
    type = type,
    read = read,
    dataJson = dataJson,
    createdAt = createdAt,
)

private fun NotificationEntity.toDomain() = Notification(
    id = id,
    userId = userId,
    title = title,
    body = body,
    type = type,
    read = read,
    dataJson = dataJson,
    createdAt = createdAt,
)

private fun NotificationPreferencesDto.toDomain() = NotificationPreferences(
    email = email,
    sms = sms,
    push = push,
    whatsapp = whatsapp,
)
