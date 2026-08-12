package io.gula.android.domain.repository

import io.gula.android.domain.model.CreateSampleRequest
import io.gula.android.domain.model.Sample
import io.gula.android.domain.model.UpdateSampleRequest
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow

interface SampleRepository {
    fun getSamples(status: String? = null, page: Int = 1, limit: Int = 20): Flow<Resource<List<Sample>>>
    fun getSampleByBarcode(barcode: String): Flow<Resource<Sample>>
    fun getSamplesByOrderId(orderId: Int): Flow<Resource<List<Sample>>>
    suspend fun createSample(request: CreateSampleRequest): Resource<Sample>
    suspend fun updateSample(barcode: String, request: UpdateSampleRequest): Resource<Sample>
    suspend fun refreshSamples()
}
