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
import io.gula.android.security.EncryptedPrefs
import net.zetetic.database.sqlcipher.SQLiteDatabase
import net.zetetic.database.sqlcipher.SupportOpenHelperFactory
import java.io.File
import java.nio.charset.StandardCharsets
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(
        @ApplicationContext context: Context,
        encryptedPrefs: EncryptedPrefs,
    ): GulaDatabase {
        System.loadLibrary("sqlcipher")
        val passphrase = encryptedPrefs.databaseEncryptionKey.toByteArray(StandardCharsets.UTF_8)
        migrateLegacyPlaintextDatabase(context, passphrase)

        return Room.databaseBuilder(
            context,
            GulaDatabase::class.java,
            GulaDatabase.DATABASE_NAME,
        )
            .openHelperFactory(SupportOpenHelperFactory(passphrase))
            .build()
    }

    private fun migrateLegacyPlaintextDatabase(context: Context, passphrase: ByteArray) {
        val databaseFile = context.getDatabasePath(GulaDatabase.DATABASE_NAME)
        if (!databaseFile.exists() || !looksLikePlaintextSqlite(databaseFile)) return

        val temporaryFile = File(databaseFile.parentFile, "${databaseFile.name}.encrypted.tmp")
        if (temporaryFile.exists() && !temporaryFile.delete()) {
            error("Unable to clear interrupted encrypted database migration")
        }

        val legacy = SQLiteDatabase.openOrCreateDatabase(databaseFile, "", null, null, null)
        try {
            val path = sqlLiteral(temporaryFile.absolutePath)
            val key = sqlLiteral(String(passphrase, StandardCharsets.UTF_8))
            legacy.rawExecSQL("ATTACH DATABASE '$path' AS encrypted KEY '$key'")
            legacy.rawExecSQL("SELECT sqlcipher_export('encrypted')")
            legacy.rawExecSQL("DETACH DATABASE encrypted")
        } finally {
            legacy.close()
        }

        val encrypted = SQLiteDatabase.openOrCreateDatabase(temporaryFile, String(passphrase, StandardCharsets.UTF_8), null, null, null)
        try {
            encrypted.rawQuery("PRAGMA cipher_integrity_check", null).use { cursor ->
                check(cursor.moveToFirst() && cursor.getString(0).equals("ok", ignoreCase = true)) {
                    "Encrypted Android database integrity check failed"
                }
            }
        } finally {
            encrypted.close()
        }

        check(databaseFile.delete()) { "Unable to replace plaintext Android database" }
        check(temporaryFile.renameTo(databaseFile)) { "Unable to finalize encrypted Android database" }
    }

    private fun looksLikePlaintextSqlite(file: File): Boolean {
        val header = ByteArray(SQLITE_HEADER.size)
        file.inputStream().use { input ->
            var offset = 0
            while (offset < header.size) {
                val read = input.read(header, offset, header.size - offset)
                if (read <= 0) return false
                offset += read
            }
        }
        return header.contentEquals(SQLITE_HEADER)
    }

    private fun sqlLiteral(value: String): String = value.replace("'", "''")

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

    private val SQLITE_HEADER = "SQLite format 3\u0000".toByteArray(StandardCharsets.US_ASCII)
}
