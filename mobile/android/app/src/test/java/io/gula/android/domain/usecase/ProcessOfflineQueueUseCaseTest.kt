package io.gula.android.domain.usecase

import io.gula.android.data.local.dao.SyncQueueDao
import io.gula.android.data.local.entity.SyncQueueEntity
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.PatientDto
import io.gula.android.domain.model.SyncAction
import io.gula.android.domain.model.SyncEntityType
import io.gula.android.util.NetworkMonitor
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest
import org.junit.Before
import org.junit.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class ProcessOfflineQueueUseCaseTest {

    private lateinit var syncQueueDao: SyncQueueDao
    private lateinit var gulaApi: GulaApi
    private lateinit var networkMonitor: NetworkMonitor
    private lateinit var useCase: ProcessOfflineQueueUseCase

    private val testDispatcher = StandardTestDispatcher()
    private val onlineFlow = MutableStateFlow(true)

    @Before
    fun setup() {
        syncQueueDao = mockk()
        gulaApi = mockk()
        networkMonitor = mockk()

        every { networkMonitor.isOnline } returns onlineFlow
        every { networkMonitor.isOnline.value } returns true

        useCase = ProcessOfflineQueueUseCase(
            syncQueueDao = syncQueueDao,
            gulaApi = gulaApi,
            networkMonitor = networkMonitor,
            ioDispatcher = testDispatcher
        )
    }

    @Test
    fun `processes create patient action successfully`() = runTest(testDispatcher) {
        val queueEntity = SyncQueueEntity(
            id = 1,
            entityType = SyncEntityType.PATIENT.name,
            action = SyncAction.CREATE.name,
            entityId = "temp-id",
            payload = """{"fullName":"Queued Patient","phone":"07701234567","gender":"male"}""",
            retryCount = 0,
            maxRetries = 3,
            createdAt = System.currentTimeMillis()
        )

        val pendingItems = listOf(queueEntity)

        coEvery { syncQueueDao.getPendingItems() } returns pendingItems
        coEvery { syncQueueDao.markSyncing(1) } returns Unit
        coEvery { gulaApi.createPatient(any<PatientDto>()) } returns PatientDto(
            id = "p-created",
            fullName = "Queued Patient",
            phone = "07701234567",
            birthDate = null,
            gender = "male",
            isActive = true,
            labId = "lab-1",
            createdAt = "2024-01-01T00:00:00Z",
            updatedAt = "2024-01-01T00:00:00Z"
        )
        coEvery { syncQueueDao.deleteById(1) } returns Unit

        val result = useCase()

        assertTrue(result.isSuccess)
        val processed = result.getOrThrow()
        assertEquals(1, processed.size)
        assertEquals(1, processed[0].id)
        assertTrue(processed[0].isSuccess)

        coVerify {
            syncQueueDao.getPendingItems()
            syncQueueDao.markSyncing(1)
            gulaApi.createPatient(any<PatientDto>())
            syncQueueDao.deleteById(1)
        }
    }

    @Test
    fun `skips processing when offline`() = runTest(testDispatcher) {
        onlineFlow.value = false

        val result = useCase()

        assertTrue(result.isSuccess)
        val processed = result.getOrThrow()
        assertTrue(processed.isEmpty())

        coVerify(exactly = 0) { syncQueueDao.getPendingItems() }
        coVerify(exactly = 0) { gulaApi.createPatient(any()) }
    }

    @Test
    fun `marks item as failed after max retries`() = runTest(testDispatcher) {
        val failedEntity = SyncQueueEntity(
            id = 2,
            entityType = SyncEntityType.ORDER.name,
            action = SyncAction.CREATE.name,
            entityId = "order-temp",
            payload = "{}",
            retryCount = 2,
            maxRetries = 3,
            createdAt = System.currentTimeMillis()
        )

        coEvery { syncQueueDao.getPendingItems() } returns listOf(failedEntity)
        coEvery { syncQueueDao.markSyncing(2) } returns Unit
        coEvery { gulaApi.createOrder(any()) } throws RuntimeException("API error")
        coEvery { syncQueueDao.incrementRetry(2) } returns Unit
        coEvery { syncQueueDao.markFailed(2) } returns Unit

        val result = useCase()

        assertTrue(result.isSuccess)
        val processed = result.getOrThrow()
        assertEquals(1, processed.size)
        assertTrue(processed[0].isFailure)

        coVerify {
            syncQueueDao.incrementRetry(2)
            syncQueueDao.markFailed(2)
        }
    }

    @Test
    fun `processes multiple items in queue`() = runTest(testDispatcher) {
        val items = listOf(
            SyncQueueEntity(
                id = 1,
                entityType = SyncEntityType.PATIENT.name,
                action = SyncAction.CREATE.name,
                entityId = "p1",
                payload = """{"fullName":"Patient One","phone":"07701111111"}""",
                retryCount = 0,
                maxRetries = 3,
                createdAt = System.currentTimeMillis()
            ),
            SyncQueueEntity(
                id = 2,
                entityType = SyncEntityType.ORDER.name,
                action = SyncAction.CREATE.name,
                entityId = "o1",
                payload = """{"patientId":"p1","tests":[]}""",
                retryCount = 0,
                maxRetries = 3,
                createdAt = System.currentTimeMillis()
            )
        )

        coEvery { syncQueueDao.getPendingItems() } returns items
        coEvery { syncQueueDao.markSyncing(any()) } returns Unit
        coEvery { gulaApi.createPatient(any<PatientDto>()) } returns PatientDto(
            id = "p-api", fullName = "Patient One", phone = "07701111111",
            isActive = true, labId = "lab-1",
            createdAt = "", updatedAt = ""
        )
        coEvery { gulaApi.createOrder(any()) } throws RuntimeException("Order API error")
        coEvery { syncQueueDao.deleteById(1) } returns Unit
        coEvery { syncQueueDao.incrementRetry(2) } returns Unit

        val result = useCase()

        assertTrue(result.isSuccess)
        val processed = result.getOrThrow()
        assertEquals(2, processed.size)
        assertTrue(processed[0].isSuccess)
        assertTrue(processed[1].isFailure)

        coVerify {
            syncQueueDao.deleteById(1)
            syncQueueDao.incrementRetry(2)
        }
    }

    @Test
    fun `handles null payload gracefully`() = runTest(testDispatcher) {
        val entity = SyncQueueEntity(
            id = 3,
            entityType = SyncEntityType.PATIENT.name,
            action = SyncAction.CREATE.name,
            entityId = "bad-id",
            payload = null,
            retryCount = 0,
            maxRetries = 3,
            createdAt = System.currentTimeMillis()
        )

        coEvery { syncQueueDao.getPendingItems() } returns listOf(entity)
        coEvery { syncQueueDao.markSyncing(3) } returns Unit
        coEvery { syncQueueDao.markFailed(3) } returns Unit

        val result = useCase()

        assertTrue(result.isSuccess)
        val processed = result.getOrThrow()
        assertEquals(1, processed.size)
        assertTrue(processed[0].isFailure)

        coVerify {
            syncQueueDao.markFailed(3)
            coEvery { gulaApi.createPatient(any()) } wasNot called
        }
    }
}
