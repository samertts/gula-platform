import 'package:json_annotation/json_annotation.dart';
import '../enums.dart';

part 'patient.g.dart';

@JsonSerializable()
class Patient {
  final int id;
  final int labId;
  final String? healthId;
  final String? nationalIdHash;
  final String? familyIdHash;
  final int? guardianId;
  final String fullName;
  final String phone;
  final String? birthDate;
  final Gender? gender;
  final String? email;
  final DateTime? createdAt;
  final List<Patient>? dependents;

  const Patient({
    required this.id,
    required this.labId,
    this.healthId,
    this.nationalIdHash,
    this.familyIdHash,
    this.guardianId,
    required this.fullName,
    required this.phone,
    this.birthDate,
    this.gender,
    this.email,
    this.createdAt,
    this.dependents,
  });

  factory Patient.fromJson(Map<String, dynamic> json) => _$PatientFromJson(json);
  Map<String, dynamic> toJson() => _$PatientToJson(this);
}

@JsonSerializable()
class PatientCreateRequest {
  final int labId;
  final String fullName;
  final String phone;
  final String? birthDate;
  final String? gender;
  final String? email;
  final String? nationalId;
  final String? familyId;

  const PatientCreateRequest({
    required this.labId,
    required this.fullName,
    required this.phone,
    this.birthDate,
    this.gender,
    this.email,
    this.nationalId,
    this.familyId,
  });

  factory PatientCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$PatientCreateRequestFromJson(json);
  Map<String, dynamic> toJson() => _$PatientCreateRequestToJson(this);
}

@JsonSerializable()
class PatientUpdateRequest {
  final String? fullName;
  final String? phone;
  final String? birthDate;
  final String? gender;
  final String? email;

  const PatientUpdateRequest({
    this.fullName,
    this.phone,
    this.birthDate,
    this.gender,
    this.email,
  });

  factory PatientUpdateRequest.fromJson(Map<String, dynamic> json) =>
      _$PatientUpdateRequestFromJson(json);
  Map<String, dynamic> toJson() => _$PatientUpdateRequestToJson(this);
}

@JsonSerializable()
class PatientCardResponse {
  final Patient patient;
  final String qrToken;
  final String printableHtml;

  const PatientCardResponse({
    required this.patient,
    required this.qrToken,
    required this.printableHtml,
  });

  factory PatientCardResponse.fromJson(Map<String, dynamic> json) =>
      _$PatientCardResponseFromJson(json);
  Map<String, dynamic> toJson() => _$PatientCardResponseToJson(this);
}
