package io.gula.android.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class NotificationResponseDto(
    @Json(name = "id") val id: Int,
    @Json(name = "user_id") val userId: Int,
    @Json(name = "title") val title: String,
    @Json(name = "body") val body: String,
    @Json(name = "type") val type: String = "info",
    @Json(name = "read") val read: Boolean = false,
    @Json(name = "data_json") val dataJson: String? = null,
    @Json(name = "created_at") val createdAt: String? = null,
)

@JsonClass(generateAdapter = true)
data class NotificationListResponseDto(
    @Json(name = "items") val items: List<NotificationResponseDto>,
    @Json(name = "total") val total: Int,
    @Json(name = "page") val page: Int = 1,
    @Json(name = "limit") val limit: Int = 20,
)

@JsonClass(generateAdapter = true)
data class NotificationPreferencesDto(
    @Json(name = "email") val email: Boolean = true,
    @Json(name = "sms") val sms: Boolean = false,
    @Json(name = "push") val push: Boolean = true,
    @Json(name = "whatsapp") val whatsapp: Boolean = false,
)

@JsonClass(generateAdapter = true)
data class DashboardStatsDto(
    @Json(name = "patients_count") val patientsCount: Int = 0,
    @Json(name = "orders_today") val ordersToday: Int = 0,
    @Json(name = "pending_results") val pendingResults: Int = 0,
    @Json(name = "critical_alerts") val criticalAlerts: Int = 0,
    @Json(name = "samples_today") val samplesToday: Int = 0,
    @Json(name = "revenue_today") val revenueToday: Double? = null,
)
