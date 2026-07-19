package io.gula.android.data.repository

import io.gula.android.data.local.dao.OrderDao
import io.gula.android.data.local.entity.OrderEntity
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.*
import io.gula.android.domain.model.*
import io.gula.android.domain.repository.OrderRepository
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class OrderRepositoryImpl @Inject constructor(
    private val orderDao: OrderDao,
    private val gulaApi: GulaApi,
) : OrderRepository {

    override fun getOrders(search: String?, page: Int, limit: Int): Flow<Resource<List<Order>>> {
        return orderDao.getOrders(search, limit, (page - 1) * limit).map { entities ->
            if (entities.isNotEmpty()) {
                Resource.success(entities.map { it.toDomain() })
            } else {
                Resource.loading()
            }
        }
    }

    override fun getOrderById(id: Int): Flow<Resource<Order>> {
        return orderDao.getOrderById(id).map { entity ->
            if (entity != null) Resource.success(entity.toDomain())
            else Resource.loading()
        }
    }

    override fun getOrdersByPatientId(patientId: Int): Flow<Resource<List<Order>>> {
        return orderDao.getOrdersByPatientId(patientId).map { entities ->
            Resource.success(entities.map { it.toDomain() })
        }
    }

    override suspend fun createOrder(request: CreateOrderRequest): Resource<Order> {
        return try {
            val response = gulaApi.createOrder(
                CreateOrderRequestDto(
                    patientId = request.patientId,
                    doctorName = request.doctorName,
                    doctorUserId = request.doctorUserId,
                    results = request.results.map { r ->
                        ResultItemDto(
                            testName = r.testName,
                            value = r.value,
                            valueText = r.valueText,
                            unit = r.unit,
                            normalRangeLow = r.normalRangeLow,
                            normalRangeHigh = r.normalRangeHigh,
                        )
                    },
                )
            )
            if (response.isSuccessful) {
                val dto = response.body()!!
                val order = dto.toDomain()
                orderDao.insert(order.toEntity())
                Resource.success(order)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun cancelOrder(id: Int): Resource<Unit> {
        return try {
            val response = gulaApi.cancelOrder(id)
            if (response.isSuccessful) {
                Resource.success(Unit)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun validateOrder(id: Int): Resource<Unit> {
        return try {
            val response = gulaApi.validateOrder(id)
            if (response.isSuccessful) {
                Resource.success(Unit)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun createBatchOrders(request: BatchOrderRequest): Resource<BatchOrderResult> {
        return try {
            val response = gulaApi.createBatchOrders(
                BatchOrderRequestDto(
                    orders = request.orders.map { item ->
                        BatchOrderItemDto(
                            patientId = item.patientId,
                            doctorName = item.doctorName,
                            results = item.results.map { r ->
                                ResultItemDto(
                                    testName = r.testName,
                                    value = r.value,
                                    valueText = r.valueText,
                                    unit = r.unit,
                                    normalRangeLow = r.normalRangeLow,
                                    normalRangeHigh = r.normalRangeHigh,
                                )
                            },
                        )
                    },
                )
            )
            if (response.isSuccessful) {
                val body = response.body()!!
                Resource.success(BatchOrderResult(body.created, body.failed, body.errors))
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun analyzeResults(items: List<ResultItemInput>): Resource<OrderIntelligence> {
        return try {
            val response = gulaApi.analyzeResults(
                AnalyzeRequestDto(
                    results = items.map { r ->
                        ResultItemDto(
                            testName = r.testName,
                            value = r.value,
                            valueText = r.valueText,
                            unit = r.unit,
                            normalRangeLow = r.normalRangeLow,
                            normalRangeHigh = r.normalRangeHigh,
                        )
                    },
                )
            )
            if (response.isSuccessful) {
                val body = response.body()!!
                Resource.success(body.toDomain())
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun getOrderIntelligence(orderId: Int): Resource<OrderIntelligence> {
        return try {
            val response = gulaApi.getOrderIntelligence(orderId)
            if (response.isSuccessful) {
                Resource.success(response.body()!!.toDomain())
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun refreshOrders() {
        try {
            val response = gulaApi.getOrders(limit = 100)
            if (response.isSuccessful) {
                orderDao.insertAll(response.body()!!.items.map { it.toDomain().toEntity() })
            }
        } catch (_: Exception) { }
    }
}

private fun OrderResponseDto.toDomain() = Order(
    id = id,
    patientId = patientId,
    patientName = patientName,
    labId = labId,
    doctorName = doctorName,
    doctorUserId = doctorUserId,
    status = status,
    priority = priority,
    version = version ?: 1,
    visitId = visitId,
    createdAt = createdAt,
    updatedAt = updatedAt,
    results = results?.map { it.toDomain() } ?: emptyList(),
)

private fun ResultItemResponseDto.toDomain() = ResultItem(
    id = id,
    testName = testName,
    value = value,
    valueText = valueText,
    unit = unit,
    normalRangeLow = normalRangeLow,
    normalRangeHigh = normalRangeHigh,
    status = status,
    isCritical = isCritical,
    isAbnormal = isAbnormal,
    flag = flag,
    createdAt = createdAt,
)

private fun Order.toEntity() = OrderEntity(
    id = id,
    patientId = patientId,
    patientName = patientName,
    labId = labId,
    doctorName = doctorName,
    doctorUserId = doctorUserId,
    status = status,
    priority = priority,
    version = version,
    visitId = visitId,
    createdAt = createdAt,
    updatedAt = updatedAt,
)

private fun OrderEntity.toDomain() = Order(
    id = id,
    patientId = patientId,
    patientName = patientName,
    labId = labId,
    doctorName = doctorName,
    doctorUserId = doctorUserId,
    status = status,
    priority = priority,
    version = version,
    visitId = visitId,
    createdAt = createdAt,
    updatedAt = updatedAt,
)

private fun AnalyzeResponseDto.toDomain() = OrderIntelligence(
    orderId = 0,
    patternsDetected = patternsDetected,
    patterns = patterns.map { ClinicalPattern(it.pattern, it.severity, it.description, it.findings) },
    flagSummary = FlagSummary(flagSummary.total, flagSummary.high, flagSummary.low, flagSummary.critical, flagSummary.normal),
    hasCriticalPattern = hasCriticalPattern,
)

private fun OrderIntelligenceResponseDto.toDomain() = OrderIntelligence(
    orderId = orderId,
    patternsDetected = patternsDetected,
    patterns = patterns.map { ClinicalPattern(it.pattern, it.severity, it.description, it.findings) },
    flagSummary = FlagSummary(flagSummary.total, flagSummary.high, flagSummary.low, flagSummary.critical, flagSummary.normal),
    hasCriticalPattern = hasCriticalPattern,
)
