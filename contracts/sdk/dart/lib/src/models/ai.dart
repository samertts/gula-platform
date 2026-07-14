import 'package:json_annotation/json_annotation.dart';
import '../enums.dart';

part 'ai.g.dart';

@JsonSerializable()
class AiSuggestionRequest {
  final int orderId;
  final String prompt;

  const AiSuggestionRequest({required this.orderId, required this.prompt});

  factory AiSuggestionRequest.fromJson(Map<String, dynamic> json) =>
      _$AiSuggestionRequestFromJson(json);
  Map<String, dynamic> toJson() => _$AiSuggestionRequestToJson(this);
}

@JsonSerializable()
class AiSuggestionResponse {
  final String suggestion;
  final double confidenceScore;
  final String? riskLevel;
  final bool escalationRecommended;

  const AiSuggestionResponse({
    required this.suggestion,
    required this.confidenceScore,
    this.riskLevel,
    required this.escalationRecommended,
  });

  factory AiSuggestionResponse.fromJson(Map<String, dynamic> json) =>
      _$AiSuggestionResponseFromJson(json);
  Map<String, dynamic> toJson() => _$AiSuggestionResponseToJson(this);
}

@JsonSerializable()
class AiPendingApproval {
  final int id;
  final int orderId;
  final String action;
  final String suggestion;
  final double confidenceScore;
  final String? riskLevel;
  final DateTime? createdAt;

  const AiPendingApproval({
    required this.id,
    required this.orderId,
    required this.action,
    required this.suggestion,
    required this.confidenceScore,
    this.riskLevel,
    this.createdAt,
  });

  factory AiPendingApproval.fromJson(Map<String, dynamic> json) =>
      _$AiPendingApprovalFromJson(json);
  Map<String, dynamic> toJson() => _$AiPendingApprovalToJson(this);
}

@JsonSerializable()
class AiInteraction {
  final String id;
  final int labId;
  final String anonymousSessionId;
  final String? language;
  final String? region;
  final String? intent;
  final String? prompt;
  final bool promptRedacted;
  final String? response;
  final String? responseModel;
  final String? retrievalStrategy;
  final int? retrievalCount;
  final Map<String, dynamic>? biomarkers;
  final int? latencyMs;
  final AiInteractionStatus status;
  final String? errorCode;
  final double? confidenceScore;
  final AiRiskLevel? riskLevel;
  final bool escalationRecommended;
  final bool? retrievalUsed;
  final double? sourceQuality;
  final int? unsupportedClaims;
  final bool fallbackGeneration;
  final Map<String, dynamic>? safetyFlags;
  final DateTime? createdAt;
  final List<AiRetrievalRef>? retrievalRefs;
  final List<AiFeedback>? feedback;

  const AiInteraction({
    required this.id,
    required this.labId,
    required this.anonymousSessionId,
    this.language,
    this.region,
    this.intent,
    this.prompt,
    required this.promptRedacted,
    this.response,
    this.responseModel,
    this.retrievalStrategy,
    this.retrievalCount,
    this.biomarkers,
    this.latencyMs,
    required this.status,
    this.errorCode,
    this.confidenceScore,
    this.riskLevel,
    required this.escalationRecommended,
    this.retrievalUsed,
    this.sourceQuality,
    this.unsupportedClaims,
    required this.fallbackGeneration,
    this.safetyFlags,
    this.createdAt,
    this.retrievalRefs,
    this.feedback,
  });

  factory AiInteraction.fromJson(Map<String, dynamic> json) => _$AiInteractionFromJson(json);
  Map<String, dynamic> toJson() => _$AiInteractionToJson(this);
}

@JsonSerializable()
class AiRetrievalRef {
  final String id;
  final String interactionId;
  final String? source;
  final String? docId;
  final String? docTitle;
  final String? chunkText;
  final double? similarity;
  final int? rank;
  final DateTime? createdAt;

  const AiRetrievalRef({
    required this.id,
    required this.interactionId,
    this.source,
    this.docId,
    this.docTitle,
    this.chunkText,
    this.similarity,
    this.rank,
    this.createdAt,
  });

  factory AiRetrievalRef.fromJson(Map<String, dynamic> json) => _$AiRetrievalRefFromJson(json);
  Map<String, dynamic> toJson() => _$AiRetrievalRefToJson(this);
}

@JsonSerializable()
class AiFeedback {
  final String id;
  final String interactionId;
  final int labId;
  final String anonymousSessionId;
  final String signal;
  final String? notes;
  final DateTime? createdAt;

  const AiFeedback({
    required this.id,
    required this.interactionId,
    required this.labId,
    required this.anonymousSessionId,
    required this.signal,
    this.notes,
    this.createdAt,
  });

  factory AiFeedback.fromJson(Map<String, dynamic> json) => _$AiFeedbackFromJson(json);
  Map<String, dynamic> toJson() => _$AiFeedbackToJson(this);
}

@JsonSerializable()
class AiCriticalAlert {
  final int id;
  final int orderId;
  final int patientId;
  final String patientName;
  final String testName;
  final String value;
  final String unit;
  final String flag;

  const AiCriticalAlert({
    required this.id,
    required this.orderId,
    required this.patientId,
    required this.patientName,
    required this.testName,
    required this.value,
    required this.unit,
    required this.flag,
  });

  factory AiCriticalAlert.fromJson(Map<String, dynamic> json) => _$AiCriticalAlertFromJson(json);
  Map<String, dynamic> toJson() => _$AiCriticalAlertToJson(this);
}

@JsonSerializable()
class OrderIntelligence {
  final int orderId;
  final List<AiSuggestionResponse> suggestions;
  final List<AiCriticalAlert> criticalAlerts;
  final String? summary;

  const OrderIntelligence({
    required this.orderId,
    required this.suggestions,
    required this.criticalAlerts,
    this.summary,
  });

  factory OrderIntelligence.fromJson(Map<String, dynamic> json) =>
      _$OrderIntelligenceFromJson(json);
  Map<String, dynamic> toJson() => _$OrderIntelligenceToJson(this);
}

@JsonSerializable()
class AnalyzeRequest {
  final int orderId;

  const AnalyzeRequest({required this.orderId});

  factory AnalyzeRequest.fromJson(Map<String, dynamic> json) => _$AnalyzeRequestFromJson(json);
  Map<String, dynamic> toJson() => _$AnalyzeRequestToJson(this);
}

@JsonSerializable()
class AnalyzeResponse {
  final String interpretation;
  final String? clinicalSummary;
  final List<String> flags;
  final String? recommendation;

  const AnalyzeResponse({
    required this.interpretation,
    this.clinicalSummary,
    required this.flags,
    this.recommendation,
  });

  factory AnalyzeResponse.fromJson(Map<String, dynamic> json) => _$AnalyzeResponseFromJson(json);
  Map<String, dynamic> toJson() => _$AnalyzeResponseToJson(this);
}
