import 'package:json_annotation/json_annotation.dart';

part 'lims.g.dart';

@JsonSerializable()
class DashboardResponse {
  final int totalPatients;
  final int totalOrders;
  final int pendingOrders;
  final int criticalResults;
  final int todayOrders;
  final int todaySamples;

  const DashboardResponse({
    required this.totalPatients,
    required this.totalOrders,
    required this.pendingOrders,
    required this.criticalResults,
    required this.todayOrders,
    required this.todaySamples,
  });

  factory DashboardResponse.fromJson(Map<String, dynamic> json) =>
      _$DashboardResponseFromJson(json);
  Map<String, dynamic> toJson() => _$DashboardResponseToJson(this);
}

@JsonSerializable()
class StatsResponse {
  final int totalOrders;
  final int completedOrders;
  final int cancelledOrders;
  final int validatedOrders;
  final double avgCompletionTimeHours;
  final Map<String, int> ordersByDay;
  final Map<String, int> resultsByCategory;

  const StatsResponse({
    required this.totalOrders,
    required this.completedOrders,
    required this.cancelledOrders,
    required this.validatedOrders,
    required this.avgCompletionTimeHours,
    required this.ordersByDay,
    required this.resultsByCategory,
  });

  factory StatsResponse.fromJson(Map<String, dynamic> json) => _$StatsResponseFromJson(json);
  Map<String, dynamic> toJson() => _$StatsResponseToJson(this);
}

@JsonSerializable()
class AuditLogEntry {
  final int id;
  final int? userId;
  final String? userRole;
  final String action;
  final String resourceType;
  final int? resourceId;
  final String? details;
  final String? ipAddress;
  final DateTime? createdAt;
  final String? chainHash;

  const AuditLogEntry({
    required this.id,
    this.userId,
    this.userRole,
    required this.action,
    required this.resourceType,
    this.resourceId,
    this.details,
    this.ipAddress,
    this.createdAt,
    this.chainHash,
  });

  factory AuditLogEntry.fromJson(Map<String, dynamic> json) => _$AuditLogEntryFromJson(json);
  Map<String, dynamic> toJson() => _$AuditLogEntryToJson(this);
}

@JsonSerializable()
class Organization {
  final int id;
  final String name;
  final String? nameAr;
  final String orgType;
  final String? licenseNumber;
  final String? taxId;
  final String? phone;
  final String? email;
  final String? website;
  final String? address;
  final String? city;
  final String? province;
  final String country;
  final bool isActive;
  final DateTime? createdAt;

  const Organization({
    required this.id,
    required this.name,
    this.nameAr,
    required this.orgType,
    this.licenseNumber,
    this.taxId,
    this.phone,
    this.email,
    this.website,
    this.address,
    this.city,
    this.province,
    this.country = 'IQ',
    required this.isActive,
    this.createdAt,
  });

  factory Organization.fromJson(Map<String, dynamic> json) => _$OrganizationFromJson(json);
  Map<String, dynamic> toJson() => _$OrganizationToJson(this);
}

@JsonSerializable()
class Facility {
  final int id;
  final int organizationId;
  final String name;
  final String? nameAr;
  final String facilityType;
  final String? phone;
  final String? email;
  final String? address;
  final String? city;
  final String? province;
  final bool isActive;
  final DateTime? createdAt;

  const Facility({
    required this.id,
    required this.organizationId,
    required this.name,
    this.nameAr,
    required this.facilityType,
    this.phone,
    this.email,
    this.address,
    this.city,
    this.province,
    required this.isActive,
    this.createdAt,
  });

  factory Facility.fromJson(Map<String, dynamic> json) => _$FacilityFromJson(json);
  Map<String, dynamic> toJson() => _$FacilityToJson(this);
}

@JsonSerializable()
class Appointment {
  final int id;
  final int patientId;
  final int? providerId;
  final int? facilityId;
  final int labId;
  final String appointmentType;
  final String status;
  final DateTime scheduledDate;
  final int durationMinutes;
  final String? reason;
  final String? notes;
  final DateTime? createdAt;

  const Appointment({
    required this.id,
    required this.patientId,
    this.providerId,
    this.facilityId,
    required this.labId,
    required this.appointmentType,
    required this.status,
    required this.scheduledDate,
    this.durationMinutes = 30,
    this.reason,
    this.notes,
    this.createdAt,
  });

  factory Appointment.fromJson(Map<String, dynamic> json) => _$AppointmentFromJson(json);
  Map<String, dynamic> toJson() => _$AppointmentToJson(this);
}

@JsonSerializable()
class CriticalAlert {
  final int id;
  final int orderId;
  final int patientId;
  final String patientName;
  final String testName;
  final String value;
  final String unit;
  final String? flag;
  final DateTime? createdAt;

  const CriticalAlert({
    required this.id,
    required this.orderId,
    required this.patientId,
    required this.patientName,
    required this.testName,
    required this.value,
    required this.unit,
    this.flag,
    this.createdAt,
  });

  factory CriticalAlert.fromJson(Map<String, dynamic> json) => _$CriticalAlertFromJson(json);
  Map<String, dynamic> toJson() => _$CriticalAlertToJson(this);
}

@JsonSerializable()
class DeviceResultPayload {
  final int labId;
  final String deviceId;
  final String sampleBarcode;
  final String testCode;
  final String testName;
  final double? value;
  final String? valueText;
  final String unit;
  final DateTime sampleCollectedAt;

  const DeviceResultPayload({
    required this.labId,
    required this.deviceId,
    required this.sampleBarcode,
    required this.testCode,
    required this.testName,
    this.value,
    this.valueText,
    required this.unit,
    required this.sampleCollectedAt,
  });

  factory DeviceResultPayload.fromJson(Map<String, dynamic> json) =>
      _$DeviceResultPayloadFromJson(json);
  Map<String, dynamic> toJson() => _$DeviceResultPayloadToJson(this);
}

@JsonSerializable()
class IntegrationStatus {
  final String name;
  final String status;
  final DateTime? lastCheckedAt;
  final String? error;

  const IntegrationStatus({
    required this.name,
    required this.status,
    this.lastCheckedAt,
    this.error,
  });

  factory IntegrationStatus.fromJson(Map<String, dynamic> json) =>
      _$IntegrationStatusFromJson(json);
  Map<String, dynamic> toJson() => _$IntegrationStatusToJson(this);
}
