import 'package:json_annotation/json_annotation.dart';
import '../enums.dart';

part 'notification.g.dart';

@JsonSerializable()
class NotificationSendRequest {
  final int orderId;
  final String? patientPhone;
  final String? patientEmail;
  final NotificationChannel channel;
  final String? message;
  final String? language;

  const NotificationSendRequest({
    required this.orderId,
    this.patientPhone,
    this.patientEmail,
    this.channel = NotificationChannel.sms,
    this.message,
    this.language,
  });

  factory NotificationSendRequest.fromJson(Map<String, dynamic> json) =>
      _$NotificationSendRequestFromJson(json);
  Map<String, dynamic> toJson() => _$NotificationSendRequestToJson(this);
}

@JsonSerializable()
class NotificationSendResponse {
  final bool success;
  final String? providerResponse;
  final String? error;

  const NotificationSendResponse({
    required this.success,
    this.providerResponse,
    this.error,
  });

  factory NotificationSendResponse.fromJson(Map<String, dynamic> json) =>
      _$NotificationSendResponseFromJson(json);
  Map<String, dynamic> toJson() => _$NotificationSendResponseToJson(this);
}

@JsonSerializable()
class NotificationHistoryItem {
  final int id;
  final int orderId;
  final String channel;
  final String recipient;
  final String status;
  final String? message;
  final DateTime? sentAt;
  final String? error;

  const NotificationHistoryItem({
    required this.id,
    required this.orderId,
    required this.channel,
    required this.recipient,
    required this.status,
    this.message,
    this.sentAt,
    this.error,
  });

  factory NotificationHistoryItem.fromJson(Map<String, dynamic> json) =>
      _$NotificationHistoryItemFromJson(json);
  Map<String, dynamic> toJson() => _$NotificationHistoryItemToJson(this);
}
