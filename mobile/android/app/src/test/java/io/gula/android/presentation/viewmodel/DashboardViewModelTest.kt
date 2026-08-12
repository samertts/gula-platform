package io.gula.android.presentation.viewmodel

import app.cash.turbine.test
import io.gula.android.data.repository.AuthRepositoryImpl
import io.gula.android.data.repository.OrderRepositoryImpl
import io.gula.android.data.repository.ResultRepositoryImpl
import io.gula.android.data.repository.SampleRepositoryImpl
import io.gula.android.domain.model.User
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Before
import org.junit.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class DashboardViewModelTest {

    private lateinit var orderRepository: OrderRepositoryImpl
    private lateinit var resultRepository: ResultRepositoryImpl
    private lateinit var sampleRepository: SampleRepositoryImpl
    private lateinit var authRepository: AuthRepositoryImpl
    private lateinit var viewModel: DashboardViewModel

    private val testDispatcher = StandardTestDispatcher()

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)

        orderRepository = mockk()
        resultRepository = mockk()
        sampleRepository = mockk()
        authRepository = mockk()
    }

    @After
    fun teardown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `loadDashboard emits loading then success`() = runTest(testDispatcher) {
        val mockUser = User(
            id = "user-1",
            email = "admin@lab.com",
            fullName = "Admin User",
            role = "admin",
            labId = "lab-1",
            isActive = true
        )

        coEvery { authRepository.checkAuth() } returns Result.success(mockUser)
        coEvery { orderRepository.getOrdersCount() } returns Result.success(42)
        coEvery { resultRepository.getPendingResultsCount() } returns Result.success(15)
        coEvery { sampleRepository.getSamplesCount() } returns Result.success(28)
        coEvery { orderRepository.getRecentOrders(any()) } returns Result.success(emptyList())
        coEvery { resultRepository.getCriticalAlertsCount() } returns Result.success(3)

        viewModel = DashboardViewModel(
            orderRepository = orderRepository,
            resultRepository = resultRepository,
            sampleRepository = sampleRepository,
            authRepository = authRepository
        )

        viewModel.uiState.test {
            val initialState = awaitItem()
            assertNotNull(initialState)
            assertTrue(initialState.isLoading || initialState.stats == null)

            val loadedState = awaitItem()
            assertNotNull(loadedState.stats)
            assertEquals(42, loadedState.stats.ordersToday)
            assertEquals(15, loadedState.stats.pendingResults)
            assertEquals(28, loadedState.stats.samplesToday)
            assertEquals(3, loadedState.stats.criticalAlerts)
            assertEquals(0, loadedState.stats.totalPatients)
        }
    }

    @Test
    fun `loadDashboard handles error gracefully`() = runTest(testDispatcher) {
        coEvery { authRepository.checkAuth() } throws RuntimeException("Auth failed")

        viewModel = DashboardViewModel(
            orderRepository = orderRepository,
            resultRepository = resultRepository,
            sampleRepository = sampleRepository,
            authRepository = authRepository
        )

        viewModel.uiState.test {
            val state = awaitItem()
            assertNotNull(state)
            assertTrue(state.isLoading || state.error != null)
        }
    }

    @Test
    fun `loadDashboard shows user info`() = runTest(testDispatcher) {
        val mockUser = User(
            id = "user-1",
            email = "tech@lab.com",
            fullName = "Lab Technician",
            role = "lab_tech",
            labId = "lab-1",
            isActive = true
        )

        coEvery { authRepository.checkAuth() } returns Result.success(mockUser)
        coEvery { orderRepository.getOrdersCount() } returns Result.success(0)
        coEvery { resultRepository.getPendingResultsCount() } returns Result.success(0)
        coEvery { sampleRepository.getSamplesCount() } returns Result.success(0)
        coEvery { orderRepository.getRecentOrders(any()) } returns Result.success(emptyList())
        coEvery { resultRepository.getCriticalAlertsCount() } returns Result.success(0)

        viewModel = DashboardViewModel(
            orderRepository = orderRepository,
            resultRepository = resultRepository,
            sampleRepository = sampleRepository,
            authRepository = authRepository
        )

        viewModel.uiState.test {
            skipItems(1)
            val state = awaitItem()
            assertEquals("Lab Technician", state.user?.fullName)
            assertEquals("lab_tech", state.user?.role)
        }
    }

    @Test
    fun `refreshDashboard reloads stats`() = runTest(testDispatcher) {
        coEvery { authRepository.checkAuth() } returns Result.success(
            User("u1", "a@b.com", "User", "admin", "lab-1", true)
        )
        coEvery { orderRepository.getOrdersCount() } returns Result.success(10)
        coEvery { resultRepository.getPendingResultsCount() } returns Result.success(5)
        coEvery { sampleRepository.getSamplesCount() } returns Result.success(8)
        coEvery { orderRepository.getRecentOrders(any()) } returns Result.success(emptyList())
        coEvery { resultRepository.getCriticalAlertsCount() } returns Result.success(1)

        viewModel = DashboardViewModel(
            orderRepository = orderRepository,
            resultRepository = resultRepository,
            sampleRepository = sampleRepository,
            authRepository = authRepository
        )

        viewModel.uiState.test {
            skipItems(1)

            val beforeRefresh = awaitItem()
            assertEquals(10, beforeRefresh.stats?.ordersToday)

            coEvery { orderRepository.getOrdersCount() } returns Result.success(25)
            coEvery { resultRepository.getPendingResultsCount() } returns Result.success(12)
            coEvery { sampleRepository.getSamplesCount() } returns Result.success(18)
            coEvery { resultRepository.getCriticalAlertsCount() } returns Result.success(2)

            viewModel.refresh()

            val afterRefresh = awaitItem()
            assertEquals(25, afterRefresh.stats?.ordersToday)
            assertEquals(12, afterRefresh.stats?.pendingResults)
            assertEquals(18, afterRefresh.stats?.samplesToday)
            assertEquals(2, afterRefresh.stats?.criticalAlerts)
        }
    }
}
