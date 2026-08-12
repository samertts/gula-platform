package io.gula.sdk.models

import io.gula.sdk.BillingCycle
import io.gula.sdk.DeploymentMode
import io.gula.sdk.SecurityLevel
import io.gula.sdk.SubscriptionTier
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class TierInfo(
    val id: String,
    val name: String,
    @SerialName("name_ar") val nameAr: String,
    @SerialName("monthly_price_usd") val monthlyPriceUsd: Double,
    val limits: TierLimits,
    val features: List<String>,
)

@Serializable
data class TierLimits(
    @SerialName("max_patients") val maxPatients: Int,
    @SerialName("max_staff") val maxStaff: Int,
    @SerialName("max_branches") val maxBranches: Int,
    @SerialName("max_orders_per_day") val maxOrdersPerDay: Int,
    @SerialName("max_ai_calls_per_day") val maxAiCallsPerDay: Int,
)

@Serializable
data class TierListResponse(
    val tiers: List<TierInfo>,
)

@Serializable
data class SubscriptionInfoResponse(
    val tier: SubscriptionTier,
    @SerialName("deployment_mode") val deploymentMode: DeploymentMode = DeploymentMode.single,
    @SerialName("security_level") val securityLevel: SecurityLevel = SecurityLevel.standard,
    @SerialName("is_trial") val isTrial: Boolean = false,
    @SerialName("trial_ends_at") val trialEndsAt: String? = null,
    @SerialName("billing_cycle") val billingCycle: BillingCycle = BillingCycle.monthly,
    @SerialName("max_patients") val maxPatients: Int = 500,
    @SerialName("max_staff") val maxStaff: Int = 5,
    @SerialName("max_branches") val maxBranches: Int = 1,
    @SerialName("max_orders_per_day") val maxOrdersPerDay: Int = 100,
    @SerialName("max_ai_calls_per_day") val maxAiCallsPerDay: Int = 0,
    val features: List<String>,
    @SerialName("expires_at") val expiresAt: String? = null,
)

@Serializable
data class UpgradeRequest(
    @SerialName("target_tier") val targetTier: SubscriptionTier,
    @SerialName("target_deployment_mode") val targetDeploymentMode: DeploymentMode? = null,
    @SerialName("target_security_level") val targetSecurityLevel: SecurityLevel? = null,
    val reason: String? = null,
)

@Serializable
data class UpgradeResponse(
    val message: String,
    @SerialName("request_id") val requestId: Int,
    val status: String = "pending",
)

@Serializable
data class UpgradeDemandRequest(
    @SerialName("target_tier") val targetTier: SubscriptionTier,
    @SerialName("target_deployment_mode") val targetDeploymentMode: String? = null,
    @SerialName("target_security_level") val targetSecurityLevel: String? = null,
    val reason: String? = null,
)

@Serializable
data class UpgradeRequestResponse(
    val id: Int,
    @SerialName("lab_id") val labId: Int,
    @SerialName("target_tier") val targetTier: String,
    @SerialName("target_deployment_mode") val targetDeploymentMode: String? = null,
    @SerialName("target_security_level") val targetSecurityLevel: String? = null,
    val reason: String? = null,
    val status: String,
    @SerialName("weight") val weight: Double = 1.0,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class UpgradeDemandResponse(
    val labs: List<UpgradeDemandLab>,
)

@Serializable
data class UpgradeDemandLab(
    @SerialName("lab_id") val labId: Int,
    @SerialName("lab_name") val labName: String,
    @SerialName("raw_score") val rawScore: Double,
    @SerialName("unique_requesters") val uniqueRequesters: Int,
    @SerialName("weighted_score") val weightedScore: Double,
)

@Serializable
data class AdminSetTierRequest(
    val tier: SubscriptionTier,
    @SerialName("deployment_mode") val deploymentMode: DeploymentMode? = null,
    @SerialName("security_level") val securityLevel: SecurityLevel? = null,
)

@Serializable
data class FeatureFlagRequest(
    @SerialName("feature_key") val featureKey: String,
    @SerialName("is_enabled") val isEnabled: Boolean = true,
    val reason: String? = null,
    @SerialName("expires_at") val expiresAt: String? = null,
)

@Serializable
data class FeatureFlagResponse(
    val id: Int,
    @SerialName("lab_id") val labId: Int,
    @SerialName("feature_key") val featureKey: String,
    @SerialName("is_enabled") val isEnabled: Boolean,
    val reason: String? = null,
    @SerialName("expires_at") val expiresAt: String? = null,
    @SerialName("created_at") val createdAt: String,
)
