package io.gula.android.data.local

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import io.gula.android.data.local.dao.PatientDao
import io.gula.android.data.local.dao.SyncQueueDao
import io.gula.android.data.local.entity.PatientEntity
import io.gula.android.data.local.entity.SyncQueueEntity
import io.gula.android.domain.model.SyncAction
import io.gula.android.domain.model.SyncEntityType
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

@RunWith(AndroidJUnit4::class)
class SyncIntegrationTest {

    private lateinit var database: GulaDatabase
    private lateinit var patientDao: PatientDao
    private lateinit var syncQueueDao: SyncQueueDao

    @Before
    fun setup() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(
            context,
            GulaDatabase::class.java
        ).allowMainThreadQueries().build()

        patientDao = database.patientDao()
        syncQueueDao = database.syncQueueDao()
    }

    @After
    fun teardown() {
        database.close()
    }

    @Test
    fun databaseStoresEntityWithForeignKeys() = runBlocking {
        val patient = PatientEntity(
            id = "p-1",
            fullName = "Sync Patient",
            phone = "07701234567",
            birthDate = "1985-03-15",
            gender = "male",
            createdAt = "2024-01-01T00:00:00Z",
            updatedAt = "2024-01-01T00:00:00Z"
        )

        patientDao.insertPatient(patient)

        val retrieved = patientDao.getPatientById("p-1")
        assertNotNull(retrieved)
        assertEquals("Sync Patient", retrieved.fullName)
    }

    @Test
    fun syncQueueStoresAndRetrievesPendingItems() = runBlocking {
        val queueItem = SyncQueueEntity(
            entityType = SyncEntityType.PATIENT.name,
            action = SyncAction.CREATE.name,
            entityId = "p-queue-1",
            payload = """{"fullName":"Queued Patient","phone":"07701234567"}""",
            retryCount = 0,
            maxRetries = 3,
            createdAt = System.currentTimeMillis()
        )

        val id = syncQueueDao.insert(queueItem)
        assertTrue(id > 0)

        val pendingItems = syncQueueDao.getPendingItems()
        assertEquals(1, pendingItems.size)
        assertEquals(SyncEntityType.PATIENT.name, pendingItems[0].entityType)
        assertEquals(SyncAction.CREATE.name, pendingItems[0].action)
    }

    @Test
    fun syncQueueMarksItemsAsFailed() = runBlocking {
        val queueItem = SyncQueueEntity(
            entityType = SyncEntityType.ORDER.name,
            action = SyncAction.CREATE.name,
            entityId = "order-1",
            payload = "{}",
            retryCount = 0,
            maxRetries = 3,
            createdAt = System.currentTimeMillis()
        )

        val id = syncQueueDao.insert(queueItem)
        syncQueueDao.markFailed(id)

        val failedItems = syncQueueDao.getFailedItems()
        assertEquals(1, failedItems.size)
        assertEquals(id, failedItems[0].id)
    }

    @Test
    fun syncQueueDeletesItemAfterSuccessfulSync() = runBlocking {
        val queueItem = SyncQueueEntity(
            entityType = SyncEntityType.PATIENT.name,
            action = SyncAction.CREATE.name,
            entityId = "p-completed",
            payload = """{"fullName":"Complete","phone":"07701111111"}""",
            retryCount = 0,
            maxRetries = 3,
            createdAt = System.currentTimeMillis()
        )

        val id = syncQueueDao.insert(queueItem)
        syncQueueDao.deleteById(id)

        val pendingItems = syncQueueDao.getPendingItems()
        assertTrue(pendingItems.isEmpty())
    }

    @Test
    fun syncQueuePreventsDuplicateIds() = runBlocking {
        val queueItem = SyncQueueEntity(
            entityType = SyncEntityType.PATIENT.name,
            action = SyncAction.CREATE.name,
            entityId = "p-dup",
            payload = "{}",
            retryCount = 0,
            maxRetries = 3,
            createdAt = System.currentTimeMillis()
        )

        val id1 = syncQueueDao.insert(queueItem)
        val id2 = syncQueueDao.insert(queueItem.copy())
        assertTrue(id1 != id2)
    }

    @Test
    fun syncQueueIncrementsRetryCount() = runBlocking {
        val queueItem = SyncQueueEntity(
            entityType = SyncEntityType.RESULT.name,
            action = SyncAction.CREATE.name,
            entityId = "r-1",
            payload = """{"value":"5.5"}""",
            retryCount = 0,
            maxRetries = 3,
            createdAt = System.currentTimeMillis()
        )

        val id = syncQueueDao.insert(queueItem)

        syncQueueDao.incrementRetry(id)
        syncQueueDao.incrementRetry(id)

        val items = syncQueueDao.getFailedItems()
        val match = items.find { it.id == id }
        assertEquals(2, match?.retryCount)
    }

    @Test
    fun syncQueueGetPendingItemsExcludesFailedItems() = runBlocking {
        val pendingItem = SyncQueueEntity(
            entityType = SyncEntityType.PATIENT.name,
            action = SyncAction.CREATE.name,
            entityId = "p-pending",
            payload = """{"fullName":"Pending"}""",
            retryCount = 0,
            maxRetries = 3,
            createdAt = System.currentTimeMillis()
        )
        val failedItem = SyncQueueEntity(
            entityType = SyncEntityType.ORDER.name,
            action = SyncAction.CREATE.name,
            entityId = "o-failed",
            payload = "{}",
            retryCount = 4,
            maxRetries = 3,
            createdAt = System.currentTimeMillis()
        )

        syncQueueDao.insert(pendingItem)
        val failedId = syncQueueDao.insert(failedItem)
        syncQueueDao.markFailed(failedId)

        val pending = syncQueueDao.getPendingItems()
        assertEquals(1, pending.size)
        assertEquals(SyncEntityType.PATIENT.name, pending[0].entityType)
    }

    @Test
    fun patientAndSyncRelationships() = runBlocking {
        val patient = PatientEntity(
            id = "p-relation",
            fullName = "Relationship Test",
            phone = "07709999999",
            birthDate = "1980-01-01",
            gender = "male",
            createdAt = "2024-01-01T00:00:00Z",
            updatedAt = "2024-01-01T00:00:00Z"
        )
        patientDao.insertPatient(patient)

        val orderRefs = listOf(
            SyncQueueEntity(
                entityType = SyncEntityType.ORDER.name,
                action = SyncAction.CREATE.name,
                entityId = "order-rel-1",
                payload = """{"patientId":"p-relation","tests":["CBC"]}""",
                retryCount = 0,
                maxRetries = 3,
                createdAt = System.currentTimeMillis()
            ),
            SyncQueueEntity(
                entityType = SyncEntityType.ORDER.name,
                action = SyncAction.CREATE.name,
                entityId = "order-rel-2",
                payload = """{"patientId":"p-relation","tests":["X-Ray"]}""",
                retryCount = 0,
                maxRetries = 3,
                createdAt = System.currentTimeMillis()
            )
        )

        orderRefs.forEach { syncQueueDao.insert(it) }

        val pending = syncQueueDao.getPendingItems()
        assertEquals(2, pending.size)
        assertTrue(pending.all { it.entityType == SyncEntityType.ORDER.name })

        val patientRetrieved = patientDao.getPatientById("p-relation")
        assertNotNull(patientRetrieved)
    }

    @Test
    fun syncQueueGetPendingReturnsEmptyWhenNoItems() = runBlocking {
        val pending = syncQueueDao.getPendingItems()
        assertTrue(pending.isEmpty())
    }

    @Test
    fun syncQueueStoresMultipleEntityTypes() = runBlocking {
        val entities = listOf(
            SyncEntityType.PATIENT,
            SyncEntityType.ORDER,
            SyncEntityType.SAMPLE,
            SyncEntityType.RESULT,
            SyncEntityType.NOTIFICATION
        )

        entities.forEachIndexed { index, type ->
            syncQueueDao.insert(
                SyncQueueEntity(
                    entityType = type.name,
                    action = SyncAction.CREATE.name,
                    entityId = "entity-$index",
                    payload = "{}",
                    retryCount = 0,
                    maxRetries = 3,
                    createdAt = System.currentTimeMillis()
                )
            )
        }

        val pending = syncQueueDao.getPendingItems()
        assertEquals(entities.size, pending.size)

        val entityTypes = pending.map { it.entityType }.toSet()
        entities.forEach { assertTrue(entityTypes.contains(it.name)) }
    }

    @Test
    fun syncQueueGetCountsReturnsCorrectNumbers() = runBlocking {
        repeat(3) {
            syncQueueDao.insert(
                SyncQueueEntity(
                    entityType = SyncEntityType.PATIENT.name,
                    action = SyncAction.CREATE.name,
                    entityId = "p-count-$it",
                    payload = "{}",
                    retryCount = 0,
                    maxRetries = 3,
                    createdAt = System.currentTimeMillis()
                )
            )
        }

        val failedId = syncQueueDao.insert(
            SyncQueueEntity(
                entityType = SyncEntityType.ORDER.name,
                action = SyncAction.CREATE.name,
                entityId = "o-count-fail",
                payload = "{}",
                retryCount = 0,
                maxRetries = 3,
                createdAt = System.currentTimeMillis()
            )
        )
        syncQueueDao.markFailed(failedId)

        val pending = syncQueueDao.getPendingItems()
        assertEquals(3, pending.size)

        val failed = syncQueueDao.getFailedItems()
        assertEquals(1, failed.size)
    }
}
