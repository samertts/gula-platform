package io.gula.android.domain.model

data class SyncStatus(
    val isSyncing: Boolean = false,
    val lastSyncTime: String? = null,
    val pendingCount: Int = 0,
    val failedCount: Int = 0,
    val deferredCount: Int = 0,
    val errorMessage: String? = null,
)

enum class SyncAction {
    CREATE_PATIENT,
    UPDATE_PATIENT,
    CREATE_ORDER,
    UPDATE_ORDER,
    CREATE_SAMPLE,
    UPDATE_SAMPLE,
    CREATE_RESULT,
    UPDATE_RESULT,
}

data class SyncQueueItem(
    val id: Long = 0,
    val entityType: String,
    val entityId: String? = null,
    val action: SyncAction,
    val payload: String,
    val createdAt: Long = System.currentTimeMillis(),
    val retryCount: Int = 0,
    val maxRetries: Int = 3,
    val lastError: String? = null,
    val status: SyncItemStatus = SyncItemStatus.PENDING,
)

enum class SyncItemStatus {
    PENDING,
    IN_PROGRESS,
    COMPLETED,
    FAILED,
    DEFERRED,
}

data class DashboardStats(
    val patientsCount: Int = 0,
    val ordersToday: Int = 0,
    val pendingResults: Int = 0,
    val criticalAlerts: Int = 0,
    val samplesToday: Int = 0,
    val revenueToday: Double? = null,
    val pendingOrders: Int = 0,
    val completedOrders: Int = 0,
    val collectedSamples: Int = 0,
    val processingSamples: Int = 0,
    val unreadNotifications: Int = 0,
)
