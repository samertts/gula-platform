package io.gula.android.domain.usecase

import io.gula.android.domain.model.SyncStatus
import io.gula.android.domain.repository.SyncRepository
import io.gula.android.util.NetworkMonitor
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Before
import org.junit.Test

class ProcessOfflineQueueUseCaseTest {

    private lateinit var syncRepository: SyncRepository
    private lateinit var networkMonitor: NetworkMonitor
    private lateinit var useCase: ProcessOfflineQueueUseCase
    private val online = MutableStateFlow(true)

    @Before
    fun setup() {
        syncRepository = mockk()
        networkMonitor = mockk()
        every { networkMonitor.isOnline } returns online
        useCase = ProcessOfflineQueueUseCase(syncRepository, networkMonitor)
    }

    @Test
    fun `processes the queue when the device is online`() = runTest {
        val expected = SyncStatus(isSyncing = false, pendingCount = 2, failedCount = 0)
        coEvery { syncRepository.processQueue() } returns expected

        val result = useCase()

        assertEquals(expected, result)
        coVerify(exactly = 1) { syncRepository.processQueue() }
        coVerify(exactly = 0) { syncRepository.retryFailed() }
    }

    @Test
    fun `retries failed records after queue processing`() = runTest {
        val expected = SyncStatus(isSyncing = false, pendingCount = 1, failedCount = 1)
        coEvery { syncRepository.processQueue() } returns expected
        coEvery { syncRepository.retryFailed() } returns Unit

        val result = useCase()

        assertEquals(expected, result)
        coVerify(exactly = 1) { syncRepository.retryFailed() }
    }

    @Test
    fun `reports pending records without processing while offline`() = runTest {
        online.value = false
        coEvery { syncRepository.getPendingCount() } returns 4
        coEvery { syncRepository.getFailedCount() } returns 1

        val result = useCase()

        assertFalse(result.isSyncing)
        assertEquals(4, result.pendingCount)
        assertEquals(1, result.failedCount)
        assertEquals("No internet connection. Items will sync when online.", result.errorMessage)
        coVerify(exactly = 0) { syncRepository.processQueue() }
    }
}
