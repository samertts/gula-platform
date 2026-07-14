package io.gula.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class GrantRequest(
    val gpid: String,
    @SerialName("grantee_id") val granteeId: String,
    val scope: String,
    @SerialName("expires_in_hours") val expiresInHours: Int,
)

@Serializable
data class GrantResponse(
    @SerialName("consent_id") val consentId: String,
    val gpid: String,
    @SerialName("grantee_id") val granteeId: String,
    val scope: String,
    @SerialName("expires_at") val expiresAt: String,
)

@Serializable
data class RevokeRequest(
    val gpid: String,
    @SerialName("grantee_id") val granteeId: String,
    val scope: String,
)

@Serializable
data class RevokeResponse(
    val revoked: Boolean,
)

@Serializable
data class CheckRequest(
    val gpid: String? = null,
    @SerialName("grantee_id") val granteeId: String? = null,
    val scope: String,
)

@Serializable
data class CheckResponse(
    val allowed: Boolean,
    val scope: String,
    @SerialName("expires_at") val expiresAt: String? = null,
)
