package io.gula.sdk

import kotlinx.serialization.Serializable

@Serializable
enum class Gender {
    M, F;

    companion object {
        fun fromString(s: String): Gender = when (s.lowercase()) {
            "male", "m" -> M
            "female", "f" -> F
            else -> throw IllegalArgumentException("Unknown gender: $s")
        }
    }
}

@Serializable
enum class LabType {
    private, government, hospital, clinic
}

@Serializable
enum class LabUserRole {
    master_admin, ministry_admin, province_admin, admin, lab_admin, doctor, staff, lab_staff, technician, citizen
}

@Serializable
enum class OrderStatus {
    pending, completed, validated, cancelled
}

@Serializable
enum class SampleStatus {
    collected, received, processing, analyzed, rejected
}

@Serializable
enum class SampleType {
    blood, urine, stool, swab, serum, plasma, csf, sputum, other
}

@Serializable
enum class ClaimStatus {
    draft, validated, submitted, accepted, rejected, paid
}

@Serializable
enum class ConsentStatus {
    active, revoked, expired
}

@Serializable
enum class EdgeDeviceStatus {
    pending, active, quarantined, revoked, offline
}

@Serializable
enum class EdgeDeviceRole {
    personal, clinic, enterprise
}

@Serializable
enum class EdgeTaskStatus {
    pending, dispatched, running, completed, failed, cancelled, expired
}

@Serializable
enum class EdgeTaskPrivacy {
    standard, sensitive, phi
}

@Serializable
enum class EdgeModelStatus {
    draft, canary, active, retired, blocked
}

@Serializable
enum class EdgeEventSeverity {
    debug, info, warning, error, critical
}

@Serializable
enum class SubscriptionTier {
    starter, growth, enterprise
}

@Serializable
enum class DeploymentMode {
    single, multi_branch, government
}

@Serializable
enum class SecurityLevel {
    standard, high_security, air_gapped
}

@Serializable
enum class BillingCycle {
    monthly, yearly
}

@Serializable
enum class UpgradeRequestStatus {
    pending, approved, rejected, fulfilled
}

@Serializable
enum class AIStatus {
    ok, error, timeout, blocked
}

@Serializable
enum class AIRiskLevel {
    low_risk, medium_risk, high_risk
}

@Serializable
enum class AIFeedbackSignal {
    positive, negative, neutral, inappropriate, harmful
}

@Serializable
enum class AIQuestionStatus {
    open, answered, escalated, closed
}

@Serializable
enum class OrganizationType {
    hospital, clinic, laboratory, pharmacy, ministry, insurance, research, other
}

@Serializable
enum class FacilityType {
    main_branch, sub_branch, mobile_unit, collection_center, reference_lab, other
}

@Serializable
enum class AppointmentStatus {
    scheduled, confirmed, in_progress, completed, cancelled, no_show
}

@Serializable
enum class AuditAction {
    view, create, update, delete, login, login_failed, login_denied, logout, export
}

@Serializable
enum class ConsentScope {
    results_read, results_write, demographics_read, demographics_write, full_access
}

@Serializable
enum class IdentifierType {
    national_id, passport, driver_license, health_id, citizen_ulid, other
}

@Serializable
enum class TestResultFlag {
    H, L, normal, critical
}

@Serializable
enum class MPIMatchLevel {
    exact, high, medium, low, none
}

@Serializable
enum class MPIAction {
    auto_merge, suggest_merge, flag_review, no_action
}
