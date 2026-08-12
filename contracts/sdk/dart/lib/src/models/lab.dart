import 'package:json_annotation/json_annotation.dart';
import '../enums.dart';

part 'lab.g.dart';

@JsonSerializable()
class Lab {
  final int id;
  final String name;
  final String? licenseNumber;
  final LabType? labType;
  final String? directorName;
  final String? website;
  final String city;
  final String address;
  final String phone;
  final bool isActive;
  final DateTime? createdAt;

  const Lab({
    required this.id,
    required this.name,
    this.licenseNumber,
    this.labType,
    this.directorName,
    this.website,
    required this.city,
    required this.address,
    required this.phone,
    required this.isActive,
    this.createdAt,
  });

  factory Lab.fromJson(Map<String, dynamic> json) => _$LabFromJson(json);
  Map<String, dynamic> toJson() => _$LabToJson(this);
}

@JsonSerializable()
class LabUpdateRequest {
  final String? name;
  final String? city;
  final String? address;
  final String? phone;
  final String? licenseNumber;
  final String? labType;
  final String? directorName;
  final String? website;

  const LabUpdateRequest({
    this.name,
    this.city,
    this.address,
    this.phone,
    this.licenseNumber,
    this.labType,
    this.directorName,
    this.website,
  });

  factory LabUpdateRequest.fromJson(Map<String, dynamic> json) =>
      _$LabUpdateRequestFromJson(json);
  Map<String, dynamic> toJson() => _$LabUpdateRequestToJson(this);
}

@JsonSerializable()
class LabUser {
  final int id;
  final int labId;
  final String name;
  final String email;
  final String role;
  final bool isActive;
  final int permVersion;
  final DateTime? createdAt;
  final String? nationalIdHash;
  final int? provinceId;
  final int? createdBy;

  const LabUser({
    required this.id,
    required this.labId,
    required this.name,
    required this.email,
    required this.role,
    required this.isActive,
    required this.permVersion,
    this.createdAt,
    this.nationalIdHash,
    this.provinceId,
    this.createdBy,
  });

  factory LabUser.fromJson(Map<String, dynamic> json) => _$LabUserFromJson(json);
  Map<String, dynamic> toJson() => _$LabUserToJson(this);
}

@JsonSerializable()
class StaffCreateRequest {
  final int labId;
  final String name;
  final String email;
  final String password;
  final String role;
  final int? provinceId;

  const StaffCreateRequest({
    required this.labId,
    required this.name,
    required this.email,
    required this.password,
    required this.role,
    this.provinceId,
  });

  factory StaffCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$StaffCreateRequestFromJson(json);
  Map<String, dynamic> toJson() => _$StaffCreateRequestToJson(this);
}
