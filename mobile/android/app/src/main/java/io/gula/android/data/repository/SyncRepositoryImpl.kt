package io.gula.android.data.repository

import io.gula.android.data.local.dao.SyncQueueDao
import io.gula.android.data.local.entity.SyncQueueEntity
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.*
import io.gula.android.domain.model.SyncAction
import io.gula.android.domain.model.SyncStatus
import io.gula.android.domain.repository.SyncRepository
import io.gula.android.security.EncryptedPrefs
import io.gula.android.security.SecurePayloadCodec
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import retrofit2.Response
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SyncRepositoryImpl @Inject constructor(
    private val syncQueueDao: SyncQueueDao,
    private val gulaApi: GulaApi,
    private val encryptedPrefs: EncryptedPrefs,
    private val payloadCodec: SecurePayloadCodec,
) : SyncRepository {

    private val _syncStatus = MutableStateFlow(SyncStatus())
    override val syncStatus: Flow<SyncStatus> = _syncStatus.asStateFlow()

    override suspend fun enqueue(
        entityType: String,
        entityId: String?,
        action: SyncAction,
        payload: String,
    ) {
        check(encryptedPrefs.syncDeviceId.isNotBlank()) { "Sync device identity is unavailable" }
        syncQueueDao.insert(
            SyncQueueEntity(
                entityType = entityType,
                entityId = entityId,
                action = action.name,
                payload = payloadCodec.encrypt(payload),
            )
        )
        updateStatus()
    }

    override suspend fun processQueue(): SyncStatus {
        check(encryptedPrefs.syncDeviceId.isNotBlank()) { "Sync device identity is unavailable" }
        syncQueueDao.recoverInProgress()
        _syncStatus.value = _syncStatus.value.copy(isSyncing = true, errorMessage = null)
        var failed = 0
        var lastCompletedId: Long? = null

        try {
            val storedItems = syncQueueDao.getPendingItems(50)
            for (storedItem in storedItems) {
                val item = secureItem(storedItem)
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
                    lastCompletedId = item.id
                } catch (error: Exception) {
                    if (error is RetryableSyncException || error is IOException) {
                        syncQueueDao.markDeferred(item.id, error.message?.take(500))
                    } else {
                        failed++
                        syncQueueDao.markFailed(item.id, error = error.message?.take(500) ?: "Unknown sync error")
                    }
                }
            }
        } catch (error: Exception) {
            _syncStatus.value = _syncStatus.value.copy(
                isSyncing = false,
                errorMessage = error.message?.take(500),
                pendingCount = syncQueueDao.getPendingCountOnce(),
                failedCount = syncQueueDao.getFailedCountOnce(),
                deferredCount = syncQueueDao.getDeferredCountOnce(),
            )
            return _syncStatus.value
        }

        if (lastCompletedId != null) encryptedPrefs.syncCursor = lastCompletedId.toString()
        val status = SyncStatus(
            isSyncing = false,
            lastSyncTime = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).format(Date()),
            pendingCount = syncQueueDao.getPendingCountOnce(),
            failedCount = syncQueueDao.getFailedCountOnce(),
            deferredCount = syncQueueDao.getDeferredCountOnce(),
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
            deferredCount = syncQueueDao.getDeferredCountOnce(),
        )
    }

    private suspend fun secureItem(item: SyncQueueEntity): SyncQueueEntity {
        if (payloadCodec.isEncrypted(item.payload)) {
            return item.copy(payload = payloadCodec.decrypt(item.payload))
        }
        // One-way migration for payloads created before encryption was enabled.
        syncQueueDao.updatePayload(item.id, payloadCodec.encrypt(item.payload))
        return item
    }

    private fun Response<*>.ensureSuccessful() {
        if (isSuccessful) return
        val message = "Sync request rejected by server (HTTP ${code()})"
        if (code() == 408 || code() == 429 || code() >= 500) throw RetryableSyncException(message)
        throw IllegalStateException(message)
    }

    private class RetryableSyncException(message: String) : IOException(message)

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
        ).ensureSuccessful()
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
        ).ensureSuccessful()
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
        ).ensureSuccessful()
    }

    private suspend fun syncUpdateOrder(item: SyncQueueEntity) {
        // Contract not yet exposed by GulaApi; keep the item pending in future work rather than claiming success.
        throw IllegalStateException("UPDATE_ORDER sync contract is not implemented")
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
        ).ensureSuccessful()
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
        ).ensureSuccessful()
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
        ).ensureSuccessful()
    }

    private suspend fun syncUpdateResult(item: SyncQueueEntity) {
        throw IllegalStateException("UPDATE_RESULT sync contract is not implemented")
    }
}
