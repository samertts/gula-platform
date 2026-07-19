package io.gula.android.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class SampleCreateRequestDto(
    @Json(name = "order_id") val orderId: Int,
    @Json(name = "sample_type") val sampleType: String,
    @Json(name = "collected_by") val collectedBy: String? = null,
    @Json(name = "notes") val notes: String? = null,
    @Json(name = "storage_location") val storageLocation: String? = null,
)

@JsonClass(generateAdapter = true)
data class SampleUpdateRequestDto(
    @Json(name = "status") val status: String? = null,
    @Json(name = "rejection_reason") val rejectionReason: String? = null,
    @Json(name = "notes") val notes: String? = null,
    @Json(name = "storage_location") val storageLocation: String? = null,
)

@JsonClass(generateAdapter = true)
data class SampleResponseDto(
    @Json(name = "id") val id: Int,
    @Json(name = "barcode") val barcode: String,
    @Json(name = "order_id") val orderId: Int,
    @Json(name = "sample_type") val sampleType: String,
    @Json(name = "status") val status: String = "collected",
    @Json(name = "collected_by") val collectedBy: String? = null,
    @Json(name = "collection_time") val collectionTime: String? = null,
    @Json(name = "rejection_reason") val rejectionReason: String? = null,
    @Json(name = "notes") val notes: String? = null,
    @Json(name = "storage_location") val storageLocation: String? = null,
    @Json(name = "created_at") val createdAt: String? = null,
    @Json(name = "updated_at") val updatedAt: String? = null,
)

@JsonClass(generateAdapter = true)
data class SampleListResponseDto(
    @Json(name = "items") val items: List<SampleResponseDto>,
    @Json(name = "total") val total: Int,
    @Json(name = "page") val page: Int = 1,
    @Json(name = "limit") val limit: Int = 20,
)
