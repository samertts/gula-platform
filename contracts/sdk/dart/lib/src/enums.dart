enum Gender { m, f }

enum LabType { private, government, hospital, clinic }

enum OrderStatus { pending, completed, validated, cancelled }

enum ResultFlag { h, l, normal, critical }

enum SampleStatus { collected, received, processing, analyzed, rejected }

enum SampleType { blood, urine, stool, swab, serum, plasma }

enum ClaimStatus { draft, validated, submitted, accepted, rejected, paid }

enum ConsentStatus { active, revoked, expired, pending, enteredInError }

enum EdgeDeviceStatus { pending, active, quarantined, revoked, offline }

enum EdgeRoleMode { personal, clinic, enterprise }

enum EdgeTaskStatus { pending, dispatched, running, completed, failed, cancelled, expired }

enum EdgeTaskPrivacy { standard, sensitive, phi }

enum EdgeModelStatus { draft, canary, active, retired, blocked }

enum EdgeEventSeverity { info, warning, error, critical }

enum QcLevel { low, normal, high }

enum QcStatus { pass, warning, fail }

enum WestgardRule { one2s, one3s, two2s, r4s, four1s, tenX }

enum UserRole {
  masterAdmin,
  labAdmin,
  labStaff,
  doctor,
  citizen,
}

enum DeploymentMode { single, multiBranch, government }

enum SecurityLevel { standard, highSecurity, airGapped }

enum BillingCycle { monthly, yearly }

enum SubscriptionTier { starter, growth, enterprise }

enum LicenseStatus { active, expired, suspended, revoked, pending }

enum SubStatus { pending, approved, rejected, fulfilled }

enum NotificationChannel { email, sms, push, telegram }

enum AppointmentStatus { proposed, pending, booked, arrived, inProgress, completed, cancelled, noShow, enteredInError }

enum IdentityType { iraqiCitizen, newborn, foreigner, resident, visitor, unknownPatient }

enum IdentityStatus { active, merged, deceased, inactive, suspended, pendingVerification, pendingMerge }

enum MatchMethod { nidExact, probabilistic, manual, pendingReview }

enum MergeEventType { autoMerge, manualMerge, split, reassign, create }

enum AuditAction { view, create, update, delete }

enum AiRiskLevel { low, medium, high, critical }

enum AiInteractionStatus { ok, error, filtered }

enum AiGuardrailType { promptInjection, hallucination, bias, safety, privacy, clinicalValidation }

enum TestResultStatus { pending, completed, verified, rejected }

enum AbnormalityDirection { high, low, normal }

enum FeatureFlagEntityType { lab, user, global }

enum OrgType { ministry, directorate, hospital, clinic, laboratory, pharmacy, insurance, research, other }

enum GovernanceNodeType { republic, ministry, directorate, hospital, primaryHealthcareCenter, specializedCenter, laboratory, department, unit, employee }

enum DataClassificationLevel { public, internal, confidential, restricted, topSecret }

enum InteropProtocolType { fhir, hl7, dicom, openapi, graphql, rest, grpc, mqtt, amqp, eventBus, ihe }
