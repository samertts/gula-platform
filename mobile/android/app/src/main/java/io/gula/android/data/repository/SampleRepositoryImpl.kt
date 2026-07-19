package io.gula.android.data.repository

import io.gula.android.data.local.dao.SampleDao
import io.gula.android.data.local.entity.SampleEntity
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.SampleCreateRequestDto
import io.gula.android.data.remote.dto.SampleResponseDto
import io.gula.android.data.remote.dto.SampleUpdateRequestDto
import io.gula.android.domain.model.CreateSampleRequest
import io.gula.android.domain.model.Sample
import io.gula.android.domain.model.UpdateSampleRequest
import io.gula.android.domain.repository.SampleRepository
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SampleRepositoryImpl @Inject constructor(
    private val sampleDao: SampleDao,
    private val gulaApi: GulaApi,
) : SampleRepository {

    override fun getSamples(status: String?, page: Int, limit: Int): Flow<Resource<List<Sample>>> {
        return sampleDao.getSamples(status, limit, (page - 1) * limit).map { entities ->
            if (entities.isNotEmpty()) {
                Resource.success(entities.map { it.toDomain() })
            } else {
                Resource.loading()
            }
        }
    }

    override fun getSampleByBarcode(barcode: String): Flow<Resource<Sample>> {
        return sampleDao.getSampleByBarcode(barcode).map { entity ->
            if (entity != null) Resource.success(entity.toDomain())
            else Resource.loading()
        }
    }

    override fun getSamplesByOrderId(orderId: Int): Flow<Resource<List<Sample>>> {
        return sampleDao.getSamplesByOrderId(orderId).map { entities ->
            Resource.success(entities.map { it.toDomain() })
        }
    }

    override suspend fun createSample(request: CreateSampleRequest): Resource<Sample> {
        return try {
            val response = gulaApi.createSample(
                SampleCreateRequestDto(
                    orderId = request.orderId,
                    sampleType = request.sampleType,
                    collectedBy = request.collectedBy,
                    notes = request.notes,
                    storageLocation = request.storageLocation,
                )
            )
            if (response.isSuccessful) {
                val dto = response.body()!!
                val sample = dto.toDomain()
                sampleDao.insert(sample.toEntity())
                Resource.success(sample)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun updateSample(barcode: String, request: UpdateSampleRequest): Resource<Sample> {
        return try {
            val response = gulaApi.updateSample(
                barcode,
                SampleUpdateRequestDto(
                    status = request.status,
                    rejectionReason = request.rejectionReason,
                    notes = request.notes,
                    storageLocation = request.storageLocation,
                )
            )
            if (response.isSuccessful) {
                val dto = response.body()!!
                val sample = dto.toDomain()
                sampleDao.insert(sample.toEntity())
                Resource.success(sample)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun refreshSamples() {
        try {
            val response = gulaApi.getSamples(limit = 100)
            if (response.isSuccessful) {
                sampleDao.insertAll(response.body()!!.items.map { it.toDomain().toEntity() })
            }
        } catch (_: Exception) { }
    }
}

private fun SampleResponseDto.toDomain() = Sample(
    id = id,
    barcode = barcode,
    orderId = orderId,
    sampleType = sampleType,
    status = status,
    collectedBy = collectedBy,
    collectionTime = collectionTime,
    rejectionReason = rejectionReason,
    notes = notes,
    storageLocation = storageLocation,
    createdAt = createdAt,
    updatedAt = updatedAt,
)

private fun Sample.toEntity() = SampleEntity(
    id = id,
    barcode = barcode,
    orderId = orderId,
    sampleType = sampleType,
    status = status,
    collectedBy = collectedBy,
    collectionTime = collectionTime,
    rejectionReason = rejectionReason,
    notes = notes,
    storageLocation = storageLocation,
    createdAt = createdAt,
    updatedAt = updatedAt,
)

private fun SampleEntity.toDomain() = Sample(
    id = id,
    barcode = barcode,
    orderId = orderId,
    sampleType = sampleType,
    status = status,
    collectedBy = collectedBy,
    collectionTime = collectionTime,
    rejectionReason = rejectionReason,
    notes = notes,
    storageLocation = storageLocation,
    createdAt = createdAt,
    updatedAt = updatedAt,
)
