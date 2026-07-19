package io.gula.android.domain.model

data class Sample(
    val id: Int,
    val barcode: String,
    val orderId: Int,
    val sampleType: String,
    val status: String = "collected",
    val collectedBy: String? = null,
    val collectionTime: String? = null,
    val rejectionReason: String? = null,
    val notes: String? = null,
    val storageLocation: String? = null,
    val createdAt: String? = null,
    val updatedAt: String? = null,
)

data class CreateSampleRequest(
    val orderId: Int,
    val sampleType: String,
    val collectedBy: String? = null,
    val notes: String? = null,
    val storageLocation: String? = null,
)

data class UpdateSampleRequest(
    val status: String? = null,
    val rejectionReason: String? = null,
    val notes: String? = null,
    val storageLocation: String? = null,
)
