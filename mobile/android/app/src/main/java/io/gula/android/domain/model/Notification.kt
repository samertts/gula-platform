package io.gula.android.domain.model

data class Notification(
    val id: Int,
    val userId: Int,
    val title: String,
    val body: String,
    val type: String = "info",
    val read: Boolean = false,
    val dataJson: String? = null,
    val createdAt: String? = null,
)

data class NotificationPreferences(
    val email: Boolean = true,
    val sms: Boolean = false,
    val push: Boolean = true,
    val whatsapp: Boolean = false,
)
