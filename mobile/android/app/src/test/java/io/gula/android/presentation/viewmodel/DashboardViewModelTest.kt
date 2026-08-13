package io.gula.android.ui.features.dashboard

import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.DashboardStatsDto
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Before
import org.junit.Test
import retrofit2.Response

class DashboardViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var gulaApi: GulaApi

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)
        gulaApi = mockk()
    }

    @After
    fun teardown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `loads dashboard statistics from the API`() = runTest(testDispatcher) {
        coEvery { gulaApi.getDashboardStats() } returns Response.success(
            DashboardStatsDto(
                patientsCount = 42,
                ordersToday = 9,
                pendingResults = 4,
                criticalAlerts = 1,
                samplesToday = 7,
                revenueToday = 1250.5,
            ),
        )

        val viewModel = DashboardViewModel(gulaApi)
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertEquals(42, state.stats.patientsCount)
        assertEquals(9, state.stats.ordersToday)
        assertEquals(4, state.stats.pendingResults)
        assertEquals(1, state.stats.criticalAlerts)
        assertEquals(7, state.stats.samplesToday)
    }

    @Test
    fun `reports a stable error when the dashboard API rejects the request`() = runTest(testDispatcher) {
        coEvery { gulaApi.getDashboardStats() } returns Response.error(
            500,
            "Server error".toResponseBody("text/plain".toMediaType()),
        )

        val viewModel = DashboardViewModel(gulaApi)
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertEquals("Failed to load dashboard", state.error)
    }
}
