import 'package:json_annotation/json_annotation.dart';
import '../enums.dart';

part 'consent.g.dart';

@JsonSerializable()
class Consent {
  final String id;
  final String gpid;
  final String granteeId;
  final String scope;
  final ConsentStatus status;
  final DateTime expiresAt;
  final DateTime? createdAt;
  final DateTime? revokedAt;
  final int? createdByUserId;

  const Consent({
    required this.id,
    required this.gpid,
    required this.granteeId,
    required this.scope,
    required this.status,
    required this.expiresAt,
    this.createdAt,
    this.revokedAt,
    this.createdByUserId,
  });

  factory Consent.fromJson(Map<String, dynamic> json) => _$ConsentFromJson(json);
  Map<String, dynamic> toJson() => _$ConsentToJson(this);
}

@JsonSerializable()
class ConsentGrantRequest {
  final String gpid;
  final String granteeId;
  final String scope;
  final int durationHours;

  const ConsentGrantRequest({
    required this.gpid,
    required this.granteeId,
    required this.scope,
    required this.durationHours,
  });

  factory ConsentGrantRequest.fromJson(Map<String, dynamic> json) =>
      _$ConsentGrantRequestFromJson(json);
  Map<String, dynamic> toJson() => _$ConsentGrantRequestToJson(this);
}

@JsonSerializable()
class GrantResponse {
  final String consentId;
  final String gpid;
  final String granteeId;
  final String scope;
  final DateTime expiresAt;
  final String status;

  const GrantResponse({
    required this.consentId,
    required this.gpid,
    required this.granteeId,
    required this.scope,
    required this.expiresAt,
    required this.status,
  });

  factory GrantResponse.fromJson(Map<String, dynamic> json) => _$GrantResponseFromJson(json);
  Map<String, dynamic> toJson() => _$GrantResponseToJson(this);
}

@JsonSerializable()
class RevokeRequest {
  final String consentId;

  const RevokeRequest({required this.consentId});

  factory RevokeRequest.fromJson(Map<String, dynamic> json) => _$RevokeRequestFromJson(json);
  Map<String, dynamic> toJson() => _$RevokeRequestToJson(this);
}

@JsonSerializable()
class RevokeResponse {
  final String consentId;
  final String status;
  final DateTime revokedAt;

  const RevokeResponse({
    required this.consentId,
    required this.status,
    required this.revokedAt,
  });

  factory RevokeResponse.fromJson(Map<String, dynamic> json) => _$RevokeResponseFromJson(json);
  Map<String, dynamic> toJson() => _$RevokeResponseToJson(this);
}

@JsonSerializable()
class CheckRequest {
  final String gpid;
  final String granteeId;
  final String scope;

  const CheckRequest({
    required this.gpid,
    required this.granteeId,
    required this.scope,
  });

  factory CheckRequest.fromJson(Map<String, dynamic> json) => _$CheckRequestFromJson(json);
  Map<String, dynamic> toJson() => _$CheckRequestToJson(this);
}

@JsonSerializable()
class CheckResponse {
  final bool granted;
  final String? consentId;
  final DateTime? expiresAt;

  const CheckResponse({required this.granted, this.consentId, this.expiresAt});

  factory CheckResponse.fromJson(Map<String, dynamic> json) => _$CheckResponseFromJson(json);
  Map<String, dynamic> toJson() => _$CheckResponseToJson(this);
}
