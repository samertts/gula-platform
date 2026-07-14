import 'package:json_annotation/json_annotation.dart';
import '../enums.dart';

part 'subscription.g.dart';

@JsonSerializable()
class LabSubscription {
  final int id;
  final int labId;
  final SubscriptionTier tier;
  final DeploymentMode deploymentMode;
  final SecurityLevel securityLevel;
  final bool isActive;
  final DateTime? trialEndsAt;
  final BillingCycle billingCycle;
  final double monthlyPriceUsd;
  final int maxPatients;
  final int maxStaff;
  final int maxBranches;
  final int maxOrdersPerDay;
  final int maxAiCallsPerDay;
  final String? notes;
  final DateTime? activatedAt;
  final DateTime? expiresAt;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const LabSubscription({
    required this.id,
    required this.labId,
    required this.tier,
    required this.deploymentMode,
    required this.securityLevel,
    required this.isActive,
    this.trialEndsAt,
    this.billingCycle = BillingCycle.monthly,
    this.monthlyPriceUsd = 0.0,
    this.maxPatients = 500,
    this.maxStaff = 5,
    this.maxBranches = 1,
    this.maxOrdersPerDay = 100,
    this.maxAiCallsPerDay = 0,
    this.notes,
    this.activatedAt,
    this.expiresAt,
    this.createdAt,
    this.updatedAt,
  });

  factory LabSubscription.fromJson(Map<String, dynamic> json) =>
      _$LabSubscriptionFromJson(json);
  Map<String, dynamic> toJson() => _$LabSubscriptionToJson(this);
}

@JsonSerializable()
class TierMatrix {
  final String tier;
  final int maxPatients;
  final int maxStaff;
  final int maxBranches;
  final int maxOrdersPerDay;
  final int maxAiCallsPerDay;
  final double monthlyPriceUsd;
  final List<String> features;

  const TierMatrix({
    required this.tier,
    required this.maxPatients,
    required this.maxStaff,
    required this.maxBranches,
    required this.maxOrdersPerDay,
    required this.maxAiCallsPerDay,
    required this.monthlyPriceUsd,
    required this.features,
  });

  factory TierMatrix.fromJson(Map<String, dynamic> json) => _$TierMatrixFromJson(json);
  Map<String, dynamic> toJson() => _$TierMatrixToJson(this);
}

@JsonSerializable()
class UpgradeRequest {
  final int id;
  final int labId;
  final int? requesterId;
  final String targetTier;
  final String? targetDeploymentMode;
  final String? targetSecurityLevel;
  final String? reason;
  final SubStatus status;
  final double weight;
  final int? reviewedBy;
  final DateTime? reviewedAt;
  final String? reviewNote;
  final DateTime? createdAt;

  const UpgradeRequest({
    required this.id,
    required this.labId,
    this.requesterId,
    required this.targetTier,
    this.targetDeploymentMode,
    this.targetSecurityLevel,
    this.reason,
    required this.status,
    this.weight = 1.0,
    this.reviewedBy,
    this.reviewedAt,
    this.reviewNote,
    this.createdAt,
  });

  factory UpgradeRequest.fromJson(Map<String, dynamic> json) => _$UpgradeRequestFromJson(json);
  Map<String, dynamic> toJson() => _$UpgradeRequestToJson(this);
}

@JsonSerializable()
class UpgradeDemandScore {
  final int labId;
  final double rawScore;
  final int uniqueRequesters;
  final double weightedScore;
  final DateTime? lastRequestAt;
  final DateTime? updatedAt;

  const UpgradeDemandScore({
    required this.labId,
    required this.rawScore,
    required this.uniqueRequesters,
    required this.weightedScore,
    this.lastRequestAt,
    this.updatedAt,
  });

  factory UpgradeDemandScore.fromJson(Map<String, dynamic> json) =>
      _$UpgradeDemandScoreFromJson(json);
  Map<String, dynamic> toJson() => _$UpgradeDemandScoreToJson(this);
}

@JsonSerializable()
class FeatureFlag {
  final int id;
  final int labId;
  final String featureKey;
  final bool isEnabled;
  final String? reason;
  final int? setBy;
  final DateTime? expiresAt;
  final DateTime? createdAt;

  const FeatureFlag({
    required this.id,
    required this.labId,
    required this.featureKey,
    required this.isEnabled,
    this.reason,
    this.setBy,
    this.expiresAt,
    this.createdAt,
  });

  factory FeatureFlag.fromJson(Map<String, dynamic> json) => _$FeatureFlagFromJson(json);
  Map<String, dynamic> toJson() => _$FeatureFlagToJson(this);
}

@JsonSerializable()
class TierUpgradeRequest {
  final String targetTier;
  final String? targetDeploymentMode;
  final String? targetSecurityLevel;
  final String? reason;

  const TierUpgradeRequest({
    required this.targetTier,
    this.targetDeploymentMode,
    this.targetSecurityLevel,
    this.reason,
  });

  factory TierUpgradeRequest.fromJson(Map<String, dynamic> json) =>
      _$TierUpgradeRequestFromJson(json);
  Map<String, dynamic> toJson() => _$TierUpgradeRequestToJson(this);
}
