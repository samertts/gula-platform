import 'package:json_annotation/json_annotation.dart';

part 'result.g.dart';

@JsonSerializable()
class LabResult {
  final int id;
  final int orderId;
  final int? testTypeId;
  final String testName;
  final double? value;
  final String? valueText;
  final String? unit;
  final double? normalRangeLow;
  final double? normalRangeHigh;
  final String? flag;
  final String token;
  final String? tokenHash;
  final DateTime? expiresAt;
  final DateTime? createdAt;
  final String? clinicalEngineVersion;
  final int version;

  const LabResult({
    required this.id,
    required this.orderId,
    this.testTypeId,
    required this.testName,
    this.value,
    this.valueText,
    this.unit,
    this.normalRangeLow,
    this.normalRangeHigh,
    this.flag,
    required this.token,
    this.tokenHash,
    this.expiresAt,
    this.createdAt,
    this.clinicalEngineVersion,
    required this.version,
  });

  factory LabResult.fromJson(Map<String, dynamic> json) => _$LabResultFromJson(json);
  Map<String, dynamic> toJson() => _$LabResultToJson(this);
}

@JsonSerializable()
class ResultCreateRequest {
  final int orderId;
  final int? testTypeId;
  final String testName;
  final double? value;
  final String? valueText;
  final String? unit;
  final double? normalRangeLow;
  final double? normalRangeHigh;
  final String? flag;

  const ResultCreateRequest({
    required this.orderId,
    this.testTypeId,
    required this.testName,
    this.value,
    this.valueText,
    this.unit,
    this.normalRangeLow,
    this.normalRangeHigh,
    this.flag,
  });

  factory ResultCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$ResultCreateRequestFromJson(json);
  Map<String, dynamic> toJson() => _$ResultCreateRequestToJson(this);
}

@JsonSerializable()
class TestType {
  final int id;
  final String testCode;
  final String testName;
  final String? testNameAr;
  final String? category;
  final String? unit;
  final double? normalRangeLow;
  final double? normalRangeHigh;
  final String? interpretationLow;
  final String? interpretationNormal;
  final String? interpretationHigh;
  final String? interpretationLowAr;
  final String? interpretationNormalAr;
  final String? interpretationHighAr;

  const TestType({
    required this.id,
    required this.testCode,
    required this.testName,
    this.testNameAr,
    this.category,
    this.unit,
    this.normalRangeLow,
    this.normalRangeHigh,
    this.interpretationLow,
    this.interpretationNormal,
    this.interpretationHigh,
    this.interpretationLowAr,
    this.interpretationNormalAr,
    this.interpretationHighAr,
  });

  factory TestType.fromJson(Map<String, dynamic> json) => _$TestTypeFromJson(json);
  Map<String, dynamic> toJson() => _$TestTypeToJson(this);
}

@JsonSerializable()
class TestResult {
  final int id;
  final int citizenId;
  final int labId;
  final int? deviceId;
  final String testCode;
  final String testNameEn;
  final String testNameAr;
  final String? category;
  final double? resultValue;
  final String? resultText;
  final String? unit;
  final double? referenceMin;
  final double? referenceMax;
  final String status;
  final bool isCritical;
  final bool isAbnormal;
  final String? abnormalityDirection;
  final DateTime sampleCollectedAt;
  final DateTime? resultCompletedAt;
  final DateTime? verifiedAt;
  final String? verifiedBy;
  final String sampleBarcode;
  final String? orderingPhysician;
  final String? clinicalNotes;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const TestResult({
    required this.id,
    required this.citizenId,
    required this.labId,
    this.deviceId,
    required this.testCode,
    required this.testNameEn,
    required this.testNameAr,
    this.category,
    this.resultValue,
    this.resultText,
    this.unit,
    this.referenceMin,
    this.referenceMax,
    required this.status,
    required this.isCritical,
    required this.isAbnormal,
    this.abnormalityDirection,
    required this.sampleCollectedAt,
    this.resultCompletedAt,
    this.verifiedAt,
    this.verifiedBy,
    required this.sampleBarcode,
    this.orderingPhysician,
    this.clinicalNotes,
    this.createdAt,
    this.updatedAt,
  });

  factory TestResult.fromJson(Map<String, dynamic> json) => _$TestResultFromJson(json);
  Map<String, dynamic> toJson() => _$TestResultToJson(this);
}
