package io.gula.android.domain.repository

import io.gula.android.domain.model.*
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow

interface OrderRepository {
    fun getOrders(search: String? = null, page: Int = 1, limit: Int = 20): Flow<Resource<List<Order>>>
    fun getOrderById(id: Int): Flow<Resource<Order>>
    fun getOrdersByPatientId(patientId: Int): Flow<Resource<List<Order>>>
    suspend fun createOrder(request: CreateOrderRequest): Resource<Order>
    suspend fun cancelOrder(id: Int): Resource<Unit>
    suspend fun validateOrder(id: Int): Resource<Unit>
    suspend fun createBatchOrders(request: BatchOrderRequest): Resource<BatchOrderResult>
    suspend fun analyzeResults(items: List<ResultItemInput>): Resource<OrderIntelligence>
    suspend fun getOrderIntelligence(orderId: Int): Resource<OrderIntelligence>
    suspend fun refreshOrders()
}
