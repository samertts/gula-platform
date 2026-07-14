package io.gula.sdk.models

import io.gula.sdk.Gender
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PatientCreate(
    @SerialName("full_name") val fullName: String,
    val phone: String,
    @SerialName("birth_date") val birthDate: String? = null,
    val gender: String? = null,
    val email: String? = null,
    @SerialName("national_id") val nationalId: String? = null,
    @SerialName("family_id") val familyId: String? = null,
    @SerialName("force_create") val forceCreate: Boolean = false,
    @SerialName("guardian_id") val guardianId: Int? = null,
)

@Serializable
data class PatientUpdate(
    @SerialName("full_name") val fullName: String? = null,
    val phone: String? = null,
    @SerialName("birth_date") val birthDate: String? = null,
    val gender: String? = null,
    val email: String? = null,
    @SerialName("family_id") val familyId: String? = null,
)

@Serializable
data class PatientResponse(
    val id: Int,
    @SerialName("lab_id") val labId: Int,
    @SerialName("health_id") val healthId: String? = null,
    @SerialName("full_name") val fullName: String,
    val phone: String,
    @SerialName("birth_date") val birthDate: String? = null,
    val gender: Gender? = null,
    val email: String? = null,
    @SerialName("guardian_id") val guardianId: Int? = null,
    @SerialName("created_at") val createdAt: String? = null,
)

@Serializable
data class PatientListResponse(
    val total: Int,
    val patients: List<PatientResponse>,
)

@Serializable
data class PatientCardResponse(
    val token: String,
    @SerialName("expires_at") val expiresAt: String,
    @SerialName("qr_data_url") val qrDataUrl: String? = null,
)

@Serializable
data class ScanRequest(
    val token: String,
)

@Serializable
data class ScanResponse(
    val patient: PatientResponse,
    @SerialName("card_issued_at") val cardIssuedAt: String,
    @SerialName("card_expires_at") val cardExpiresAt: String,
)
