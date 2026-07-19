class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final Map<String, dynamic>? details;

  const ApiException(this.message, {this.statusCode, this.details});

  @override
  String toString() => 'ApiException($statusCode): $message';
}

class AuthException extends ApiException {
  const AuthException([super.message = 'Authentication required', super.statusCode = 401]);
}

class UnauthorizedException extends ApiException {
  const UnauthorizedException([super.message = 'Forbidden', super.statusCode = 403]);
}

class NotFoundException extends ApiException {
  const NotFoundException([super.message = 'Resource not found', super.statusCode = 404]);
}

class ConflictException extends ApiException {
  const ConflictException([super.message = 'Resource conflict', super.statusCode = 409]);
}

class ValidationException extends ApiException {
  final List<ValidationError> errors;

  const ValidationException(
    super.message, {
    this.errors = const [],
    super.statusCode = 422,
  });
}

class ValidationError {
  final List<String> loc;
  final String msg;
  final String type;

  const ValidationError({
    this.loc = const [],
    this.msg = '',
    this.type = '',
  });
}

class NetworkException extends ApiException {
  const NetworkException([super.message = 'Network error']);
}

class RateLimitException extends ApiException {
  final int? retryAfterSeconds;

  const RateLimitException([
    super.message = 'Rate limit exceeded',
    this.retryAfterSeconds,
    super.statusCode = 429,
  ]);
}

class ServerException extends ApiException {
  const ServerException([super.message = 'Internal server error', super.statusCode = 500]);
}

class OfflineException extends ApiException {
  const OfflineException([super.message = 'Device is offline', super.statusCode = -1]);
}

ApiException parseApiError(Map<String, dynamic>? data, int? statusCode) {
  final message = data?['detail'] as String? ??
      data?['message'] as String? ??
      'Unknown error';

  switch (statusCode) {
    case 401:
      return AuthException(message);
    case 403:
      return UnauthorizedException(message);
    case 404:
      return NotFoundException(message);
    case 409:
      return ConflictException(message);
    case 422:
      return ValidationException(message,
          errors: _parseValidationErrors(data));
    case 429:
      return RateLimitException(message,
          retryAfterSeconds: data?['retry_after_seconds'] as int?);
    case 500:
    case 502:
    case 503:
      return ServerException(message);
    default:
      return ApiException(message, statusCode: statusCode, details: data);
  }
}

List<ValidationError> _parseValidationErrors(Map<String, dynamic>? data) {
  if (data == null) return [];
  final errors = <ValidationError>[];
  if (data['detail'] is List) {
    for (final e in data['detail'] as List) {
      if (e is Map<String, dynamic>) {
        errors.add(ValidationError(
          loc: List<String>.from(e['loc'] ?? []),
          msg: e['msg'] as String? ?? '',
          type: e['type'] as String? ?? '',
        ));
      }
    }
  }
  return errors;
}
