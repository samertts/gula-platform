package io.gula.android.di

import android.content.Context
import androidx.room.Room
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import io.gula.android.data.local.GulaDatabase
import io.gula.android.data.local.dao.*
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): GulaDatabase {
        return Room.databaseBuilder(
            context,
            GulaDatabase::class.java,
            GulaDatabase.DATABASE_NAME,
        )
            .fallbackToDestructiveMigration()
            .build()
    }

    @Provides
    fun providePatientDao(database: GulaDatabase): PatientDao = database.patientDao()

    @Provides
    fun provideOrderDao(database: GulaDatabase): OrderDao = database.orderDao()

    @Provides
    fun provideSampleDao(database: GulaDatabase): SampleDao = database.sampleDao()

    @Provides
    fun provideResultDao(database: GulaDatabase): ResultDao = database.resultDao()

    @Provides
    fun provideNotificationDao(database: GulaDatabase): NotificationDao = database.notificationDao()

    @Provides
    fun provideUserDao(database: GulaDatabase): UserDao = database.userDao()

    @Provides
    fun provideSyncQueueDao(database: GulaDatabase): SyncQueueDao = database.syncQueueDao()
}
