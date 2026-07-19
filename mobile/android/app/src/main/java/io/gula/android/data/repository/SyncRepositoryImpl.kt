package io.gula.android.data.repository

import io.gula.android.data.local.dao.SyncQueueDao
import io.gula.android.data.local.entity.SyncQueueEntity
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.*
import io.gula.android.domain.model.SyncAction
import io.gula.android.domain.model.SyncStatus
import io.gula.android.domain.repository.SyncRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SyncRepositoryImpl @Inject constructor(
    private val syncQueueDao: SyncQueueDao,
    private val gulaApi: GulaApi,
) : SyncRepository {

    private val _syncStatus = MutableStateFlow(SyncStatus())
    override val syncStatus: Flow<SyncStatus> = _syncStatus.asStateFlow()

    override suspend fun enqueue(
        entityType: String,
        entityId: String?,
        action: SyncAction,
        payload: String,
    ) {
        syncQueueDao.insert(
            SyncQueueEntity(
                entityType = entityType,
                entityId = entityId,
                action = action.name,
                payload = payload,
            )
        )
        updateStatus()
    }

    override suspend fun processQueue(): SyncStatus {
        _syncStatus.value = _syncStatus.value.copy(isSyncing = true)
        var pending = 0
        var failed = 0

        try {
            val items = syncQueueDao.getPendingItems(50)
            pending = items.size

            for (item in items) {
                syncQueueDao.markInProgress(item.id)
                try {
                    when (item.action) {
                        "CREATE_PATIENT" -> syncCreatePatient(item)
                        "UPDATE_PATIENT" -> syncUpdatePatient(item)
                        "CREATE_ORDER" -> syncCreateOrder(item)
                        "UPDATE_ORDER" -> syncUpdateOrder(item)
                        "CREATE_SAMPLE" -> syncCreateSample(item)
                        "UPDATE_SAMPLE" -> syncUpdateSample(item)
                        "CREATE_RESULT" -> syncCreateResult(item)
                        "UPDATE_RESULT" -> syncUpdateResult(item)
                    }
                    syncQueueDao.markCompleted(item.id)
                } catch (e: Exception) {
                    failed++
                    syncQueueDao.markFailed(
                        item.id,
                        error = e.message?.take(500) ?: "Unknown error"
                    )
                }
            }
        } catch (e: Exception) {
            _syncStatus.value = _syncStatus.value.copy(
                isSyncing = false,
                errorMessage = e.message,
            )
            return _syncStatus.value
        }

        val newFailed = syncQueueDao.getFailedCountOnce()
        val status = SyncStatus(
            isSyncing = false,
            lastSyncTime = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).format(Date()),
            pendingCount = syncQueueDao.getPendingCountOnce(),
            failedCount = newFailed,
        )
        _syncStatus.value = status
        return status
    }

    override suspend fun getPendingCount(): Int = syncQueueDao.getPendingCountOnce()

    override suspend fun getFailedCount(): Int = syncQueueDao.getFailedCountOnce()

    override suspend fun retryFailed() {
        syncQueueDao.retryFailed()
        updateStatus()
    }

    override suspend fun clearCompleted() {
        syncQueueDao.deleteCompleted()
        syncQueueDao.deletePermanentlyFailed()
        updateStatus()
    }

    override suspend fun getLastSyncTime(): String? {
        val time = syncQueueDao.getLastSyncTime() ?: return null
        return SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).format(Date(time))
    }

    private suspend fun updateStatus() {
        _syncStatus.value = SyncStatus(
            pendingCount = syncQueueDao.getPendingCountOnce(),
            failedCount = syncQueueDao.getFailedCountOnce(),
        )
    }

    private suspend fun syncCreatePatient(item: SyncQueueEntity) {
        val json = JSONObject(item.payload)
        gulaApi.createPatient(
            PatientCreateRequestDto(
                fullName = json.getString("full_name"),
                phone = json.getString("phone"),
                birthDate = json.optString("birth_date", null).ifBlank { null },
                gender = json.optString("gender", null).ifBlank { null },
                email = json.optString("email", null).ifBlank { null },
            )
        )
    }

    private suspend fun syncUpdatePatient(item: SyncQueueEntity) {
        val json = JSONObject(item.payload)
        val id = item.entityId?.toIntOrNull() ?: return
        gulaApi.updatePatient(
            id,
            PatientUpdateRequestDto(
                fullName = json.optString("full_name", null).ifBlank { null },
                phone = json.optString("phone", null).ifBlank { null },
            )
        )
    }

    private suspend fun syncCreateOrder(item: SyncQueueEntity) {
        val json = JSONObject(item.payload)
        val resultsArray = json.getJSONArray("results")
        val results = mutableListOf<ResultItemDto>()
        for (i in 0 until resultsArray.length()) {
            val r = resultsArray.getJSONObject(i)
            results.add(
                ResultItemDto(
                    testName = r.getString("test_name"),
                    value = if (r.has("value")) r.optDouble("value") else null,
                    valueText = r.optString("value_text", null).ifBlank { null },
                    unit = r.optString("unit", null).ifBlank { null },
                )
            )
        }
        gulaApi.createOrder(
            CreateOrderRequestDto(
                patientId = json.getInt("patient_id"),
                doctorName = json.optString("doctor_name", null).ifBlank { null },
                results = results,
            )
        )
    }

    private suspend fun syncUpdateOrder(item: SyncQueueEntity) {
    }

    private suspend fun syncCreateSample(item: SyncQueueEntity) {
        val json = JSONObject(item.payload)
        gulaApi.createSample(
            SampleCreateRequestDto(
                orderId = json.getInt("order_id"),
                sampleType = json.getString("sample_type"),
                collectedBy = json.optString("collected_by", null).ifBlank { null },
                notes = json.optString("notes", null).ifBlank { null },
            )
        )
    }

    private suspend fun syncUpdateSample(item: SyncQueueEntity) {
        val json = JSONObject(item.payload)
        val barcode = item.entityId ?: return
        gulaApi.updateSample(
            barcode,
            SampleUpdateRequestDto(
                status = json.optString("status", null).ifBlank { null },
                rejectionReason = json.optString("rejection_reason", null).ifBlank { null },
                notes = json.optString("notes", null).ifBlank { null },
            )
        )
    }

    private suspend fun syncCreateResult(item: SyncQueueEntity) {
        val json = JSONObject(item.payload)
        gulaApi.createResult(
            TestResultCreateDto(
                testCode = json.getString("test_code"),
                testNameEn = json.getString("test_name_en"),
                testNameAr = json.optString("test_name_ar", json.getString("test_name_en")),
                resultValue = if (json.has("result_value")) json.optDouble("result_value") else null,
                resultText = json.optString("result_text", null).ifBlank { null },
                unit = json.optString("unit", null).ifBlank { null },
                status = json.optString("status", "pending"),
                orderId = if (json.has("order_id")) json.getInt("order_id") else null,
                sampleCollectedAt = json.optString("sample_collected_at", null),
            )
        )
    }

    private suspend fun syncUpdateResult(item: SyncQueueEntity) {
    }
}
