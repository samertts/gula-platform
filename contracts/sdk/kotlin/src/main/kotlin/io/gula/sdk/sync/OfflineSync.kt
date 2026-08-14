package io.gula.sdk.sync

import io.gula.sdk.GulaClient
import io.gula.sdk.GulaNetworkException
import io.gula.sdk.models.*
import kotlinx.coroutines.*
import kotlinx.serialization.KSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.slf4j.LoggerFactory
import java.io.File
import java.nio.file.Path
import java.time.Instant
import java.util.*
import java.util.concurrent.ConcurrentLinkedQueue

class OfflineSync(
    private val client: GulaClient,
    private val storagePath: Path = Path.of(System.getProperty("user.home"), ".gula", "offline_queue"),
    private val maxRetriesPerItem: Int = 5,
    private val syncIntervalMs: Long = 30_000L,
) {
    private val log = LoggerFactory.getLogger(OfflineSync::class.java)
    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }
    private val queue = ConcurrentLinkedQueue<QueuedOperation>()
    private var syncJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    init {
        storagePath.toFile().mkdirs()
        loadPersistedQueue()
    }

    fun startAutoSync() {
        if (syncJob?.isActive == true) return
        syncJob = scope.launch {
            while (isActive) {
                try {
                    processQueue()
                } catch (e: Exception) {
                    log.error("Auto-sync cycle failed", e)
                }
                delay(syncIntervalMs)
            }
        }
        log.info("Auto-sync started (interval=${syncIntervalMs}ms)")
    }

    fun stopAutoSync() {
        syncJob?.cancel()
        syncJob = null
        log.info("Auto-sync stopped")
    }

    suspend fun syncNow() {
        processQueue()
    }

    fun enqueueCreatePatient(request: PatientCreate) {
        enqueue(QueuedOperation(
            id = UUID.randomUUID().toString(),
            type = OperationType.CREATE_PATIENT,
            payload = json.encodeToString(request),
            createdAt = Instant.now(),
        ))
    }

    fun enqueueUpdatePatient(patientId: Int, request: PatientUpdate) {
        enqueue(QueuedOperation(
            id = UUID.randomUUID().toString(),
            type = OperationType.UPDATE_PATIENT,
            resourceId = patientId.toString(),
            payload = json.encodeToString(request),
            createdAt = Instant.now(),
        ))
    }

    fun enqueueCreateOrder(request: CreateOrderRequest) {
        enqueue(QueuedOperation(
            id = UUID.randomUUID().toString(),
            type = OperationType.CREATE_ORDER,
            payload = json.encodeToString(request),
            createdAt = Instant.now(),
        ))
    }

    fun enqueueCreateSample(request: SampleCreate) {
        enqueue(QueuedOperation(
            id = UUID.randomUUID().toString(),
            type = OperationType.CREATE_SAMPLE,
            payload = json.encodeToString(request),
            createdAt = Instant.now(),
        ))
    }

    fun enqueueUpdateSample(barcode: String, request: SampleUpdate) {
        enqueue(QueuedOperation(
            id = UUID.randomUUID().toString(),
            type = OperationType.UPDATE_SAMPLE,
            resourceId = barcode,
            payload = json.encodeToString(request),
            createdAt = Instant.now(),
        ))
    }

    fun enqueueCreateClaim(request: ClaimCreate) {
        enqueue(QueuedOperation(
            id = UUID.randomUUID().toString(),
            type = OperationType.CREATE_CLAIM,
            payload = json.encodeToString(request),
            createdAt = Instant.now(),
        ))
    }

    fun enqueueSubmitDeviceResult(request: DeviceSubmission) {
        enqueue(QueuedOperation(
            id = UUID.randomUUID().toString(),
            type = OperationType.SUBMIT_DEVICE_RESULT,
            payload = json.encodeToString(request),
            createdAt = Instant.now(),
        ))
    }

    fun getQueueDepth(): Int = queue.size

    fun getPendingOperations(): List<QueuedOperation> = queue.toList()

    private fun enqueue(operation: QueuedOperation) {
        queue.offer(operation)
        persistQueue()
        log.debug("Enqueued operation: ${operation.type} (${operation.id})")
    }

    private suspend fun processQueue() {
        if (queue.isEmpty()) return

        val batch = queue.toList()
        var processed = 0

        for (op in batch) {
            if (op.retryCount >= maxRetriesPerItem) {
                queue.remove(op)
                log.warn("Dropping operation ${op.id} after $maxRetriesPerItem retries")
                continue
            }

            try {
                executeOperation(op)
                queue.remove(op)
                processed++
                log.info("Synced operation: ${op.type} (${op.id})")
            } catch (e: GulaNetworkException) {
                incrementRetry(op)
                log.warn("Network error syncing ${op.id}, will retry: ${e.message}")
            } catch (e: Exception) {
                queue.remove(op)
                log.error("Permanent failure syncing ${op.id}, dropping: ${e.message}")
            }
        }

        if (processed > 0) {
            persistQueue()
        }
    }

    private suspend fun executeOperation(op: QueuedOperation) {
        @Suppress("UNCHECKED_CAST")
        when (op.type) {
            OperationType.CREATE_PATIENT -> {
                val req = json.decodeFromString<PatientCreate>(op.payload)
                client.createPatient(req)
            }
            OperationType.UPDATE_PATIENT -> {
                val req = json.decodeFromString<PatientUpdate>(op.payload)
                val id = op.resourceId?.toIntOrNull()
                if (id != null) client.updatePatient(id, req)
                else throw IllegalArgumentException("Missing patient ID for UPDATE_PATIENT")
            }
            OperationType.CREATE_ORDER -> {
                val req = json.decodeFromString<CreateOrderRequest>(op.payload)
                client.createOrder(req)
            }
            OperationType.CREATE_SAMPLE -> {
                val req = json.decodeFromString<SampleCreate>(op.payload)
                client.createSample(req)
            }
            OperationType.UPDATE_SAMPLE -> {
                val req = json.decodeFromString<SampleUpdate>(op.payload)
                val barcode = op.resourceId ?: throw IllegalArgumentException("Missing barcode for UPDATE_SAMPLE")
                client.updateSample(barcode, req)
            }
            OperationType.CREATE_CLAIM -> {
                val req = json.decodeFromString<ClaimCreate>(op.payload)
                client.createClaim(req)
            }
            OperationType.SUBMIT_DEVICE_RESULT -> {
                val req = json.decodeFromString<DeviceSubmission>(op.payload)
                client.submitDeviceResult(req)
            }
        }
    }

    private fun incrementRetry(op: QueuedOperation) {
        val updated = op.copy(retryCount = op.retryCount + 1)
        queue.remove(op)
        queue.offer(updated)
    }

    private fun persistQueue() {
        try {
            val file = storagePath.resolve("queue.json").toFile()
            val data = queue.toList()
            if (data.isEmpty()) {
                file.delete()
                return
            }
            file.writeText(json.encodeToString(data))
        } catch (e: Exception) {
            log.error("Failed to persist offline queue", e)
        }
    }

    private fun loadPersistedQueue() {
        try {
            val file = storagePath.resolve("queue.json").toFile()
            if (!file.exists()) return
            val data = json.decodeFromString<List<QueuedOperation>>(file.readText())
            queue.addAll(data)
            log.info("Loaded ${data.size} pending operations from offline queue")
        } catch (e: Exception) {
            log.warn("Failed to load persisted offline queue (corrupted?), starting fresh", e)
        }
    }
}

@Serializable
enum class OperationType {
    CREATE_PATIENT,
    UPDATE_PATIENT,
    CREATE_ORDER,
    CREATE_SAMPLE,
    UPDATE_SAMPLE,
    CREATE_CLAIM,
    SUBMIT_DEVICE_RESULT,
}

private object InstantIsoSerializer : KSerializer<Instant> {
    override val descriptor: SerialDescriptor = PrimitiveSerialDescriptor("Instant", PrimitiveKind.STRING)

    override fun serialize(encoder: Encoder, value: Instant) = encoder.encodeString(value.toString())

    override fun deserialize(decoder: Decoder): Instant = Instant.parse(decoder.decodeString())
}

@Serializable
data class QueuedOperation(
    val id: String,
    val type: OperationType,
    val resourceId: String? = null,
    val payload: String,
    @Serializable(with = InstantIsoSerializer::class)
    val createdAt: Instant,
    val retryCount: Int = 0,
)
