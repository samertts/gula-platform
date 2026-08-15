package io.gula.android.work

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.*
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import io.gula.android.domain.repository.SyncRepository
import io.gula.android.util.Constants
import io.gula.android.util.NetworkMonitor
import java.util.concurrent.TimeUnit

@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val syncRepository: SyncRepository,
    private val networkMonitor: NetworkMonitor,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        if (!networkMonitor.isOnline.value) {
            return Result.retry()
        }
        return try {
            val status = syncRepository.processQueue()
            if (status.errorMessage != null || status.deferredCount > 0 || status.pendingCount > 0) {
                Result.retry()
            } else {
                Result.success()
            }
        } catch (e: Exception) {
            if (runAttemptCount < 3) Result.retry() else Result.failure()
        }
    }

    companion object {
        fun createPeriodicSyncRequest(): PeriodicWorkRequest {
            return PeriodicWorkRequestBuilder<SyncWorker>(
                Constants.PERIODIC_SYNC_INTERVAL_MINUTES,
                TimeUnit.MINUTES,
            )
                .setConstraints(
                    Constraints.Builder()
                        .setRequiredNetworkType(NetworkType.CONNECTED)
                        .build()
                )
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    1,
                    TimeUnit.MINUTES,
                )
                .addTag(Constants.SYNC_WORK_NAME)
                .build()
        }

        fun enqueue(context: Context) {
            val workManager = WorkManager.getInstance(context)
            val request = createPeriodicSyncRequest()
            workManager.enqueueUniquePeriodicWork(
                Constants.SYNC_WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                request,
            )
        }
    }
}
