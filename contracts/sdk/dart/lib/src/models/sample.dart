import 'package:json_annotation/json_annotation.dart';

part 'sample.g.dart';

@JsonSerializable()
class Sample {
  final int id;
  final int orderId;
  final String barcode;
  final String sampleType;
  final DateTime? collectionTime;
  final String? collectedBy;
  final String status;
  final String? rejectionReason;
  final String? notes;
  final String? storageLocation;
  final DateTime? createdAt;

  const Sample({
    required this.id,
    required this.orderId,
    required this.barcode,
    required this.sampleType,
    this.collectionTime,
    this.collectedBy,
    required this.status,
    this.rejectionReason,
    this.notes,
    this.storageLocation,
    this.createdAt,
  });

  factory Sample.fromJson(Map<String, dynamic> json) => _$SampleFromJson(json);
  Map<String, dynamic> toJson() => _$SampleToJson(this);
}
