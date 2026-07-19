package io.gula.android.domain.usecase

import io.gula.android.domain.model.SyncStatus
import io.gula.android.domain.repository.SyncRepository
import io.gula.android.util.NetworkMonitor
import javax.inject.Inject

class SyncDataUseCase @Inject constructor(
    private val syncRepository: SyncRepository,
    private val networkMonitor: NetworkMonitor,
) {
    suspend operator fun invoke(): SyncStatus {
        if (!networkMonitor.isOnline.value) {
            return SyncStatus(
                isSyncing = false,
                errorMessage = "No internet connection"
            )
        }
        return syncRepository.processQueue()
    }
}
