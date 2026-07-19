package io.gula.android.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import io.gula.android.data.local.dao.*
import io.gula.android.data.local.entity.*
import io.gula.android.util.DateConverters

@Database(
    entities = [
        PatientEntity::class,
        OrderEntity::class,
        SampleEntity::class,
        ResultEntity::class,
        NotificationEntity::class,
        UserEntity::class,
        SyncQueueEntity::class,
    ],
    version = 1,
    exportSchema = true,
)
@TypeConverters(DateConverters::class)
abstract class GulaDatabase : RoomDatabase() {
    abstract fun patientDao(): PatientDao
    abstract fun orderDao(): OrderDao
    abstract fun sampleDao(): SampleDao
    abstract fun resultDao(): ResultDao
    abstract fun notificationDao(): NotificationDao
    abstract fun userDao(): UserDao
    abstract fun syncQueueDao(): SyncQueueDao

    companion object {
        const val DATABASE_NAME = "gula_database"
    }
}
