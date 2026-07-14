import 'package:json_annotation/json_annotation.dart';

part 'fhir.g.dart';

@JsonSerializable()
class FhirPatient {
  final String? id;
  final String? resourceType;
  final List<FhirHumanName>? name;
  final String? gender;
  final String? birthDate;
  final String? phone;
  final String? email;
  final String? nationalId;

  const FhirPatient({
    this.id,
    this.resourceType = 'Patient',
    this.name,
    this.gender,
    this.birthDate,
    this.phone,
    this.email,
    this.nationalId,
  });

  factory FhirPatient.fromJson(Map<String, dynamic> json) => _$FhirPatientFromJson(json);
  Map<String, dynamic> toJson() => _$FhirPatientToJson(this);
}

@JsonSerializable()
class FhirHumanName {
  final String? use;
  final String? family;
  final List<String>? given;
  final String? text;

  const FhirHumanName({this.use, this.family, this.given, this.text});

  factory FhirHumanName.fromJson(Map<String, dynamic> json) => _$FhirHumanNameFromJson(json);
  Map<String, dynamic> toJson() => _$FhirHumanNameToJson(this);
}

@JsonSerializable()
class FhirObservation {
  final String? id;
  final String? resourceType;
  final String? status;
  final FhirCodeableConcept? code;
  final FhirQuantity? valueQuantity;
  final String? valueString;
  final FhirCodeableConcept? interpretation;
  final FhirReferenceRange? referenceRange;
  final String? effectiveDateTime;
  final String? issued;

  const FhirObservation({
    this.id,
    this.resourceType = 'Observation',
    this.status,
    this.code,
    this.valueQuantity,
    this.valueString,
    this.interpretation,
    this.referenceRange,
    this.effectiveDateTime,
    this.issued,
  });

  factory FhirObservation.fromJson(Map<String, dynamic> json) => _$FhirObservationFromJson(json);
  Map<String, dynamic> toJson() => _$FhirObservationToJson(this);
}

@JsonSerializable()
class FhirQuantity {
  final double? value;
  final String? unit;
  final String? system;
  final String? code;

  const FhirQuantity({this.value, this.unit, this.system, this.code});

  factory FhirQuantity.fromJson(Map<String, dynamic> json) => _$FhirQuantityFromJson(json);
  Map<String, dynamic> toJson() => _$FhirQuantityToJson(this);
}

@JsonSerializable()
class FhirCodeableConcept {
  final List<FhirCoding>? coding;
  final String? text;

  const FhirCodeableConcept({this.coding, this.text});

  factory FhirCodeableConcept.fromJson(Map<String, dynamic> json) =>
      _$FhirCodeableConceptFromJson(json);
  Map<String, dynamic> toJson() => _$FhirCodeableConceptToJson(this);
}

@JsonSerializable()
class FhirCoding {
  final String? system;
  final String? code;
  final String? display;

  const FhirCoding({this.system, this.code, this.display});

  factory FhirCoding.fromJson(Map<String, dynamic> json) => _$FhirCodingFromJson(json);
  Map<String, dynamic> toJson() => _$FhirCodingToJson(this);
}

@JsonSerializable()
class FhirReferenceRange {
  final FhirSimpleQuantity? low;
  final FhirSimpleQuantity? high;
  final String? type;

  const FhirReferenceRange({this.low, this.high, this.type});

  factory FhirReferenceRange.fromJson(Map<String, dynamic> json) =>
      _$FhirReferenceRangeFromJson(json);
  Map<String, dynamic> toJson() => _$FhirReferenceRangeToJson(this);
}

@JsonSerializable()
class FhirSimpleQuantity {
  final double? value;
  final String? unit;

  const FhirSimpleQuantity({this.value, this.unit});

  factory FhirSimpleQuantity.fromJson(Map<String, dynamic> json) =>
      _$FhirSimpleQuantityFromJson(json);
  Map<String, dynamic> toJson() => _$FhirSimpleQuantityToJson(this);
}

@JsonSerializable()
class FhirDiagnosticReport {
  final String? id;
  final String? resourceType;
  final String? status;
  final FhirCodeableConcept? code;
  final String? subject;
  final String? effectiveDateTime;
  final String? issued;
  final List<FhirObservation>? result;

  const FhirDiagnosticReport({
    this.id,
    this.resourceType = 'DiagnosticReport',
    this.status,
    this.code,
    this.subject,
    this.effectiveDateTime,
    this.issued,
    this.result,
  });

  factory FhirDiagnosticReport.fromJson(Map<String, dynamic> json) =>
      _$FhirDiagnosticReportFromJson(json);
  Map<String, dynamic> toJson() => _$FhirDiagnosticReportToJson(this);
}

@JsonSerializable()
class FhirServiceRequest {
  final String? id;
  final String? resourceType;
  final String? status;
  final String? intent;
  final FhirCodeableConcept? code;
  final String? subject;
  final String? authoredOn;
  final String? requester;

  const FhirServiceRequest({
    this.id,
    this.resourceType = 'ServiceRequest',
    this.status,
    this.intent,
    this.code,
    this.subject,
    this.authoredOn,
    this.requester,
  });

  factory FhirServiceRequest.fromJson(Map<String, dynamic> json) =>
      _$FhirServiceRequestFromJson(json);
  Map<String, dynamic> toJson() => _$FhirServiceRequestToJson(this);
}
