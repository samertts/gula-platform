import 'package:json_annotation/json_annotation.dart';
import '../enums.dart';
import 'patient.dart';
import 'result.dart';
import 'sample.dart';

part 'order.g.dart';

@JsonSerializable()
class LabOrder {
  final int id;
  final int patientId;
  final int labId;
  final String? doctorName;
  final int? doctorUserId;
  final OrderStatus status;
  final int? validatedBy;
  final DateTime? validatedAt;
  final DateTime? lockedAt;
  final int version;
  final DateTime? createdAt;
  final Patient? patient;
  final List<LabResult>? results;
  final List<Sample>? samples;

  const LabOrder({
    required this.id,
    required this.patientId,
    required this.labId,
    this.doctorName,
    this.doctorUserId,
    required this.status,
    this.validatedBy,
    this.validatedAt,
    this.lockedAt,
    required this.version,
    this.createdAt,
    this.patient,
    this.results,
    this.samples,
  });

  factory LabOrder.fromJson(Map<String, dynamic> json) => _$LabOrderFromJson(json);
  Map<String, dynamic> toJson() => _$LabOrderToJson(this);
}

@JsonSerializable()
class OrderCreateRequest {
  final int patientId;
  final int labId;
  final String? doctorName;
  final int? doctorUserId;

  const OrderCreateRequest({
    required this.patientId,
    required this.labId,
    this.doctorName,
    this.doctorUserId,
  });

  factory OrderCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$OrderCreateRequestFromJson(json);
  Map<String, dynamic> toJson() => _$OrderCreateRequestToJson(this);
}

@JsonSerializable()
class BatchOrderRequest {
  final List<OrderCreateRequest> orders;

  const BatchOrderRequest({required this.orders});

  factory BatchOrderRequest.fromJson(Map<String, dynamic> json) =>
      _$BatchOrderRequestFromJson(json);
  Map<String, dynamic> toJson() => _$BatchOrderRequestToJson(this);
}

@JsonSerializable()
class OrderValidateRequest {
  final int version;

  const OrderValidateRequest({required this.version});

  factory OrderValidateRequest.fromJson(Map<String, dynamic> json) =>
      _$OrderValidateRequestFromJson(json);
  Map<String, dynamic> toJson() => _$OrderValidateRequestToJson(this);
}
