import 'package:json_annotation/json_annotation.dart';
import '../enums.dart';

part 'claim.g.dart';

@JsonSerializable()
class Claim {
  final int id;
  final int labId;
  final int patientId;
  final int? orderId;
  final ClaimStatus status;
  final double? totalAmount;
  final String currency;
  final String? idempotencyKey;
  final String? externalRef;
  final DateTime? submittedAt;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final List<ClaimItem>? items;

  const Claim({
    required this.id,
    required this.labId,
    required this.patientId,
    this.orderId,
    required this.status,
    this.totalAmount,
    this.currency = 'IQD',
    this.idempotencyKey,
    this.externalRef,
    this.submittedAt,
    this.createdAt,
    this.updatedAt,
    this.items,
  });

  factory Claim.fromJson(Map<String, dynamic> json) => _$ClaimFromJson(json);
  Map<String, dynamic> toJson() => _$ClaimToJson(this);
}

@JsonSerializable()
class ClaimItem {
  final int id;
  final int claimId;
  final String testCode;
  final String? description;
  final int quantity;
  final double unitPrice;
  final double amount;

  const ClaimItem({
    required this.id,
    required this.claimId,
    required this.testCode,
    this.description,
    required this.quantity,
    required this.unitPrice,
    required this.amount,
  });

  factory ClaimItem.fromJson(Map<String, dynamic> json) => _$ClaimItemFromJson(json);
  Map<String, dynamic> toJson() => _$ClaimItemToJson(this);
}

@JsonSerializable()
class ClaimCreateRequest {
  final int labId;
  final int patientId;
  final int? orderId;
  final String? currency;
  final String? externalRef;
  final List<ClaimItemCreateRequest> items;

  const ClaimCreateRequest({
    required this.labId,
    required this.patientId,
    this.orderId,
    this.currency,
    this.externalRef,
    required this.items,
  });

  factory ClaimCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$ClaimCreateRequestFromJson(json);
  Map<String, dynamic> toJson() => _$ClaimCreateRequestToJson(this);
}

@JsonSerializable()
class ClaimItemCreateRequest {
  final String testCode;
  final String? description;
  final int quantity;
  final double unitPrice;

  const ClaimItemCreateRequest({
    required this.testCode,
    this.description,
    required this.quantity,
    required this.unitPrice,
  });

  factory ClaimItemCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$ClaimItemCreateRequestFromJson(json);
  Map<String, dynamic> toJson() => _$ClaimItemCreateRequestToJson(this);
}
