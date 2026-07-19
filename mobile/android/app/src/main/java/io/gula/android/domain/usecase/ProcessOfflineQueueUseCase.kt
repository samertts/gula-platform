package io.gula.android.domain.usecase

import io.gula.android.domain.model.SyncStatus
import io.gula.android.domain.repository.SyncRepository
import io.gula.android.util.NetworkMonitor
import javax.inject.Inject

class ProcessOfflineQueueUseCase @Inject constructor(
    private val syncRepository: SyncRepository,
    private val networkMonitor: NetworkMonitor,
) {
    suspend operator fun invoke(): SyncStatus {
        if (!networkMonitor.isOnline.value) {
            return SyncStatus(
                isSyncing = false,
                pendingCount = syncRepository.getPendingCount(),
                failedCount = syncRepository.getFailedCount(),
                errorMessage = "No internet connection. Items will sync when online."
            )
        }
        val status = syncRepository.processQueue()
        if (status.failedCount > 0) {
            syncRepository.retryFailed()
        }
        return status
    }
}
