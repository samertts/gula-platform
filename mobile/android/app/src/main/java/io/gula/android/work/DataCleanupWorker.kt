package io.gula.android.work

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.*
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import io.gula.android.data.local.GulaDatabase
import io.gula.android.domain.repository.SyncRepository
import io.gula.android.util.Constants
import java.util.concurrent.TimeUnit

@HiltWorker
class DataCleanupWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val database: GulaDatabase,
    private val syncRepository: SyncRepository,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            syncRepository.clearCompleted()

            val thirtyDaysAgo = System.currentTimeMillis() - (30L * 24 * 60 * 60 * 1000)
            val notifications = database.notificationDao().getNotifications(limit = 1000, offset = 0)

            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    companion object {
        fun createPeriodicRequest(): PeriodicWorkRequest {
            return PeriodicWorkRequestBuilder<DataCleanupWorker>(
                Constants.PERIODIC_CLEANUP_INTERVAL_HOURS,
                TimeUnit.HOURS,
            )
                .addTag(Constants.CLEANUP_WORK_NAME)
                .build()
        }

        fun enqueue(context: Context) {
            val workManager = WorkManager.getInstance(context)
            workManager.enqueueUniquePeriodicWork(
                Constants.CLEANUP_WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                createPeriodicRequest(),
            )
        }
    }
}
