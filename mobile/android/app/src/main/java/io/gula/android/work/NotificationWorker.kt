package io.gula.android.work

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.*
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.domain.repository.NotificationRepository
import io.gula.android.util.Constants
import io.gula.android.util.NetworkMonitor
import java.util.concurrent.TimeUnit

@HiltWorker
class NotificationWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val notificationRepository: NotificationRepository,
    private val networkMonitor: NetworkMonitor,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        if (!networkMonitor.isOnline.value) {
            return Result.retry()
        }
        return try {
            notificationRepository.refreshNotifications()
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    companion object {
        fun createPeriodicRequest(): PeriodicWorkRequest {
            return PeriodicWorkRequestBuilder<NotificationWorker>(
                Constants.PERIODIC_NOTIFICATION_INTERVAL_MINUTES,
                TimeUnit.MINUTES,
            )
                .setConstraints(
                    Constraints.Builder()
                        .setRequiredNetworkType(NetworkType.CONNECTED)
                        .build()
                )
                .addTag(Constants.NOTIFICATION_WORK_NAME)
                .build()
        }

        fun enqueue(context: Context) {
            val workManager = WorkManager.getInstance(context)
            workManager.enqueueUniquePeriodicWork(
                Constants.NOTIFICATION_WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                createPeriodicRequest(),
            )
        }
    }
}
