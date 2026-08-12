package io.gula.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ClaimItemCreate(
    @SerialName("test_code") val testCode: String,
    val description: String? = null,
    val quantity: Int = 1,
    @SerialName("unit_price") val unitPrice: Double,
    val amount: Double,
)

@Serializable
data class ClaimCreate(
    @SerialName("patient_id") val patientId: Int,
    @SerialName("order_id") val orderId: Int? = null,
    val items: List<ClaimItemCreate>,
    @SerialName("idempotency_key") val idempotencyKey: String? = null,
)

@Serializable
data class ClaimItemResponse(
    val id: Int,
    @SerialName("claim_id") val claimId: Int,
    @SerialName("test_code") val testCode: String,
    val description: String? = null,
    val quantity: Int,
    @SerialName("unit_price") val unitPrice: Double,
    val amount: Double,
)

@Serializable
data class ClaimResponse(
    val id: Int,
    @SerialName("lab_id") val labId: Int,
    @SerialName("patient_id") val patientId: Int,
    @SerialName("order_id") val orderId: Int? = null,
    val status: String,
    @SerialName("total_amount") val totalAmount: Double? = null,
    val currency: String = "IQD",
    @SerialName("idempotency_key") val idempotencyKey: String? = null,
    @SerialName("external_ref") val externalRef: String? = null,
    @SerialName("submitted_at") val submittedAt: String? = null,
    @SerialName("created_at") val createdAt: String? = null,
    @SerialName("updated_at") val updatedAt: String? = null,
    val items: List<ClaimItemResponse>,
)

@Serializable
data class ClaimValidateResponse(
    val message: String,
    @SerialName("claim_id") val claimId: Int,
    val status: String,
)

@Serializable
data class ClaimSubmitResponse(
    val message: String,
    @SerialName("claim_id") val claimId: Int,
    val status: String,
    @SerialName("external_ref") val externalRef: String? = null,
    @SerialName("submitted_at") val submittedAt: String? = null,
)
