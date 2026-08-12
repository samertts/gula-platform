package io.gula.sdk.models

import io.gula.sdk.MPIAction
import io.gula.sdk.MPIMatchLevel
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class MPIMatchRequest(
    @SerialName("full_name") val fullName: String,
    val phone: String? = null,
    @SerialName("birth_date") val birthDate: String? = null,
    val gender: String? = null,
    @SerialName("national_id_hash") val nationalIdHash: String? = null,
    @SerialName("family_id_hash") val familyIdHash: String? = null,
    @SerialName("lab_id") val labId: Int? = null,
)

@Serializable
data class MPIMatchResponse(
    val matches: List<MPICandidate>,
    @SerialName("match_level") val matchLevel: MPIMatchLevel,
    @SerialName("suggested_action") val suggestedAction: MPIAction,
)

@Serializable
data class MPICandidate(
    @SerialName("patient_id") val patientId: Int,
    @SerialName("full_name") val fullName: String,
    val phone: String,
    @SerialName("birth_date") val birthDate: String? = null,
    val gender: String? = null,
    val score: Double,
    @SerialName("lab_id") val labId: Int,
    @SerialName("lab_name") val labName: String? = null,
)

@Serializable
data class MPIMergeRequest(
    @SerialName("source_patient_id") val sourcePatientId: Int,
    @SerialName("target_patient_id") val targetPatientId: Int,
    val reason: String? = null,
)

@Serializable
data class MPIMergeResponse(
    @SerialName("survivor_patient_id") val survivorPatientId: Int,
    @SerialName("merged_orders") val mergedOrders: Int,
    @SerialName("merged_results") val mergedResults: Int,
    val message: String,
)

@Serializable
data class MPIDuplicateCheckRequest(
    @SerialName("full_name") val fullName: String,
    val phone: String,
    @SerialName("national_id") val nationalId: String? = null,
    @SerialName("lab_id") val labId: Int? = null,
)

@Serializable
data class MPIDuplicateCheckResponse(
    @SerialName("is_duplicate") val isDuplicate: Boolean,
    val matches: List<MPICandidate>,
    val confidence: Double,
)

@Serializable
data class MPILinkRequest(
    @SerialName("global_patient_id") val globalPatientId: String,
    @SerialName("local_patient_id") val localPatientId: Int,
    @SerialName("lab_id") val labId: Int,
)

@Serializable
data class MPILinkResponse(
    val linked: Boolean,
    @SerialName("link_id") val linkId: Int? = null,
    val message: String,
)
