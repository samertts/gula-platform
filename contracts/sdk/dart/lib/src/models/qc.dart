import 'package:json_annotation/json_annotation.dart';
import '../enums.dart';

part 'qc.g.dart';

@JsonSerializable()
class QualityControl {
  final int id;
  final int labId;
  final String testCode;
  final String? instrumentName;
  final String? lotNumber;
  final QcLevel level;
  final double expectedValue;
  final double measuredValue;
  final double? sd;
  final String? unit;
  final QcStatus status;
  final WestgardRule? violation;
  final String? notes;
  final String? performedBy;
  final DateTime? createdAt;

  const QualityControl({
    required this.id,
    required this.labId,
    required this.testCode,
    this.instrumentName,
    this.lotNumber,
    required this.level,
    required this.expectedValue,
    required this.measuredValue,
    this.sd,
    this.unit,
    required this.status,
    this.violation,
    this.notes,
    this.performedBy,
    this.createdAt,
  });

  factory QualityControl.fromJson(Map<String, dynamic> json) => _$QualityControlFromJson(json);
  Map<String, dynamic> toJson() => _$QualityControlToJson(this);
}

@JsonSerializable()
class QcCreateRequest {
  final int labId;
  final String testCode;
  final String? instrumentName;
  final String? lotNumber;
  final String level;
  final double expectedValue;
  final double measuredValue;
  final double? sd;
  final String? unit;
  final String? notes;
  final String? performedBy;

  const QcCreateRequest({
    required this.labId,
    required this.testCode,
    this.instrumentName,
    this.lotNumber,
    required this.level,
    required this.expectedValue,
    required this.measuredValue,
    this.sd,
    this.unit,
    this.notes,
    this.performedBy,
  });

  factory QcCreateRequest.fromJson(Map<String, dynamic> json) => _$QcCreateRequestFromJson(json);
  Map<String, dynamic> toJson() => _$QcCreateRequestToJson(this);
}

@JsonSerializable()
class QcStatistics {
  final String testCode;
  final int totalRuns;
  final double mean;
  final double sd;
  final double cv;
  final double min;
  final double max;
  final int failures;
  final String? latestViolation;

  const QcStatistics({
    required this.testCode,
    required this.totalRuns,
    required this.mean,
    required this.sd,
    required this.cv,
    required this.min,
    required this.max,
    required this.failures,
    this.latestViolation,
  });

  factory QcStatistics.fromJson(Map<String, dynamic> json) => _$QcStatisticsFromJson(json);
  Map<String, dynamic> toJson() => _$QcStatisticsToJson(this);
}

@JsonSerializable()
class LeveyJenningsPoint {
  final DateTime date;
  final double value;
  final double mean;
  final double sd;
  final bool outOfControl;

  const LeveyJenningsPoint({
    required this.date,
    required this.value,
    required this.mean,
    required this.sd,
    required this.outOfControl,
  });

  factory LeveyJenningsPoint.fromJson(Map<String, dynamic> json) =>
      _$LeveyJenningsPointFromJson(json);
  Map<String, dynamic> toJson() => _$LeveyJenningsPointToJson(this);
}
