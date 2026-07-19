package io.gula.android.util

object Constants {
    const val TAG = "GULA"
    const val DB_NAME = "gula_database"
    const val PREFS_NAME = "gula_preferences"
    const val SYNC_WORK_NAME = "sync_work"
    const val NOTIFICATION_WORK_NAME = "notification_work"
    const val CLEANUP_WORK_NAME = "cleanup_work"
    const val PERIODIC_SYNC_INTERVAL_MINUTES = 15L
    const val PERIODIC_NOTIFICATION_INTERVAL_MINUTES = 30L
    const val PERIODIC_CLEANUP_INTERVAL_HOURS = 24L
    const val SYNC_BATCH_SIZE = 50
    const val PAGE_SIZE = 20
    const val MAX_RETRIES = 3
    const val CONNECT_TIMEOUT_SECONDS = 15L
    const val READ_TIMEOUT_SECONDS = 30L
    const val WRITE_TIMEOUT_SECONDS = 30L
    const val MAX_CACHE_SIZE = 10 * 1024 * 1024L
    const val CACHE_TTL_SECONDS = 300
}
