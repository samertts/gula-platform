package io.gula.sdk.models

import io.gula.sdk.SampleStatus
import io.gula.sdk.SampleType
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class SampleCreate(
    @SerialName("order_id") val orderId: Int,
    @SerialName("sample_type") val sampleType: String,
    @SerialName("collected_by") val collectedBy: String? = null,
    val notes: String? = null,
    @SerialName("storage_location") val storageLocation: String? = null,
)

@Serializable
data class SampleUpdate(
    val status: String? = null,
    @SerialName("rejection_reason") val rejectionReason: String? = null,
    val notes: String? = null,
    @SerialName("storage_location") val storageLocation: String? = null,
)

@Serializable
data class SampleResponse(
    val id: Int,
    val barcode: String,
    @SerialName("order_id") val orderId: Int,
    @SerialName("sample_type") val sampleType: String,
    val status: SampleStatus,
    @SerialName("collected_by") val collectedBy: String? = null,
    @SerialName("collection_time") val collectionTime: String? = null,
    @SerialName("rejection_reason") val rejectionReason: String? = null,
    val notes: String? = null,
    @SerialName("storage_location") val storageLocation: String? = null,
    @SerialName("created_at") val createdAt: String? = null,
)

@Serializable
data class SampleListResponse(
    val total: Int,
    val samples: List<SampleResponse>,
)

@Serializable
data class SampleCreateResponse(
    val message: String,
    val sample: SampleResponse,
)

@Serializable
data class SampleUpdateResponse(
    val message: String,
    val sample: SampleResponse,
)
