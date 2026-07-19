package io.gula.android.data.repository

import io.gula.android.data.local.dao.ResultDao
import io.gula.android.data.local.entity.ResultEntity
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.*
import io.gula.android.domain.model.*
import io.gula.android.domain.repository.ResultRepository
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ResultRepositoryImpl @Inject constructor(
    private val resultDao: ResultDao,
    private val gulaApi: GulaApi,
) : ResultRepository {

    override fun getResults(page: Int, limit: Int): Flow<Resource<List<TestResult>>> {
        return resultDao.getResults(limit, (page - 1) * limit).map { entities ->
            if (entities.isNotEmpty()) {
                Resource.success(entities.map { it.toDomain() })
            } else {
                Resource.loading()
            }
        }
    }

    override fun getResultById(id: Int): Flow<Resource<TestResult>> {
        return resultDao.getResultById(id).map { entity ->
            if (entity != null) Resource.success(entity.toDomain())
            else Resource.loading()
        }
    }

    override fun getResultsByOrderId(orderId: Int): Flow<Resource<List<TestResult>>> {
        return resultDao.getResultsByOrderId(orderId).map { entities ->
            Resource.success(entities.map { it.toDomain() })
        }
    }

    override fun getCriticalAlerts(): Flow<Resource<List<CriticalAlert>>> {
        return resultDao.getCriticalResults().map { entities ->
            Resource.success(entities.map { entity ->
                CriticalAlert(
                    id = entity.id,
                    labId = entity.labId ?: 0,
                    patientName = entity.testNameEn,
                    testName = entity.testNameEn,
                    value = entity.resultValue?.toString() ?: entity.resultText ?: "",
                    severity = if (entity.isCritical) "critical" else "abnormal",
                    status = entity.status,
                    createdAt = entity.createdAt ?: "",
                )
            })
        }
    }

    override suspend fun createResult(testResult: TestResult): Resource<TestResult> {
        return try {
            val response = gulaApi.createResult(testResult.toCreateDto())
            if (response.isSuccessful) {
                val dto = response.body()!!
                val result = dto.toDomain()
                resultDao.insert(result.toEntity())
                Resource.success(result)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun updateResult(id: Int, testResult: TestResult): Resource<TestResult> {
        return try {
            val response = gulaApi.updateResult(id, testResult.toCreateDto())
            if (response.isSuccessful) {
                val dto = response.body()!!
                val result = dto.toDomain()
                resultDao.insert(result.toEntity())
                Resource.success(result)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun validateResult(id: Int, validation: ResultValidation): Resource<Unit> {
        return try {
            val response = gulaApi.validateResult(
                id,
                ValidateResultRequestDto(
                    testName = validation.testName,
                    testCode = validation.testCode,
                    value = validation.value,
                    unit = validation.unit,
                    normalRangeLow = validation.normalRangeLow,
                    normalRangeHigh = validation.normalRangeHigh,
                )
            )
            if (response.isSuccessful) Resource.success(Unit)
            else Resource.error(parseError(response.code(), response.errorBody()?.string()))
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun acknowledgeCriticalAlert(alertId: Int): Resource<Unit> {
        return try {
            val response = gulaApi.acknowledgeCriticalAlert(alertId)
            if (response.isSuccessful) Resource.success(Unit)
            else Resource.error(parseError(response.code(), response.errorBody()?.string()))
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun refreshResults() {
        try {
            val response = gulaApi.getResults(limit = 100)
            if (response.isSuccessful) {
                resultDao.insertAll(response.body()!!.items.map { it.toDomain().toEntity() })
            }
        } catch (_: Exception) { }
    }
}

private fun TestResultResponseDto.toDomain() = TestResult(
    id = id,
    testCode = testCode,
    testNameEn = testNameEn,
    testNameAr = testNameAr,
    category = category,
    resultValue = resultValue,
    resultText = resultText,
    unit = unit,
    referenceMin = referenceMin,
    referenceMax = referenceMax,
    status = status,
    isCritical = isCritical,
    isAbnormal = isAbnormal,
    abnormalityDirection = abnormalityDirection,
    sampleCollectedAt = sampleCollectedAt ?: "",
    resultCompletedAt = resultCompletedAt,
    verifiedAt = verifiedAt,
    verifiedBy = verifiedBy,
    sampleBarcode = sampleBarcode,
    orderingPhysician = orderingPhysician,
    clinicalNotes = clinicalNotes,
    patientId = patientId,
    labId = labId,
    orderId = orderId,
    createdAt = createdAt,
    updatedAt = updatedAt,
)

private fun TestResult.toCreateDto() = TestResultCreateDto(
    orderId = orderId,
    patientId = patientId,
    labId = labId,
    testCode = testCode,
    testNameEn = testNameEn,
    testNameAr = testNameAr,
    category = category,
    resultValue = resultValue,
    resultText = resultText,
    unit = unit,
    referenceMin = referenceMin,
    referenceMax = referenceMax,
    status = status,
    isCritical = isCritical,
    isAbnormal = isAbnormal,
    abnormalityDirection = abnormalityDirection,
    sampleCollectedAt = sampleCollectedAt,
    sampleBarcode = sampleBarcode,
    orderingPhysician = orderingPhysician,
    clinicalNotes = clinicalNotes,
)

private fun TestResult.toEntity() = ResultEntity(
    id = id,
    orderId = orderId,
    patientId = patientId,
    labId = labId,
    testCode = testCode,
    testNameEn = testNameEn,
    testNameAr = testNameAr,
    category = category,
    resultValue = resultValue,
    resultText = resultText,
    unit = unit,
    referenceMin = referenceMin,
    referenceMax = referenceMax,
    status = status,
    isCritical = isCritical,
    isAbnormal = isAbnormal,
    abnormalityDirection = abnormalityDirection,
    sampleCollectedAt = sampleCollectedAt,
    resultCompletedAt = resultCompletedAt,
    verifiedAt = verifiedAt,
    verifiedBy = verifiedBy,
    sampleBarcode = sampleBarcode,
    orderingPhysician = orderingPhysician,
    clinicalNotes = clinicalNotes,
    createdAt = createdAt,
    updatedAt = updatedAt,
)

private fun ResultEntity.toDomain() = TestResult(
    id = id,
    testCode = testCode,
    testNameEn = testNameEn,
    testNameAr = testNameAr,
    category = category,
    resultValue = resultValue,
    resultText = resultText,
    unit = unit,
    referenceMin = referenceMin,
    referenceMax = referenceMax,
    status = status,
    isCritical = isCritical,
    isAbnormal = isAbnormal,
    abnormalityDirection = abnormalityDirection,
    sampleCollectedAt = sampleCollectedAt ?: "",
    resultCompletedAt = resultCompletedAt,
    verifiedAt = verifiedAt,
    verifiedBy = verifiedBy,
    sampleBarcode = sampleBarcode,
    orderingPhysician = orderingPhysician,
    clinicalNotes = clinicalNotes,
    patientId = patientId,
    labId = labId,
    orderId = orderId,
    createdAt = createdAt,
    updatedAt = updatedAt,
)
