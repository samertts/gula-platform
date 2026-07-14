import 'package:json_annotation/json_annotation.dart';
import '../enums.dart';

part 'governance.g.dart';

@JsonSerializable()
class GovernanceNode {
  final int id;
  final String name;
  final String? nameAr;
  final GovernanceNodeType nodeType;
  final int? parentId;
  final String? code;
  final bool isActive;

  const GovernanceNode({
    required this.id,
    required this.name,
    this.nameAr,
    required this.nodeType,
    this.parentId,
    this.code,
    required this.isActive,
  });

  factory GovernanceNode.fromJson(Map<String, dynamic> json) => _$GovernanceNodeFromJson(json);
  Map<String, dynamic> toJson() => _$GovernanceNodeToJson(this);
}

@JsonSerializable()
class Delegation {
  final int id;
  final int delegatorId;
  final int delegateId;
  final String delegationType;
  final String status;
  final DateTime? expiresAt;
  final String? scope;
  final DateTime? createdAt;

  const Delegation({
    required this.id,
    required this.delegatorId,
    required this.delegateId,
    required this.delegationType,
    required this.status,
    this.expiresAt,
    this.scope,
    this.createdAt,
  });

  factory Delegation.fromJson(Map<String, dynamic> json) => _$DelegationFromJson(json);
  Map<String, dynamic> toJson() => _$DelegationToJson(this);
}

@JsonSerializable()
class ComplianceReport {
  final String reportId;
  final DateTime generatedAt;
  final String period;
  final int totalAuditEntries;
  final int integrityPassCount;
  final int integrityFailCount;
  final List<String> warnings;
  final String? status;

  const ComplianceReport({
    required this.reportId,
    required this.generatedAt,
    required this.period,
    required this.totalAuditEntries,
    required this.integrityPassCount,
    required this.integrityFailCount,
    required this.warnings,
    this.status,
  });

  factory ComplianceReport.fromJson(Map<String, dynamic> json) =>
      _$ComplianceReportFromJson(json);
  Map<String, dynamic> toJson() => _$ComplianceReportToJson(this);
}

@JsonSerializable()
class SecurityReport {
  final int activeUsers;
  final int activeSessions;
  final int failedLogins24h;
  final int rateLimitHits24h;
  final int auditChainGaps;
  final DataClassificationLevel dataClassificationLevel;
  final bool encryptionAtRest;
  final bool encryptionInTransit;
  final DateTime lastSecurityAudit;
  final List<String> findings;

  const SecurityReport({
    required this.activeUsers,
    required this.activeSessions,
    required this.failedLogins24h,
    required this.rateLimitHits24h,
    required this.auditChainGaps,
    required this.dataClassificationLevel,
    required this.encryptionAtRest,
    required this.encryptionInTransit,
    required this.lastSecurityAudit,
    required this.findings,
  });

  factory SecurityReport.fromJson(Map<String, dynamic> json) => _$SecurityReportFromJson(json);
  Map<String, dynamic> toJson() => _$SecurityReportToJson(this);
}

@JsonSerializable()
class PolicyDocument {
  final int id;
  final String title;
  final String? titleAr;
  final String policyType;
  final String status;
  final String? content;
  final String? contentAr;
  final int version;
  final DateTime? effectiveAt;
  final DateTime? createdAt;

  const PolicyDocument({
    required this.id,
    required this.title,
    this.titleAr,
    required this.policyType,
    required this.status,
    this.content,
    this.contentAr,
    required this.version,
    this.effectiveAt,
    this.createdAt,
  });

  factory PolicyDocument.fromJson(Map<String, dynamic> json) => _$PolicyDocumentFromJson(json);
  Map<String, dynamic> toJson() => _$PolicyDocumentToJson(this);
}

@JsonSerializable()
class License {
  final int id;
  final int labId;
  final String licenseNumber;
  final String licenseType;
  final LicenseStatus status;
  final DateTime? issuedAt;
  final DateTime? expiresAt;
  final DateTime? createdAt;

  const License({
    required this.id,
    required this.labId,
    required this.licenseNumber,
    required this.licenseType,
    required this.status,
    this.issuedAt,
    this.expiresAt,
    this.createdAt,
  });

  factory License.fromJson(Map<String, dynamic> json) => _$LicenseFromJson(json);
  Map<String, dynamic> toJson() => _$LicenseToJson(this);
}
