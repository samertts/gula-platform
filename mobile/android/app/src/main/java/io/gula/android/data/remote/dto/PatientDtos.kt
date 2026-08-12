package io.gula.android.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class PatientCreateRequestDto(
    @Json(name = "full_name") val fullName: String,
    @Json(name = "phone") val phone: String,
    @Json(name = "birth_date") val birthDate: String? = null,
    @Json(name = "gender") val gender: String? = null,
    @Json(name = "email") val email: String? = null,
    @Json(name = "national_id") val nationalId: String? = null,
    @Json(name = "family_id") val familyId: String? = null,
    @Json(name = "force_create") val forceCreate: Boolean = false,
    @Json(name = "guardian_id") val guardianId: Int? = null,
)

@JsonClass(generateAdapter = true)
data class PatientUpdateRequestDto(
    @Json(name = "full_name") val fullName: String? = null,
    @Json(name = "phone") val phone: String? = null,
    @Json(name = "birth_date") val birthDate: String? = null,
    @Json(name = "gender") val gender: String? = null,
    @Json(name = "email") val email: String? = null,
    @Json(name = "family_id") val familyId: String? = null,
)

@JsonClass(generateAdapter = true)
data class PatientResponseDto(
    @Json(name = "id") val id: Int,
    @Json(name = "full_name") val fullName: String,
    @Json(name = "phone") val phone: String,
    @Json(name = "birth_date") val birthDate: String? = null,
    @Json(name = "gender") val gender: String? = null,
    @Json(name = "email") val email: String? = null,
    @Json(name = "lab_id") val labId: Int? = null,
    @Json(name = "national_id") val nationalId: String? = null,
    @Json(name = "health_id") val healthId: String? = null,
    @Json(name = "family_id") val familyId: String? = null,
    @Json(name = "guardian_id") val guardianId: Int? = null,
    @Json(name = "status") val status: String? = null,
    @Json(name = "created_at") val createdAt: String? = null,
    @Json(name = "updated_at") val updatedAt: String? = null,
)

@JsonClass(generateAdapter = true)
data class PatientListResponseDto(
    @Json(name = "items") val items: List<PatientResponseDto>,
    @Json(name = "total") val total: Int,
    @Json(name = "page") val page: Int = 1,
    @Json(name = "limit") val limit: Int = 20,
    @Json(name = "pages") val pages: Int = 1,
    @Json(name = "has_next") val hasNext: Boolean = false,
    @Json(name = "has_prev") val hasPrev: Boolean = false,
)

@JsonClass(generateAdapter = true)
data class PatientCardResponseDto(
    @Json(name = "token") val token: String,
    @Json(name = "expires_at") val expiresAt: String,
    @Json(name = "qr_data_url") val qrDataUrl: String? = null,
)

@JsonClass(generateAdapter = true)
data class ScanRequestDto(
    @Json(name = "token") val token: String,
)

@JsonClass(generateAdapter = true)
data class ScanResponseDto(
    @Json(name = "patient") val patient: PatientResponseDto,
    @Json(name = "card_issued_at") val cardIssuedAt: String,
    @Json(name = "card_expires_at") val cardExpiresAt: String,
)

@JsonClass(generateAdapter = true)
data class ConvertGuestRequestDto(
    @Json(name = "patient_id") val patientId: Int,
    @Json(name = "full_name") val fullName: String,
    @Json(name = "phone") val phone: String,
    @Json(name = "birth_date") val birthDate: String? = null,
    @Json(name = "gender") val gender: String? = null,
)
