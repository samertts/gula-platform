import 'package:json_annotation/json_annotation.dart';

part 'mpi.g.dart';

@JsonSerializable()
class MpiResolveRequest {
  final int labId;
  final int patientId;
  final String name;
  final String? phone;
  final String? birthDate;
  final String? gender;
  final String? nationalId;
  final String? familyId;

  const MpiResolveRequest({
    required this.labId,
    required this.patientId,
    required this.name,
    this.phone,
    this.birthDate,
    this.gender,
    this.nationalId,
    this.familyId,
  });

  factory MpiResolveRequest.fromJson(Map<String, dynamic> json) =>
      _$MpiResolveRequestFromJson(json);
  Map<String, dynamic> toJson() => _$MpiResolveRequestToJson(this);
}

@JsonSerializable()
class MpiResolveResponse {
  final String citizenUlid;
  final String matchMethod;
  final double? matchScore;
  final bool created;
  final Map<String, dynamic> features;

  const MpiResolveResponse({
    required this.citizenUlid,
    required this.matchMethod,
    this.matchScore,
    required this.created,
    required this.features,
  });

  factory MpiResolveResponse.fromJson(Map<String, dynamic> json) =>
      _$MpiResolveResponseFromJson(json);
  Map<String, dynamic> toJson() => _$MpiResolveResponseToJson(this);
}

@JsonSerializable()
class CitizenResponse {
  final String citizenUlid;
  final bool nidVerified;
  final int? birthYear;
  final String? gender;
  final String status;
  final String? mergedIntoUlid;
  final DateTime? createdAt;

  const CitizenResponse({
    required this.citizenUlid,
    required this.nidVerified,
    this.birthYear,
    this.gender,
    required this.status,
    this.mergedIntoUlid,
    this.createdAt,
  });

  factory CitizenResponse.fromJson(Map<String, dynamic> json) =>
      _$CitizenResponseFromJson(json);
  Map<String, dynamic> toJson() => _$CitizenResponseToJson(this);
}

@JsonSerializable()
class MpiMergeRequest {
  final String primaryUlid;
  final String secondaryUlid;
  final String reason;

  const MpiMergeRequest({
    required this.primaryUlid,
    required this.secondaryUlid,
    required this.reason,
  });

  factory MpiMergeRequest.fromJson(Map<String, dynamic> json) =>
      _$MpiMergeRequestFromJson(json);
  Map<String, dynamic> toJson() => _$MpiMergeRequestToJson(this);
}

@JsonSerializable()
class MpiMergeResponse {
  final int eventId;
  final String primaryUlid;
  final String secondaryUlid;
  final DateTime occurredAt;
  final String entryHash;

  const MpiMergeResponse({
    required this.eventId,
    required this.primaryUlid,
    required this.secondaryUlid,
    required this.occurredAt,
    required this.entryHash,
  });

  factory MpiMergeResponse.fromJson(Map<String, dynamic> json) =>
      _$MpiMergeResponseFromJson(json);
  Map<String, dynamic> toJson() => _$MpiMergeResponseToJson(this);
}

@JsonSerializable()
class PendingReviewItem {
  final int claimId;
  final String citizenUlid;
  final int labId;
  final int localPatientId;
  final double? matchScore;
  final Map<String, dynamic> matchFeatures;
  final DateTime? createdAt;

  const PendingReviewItem({
    required this.claimId,
    required this.citizenUlid,
    required this.labId,
    required this.localPatientId,
    this.matchScore,
    required this.matchFeatures,
    this.createdAt,
  });

  factory PendingReviewItem.fromJson(Map<String, dynamic> json) =>
      _$PendingReviewItemFromJson(json);
  Map<String, dynamic> toJson() => _$PendingReviewItemToJson(this);
}

@JsonSerializable()
class PendingReviewPage {
  final int total;
  final List<PendingReviewItem> items;

  const PendingReviewPage({required this.total, required this.items});

  factory PendingReviewPage.fromJson(Map<String, dynamic> json) =>
      _$PendingReviewPageFromJson(json);
  Map<String, dynamic> toJson() => _$PendingReviewPageToJson(this);
}

@JsonSerializable()
class ResolveDecision {
  final String decision;
  final String reason;

  const ResolveDecision({required this.decision, required this.reason});

  factory ResolveDecision.fromJson(Map<String, dynamic> json) =>
      _$ResolveDecisionFromJson(json);
  Map<String, dynamic> toJson() => _$ResolveDecisionToJson(this);
}
