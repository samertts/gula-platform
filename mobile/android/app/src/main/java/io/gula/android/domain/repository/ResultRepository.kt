package io.gula.android.domain.repository

import io.gula.android.domain.model.*
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow

interface ResultRepository {
    fun getResults(page: Int = 1, limit: Int = 20): Flow<Resource<List<TestResult>>>
    fun getResultById(id: Int): Flow<Resource<TestResult>>
    fun getResultsByOrderId(orderId: Int): Flow<Resource<List<TestResult>>>
    fun getCriticalAlerts(): Flow<Resource<List<CriticalAlert>>>
    suspend fun createResult(testResult: TestResult): Resource<TestResult>
    suspend fun updateResult(id: Int, testResult: TestResult): Resource<TestResult>
    suspend fun validateResult(id: Int, validation: ResultValidation): Resource<Unit>
    suspend fun acknowledgeCriticalAlert(alertId: Int): Resource<Unit>
    suspend fun refreshResults()
}
