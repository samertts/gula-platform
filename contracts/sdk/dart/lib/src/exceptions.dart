class GulaException implements Exception {
  final String message;
  final int? statusCode;
  final Map<String, dynamic>? details;

  const GulaException(this.message, {this.statusCode, this.details});

  @override
  String toString() => 'GulaException($statusCode): $message';
}

class GulaAuthException extends GulaException {
  const GulaAuthException([super.message = 'Authentication required', super.statusCode = 401]);
}

class GulaUnauthorizedException extends GulaException {
  const GulaUnauthorizedException([super.message = 'Forbidden', super.statusCode = 403]);
}

class GulaNotFoundException extends GulaException {
  const GulaNotFoundException([super.message = 'Resource not found', super.statusCode = 404]);
}

class GulaConflictException extends GulaException {
  const GulaConflictException([super.message = 'Resource conflict', super.statusCode = 409]);
}

class GulaLockedException extends GulaException {
  const GulaLockedException([super.message = 'Resource is locked', super.statusCode = 423]);
}

class GulaValidationException extends GulaException {
  final List<ValidationError> errors;

  const GulaValidationException(
    super.message, {
    this.errors = const [],
    super.statusCode = 422,
  });

  factory GulaValidationException.fromResponse(Map<String, dynamic> json) {
    final errors = <ValidationError>[];
    if (json['detail'] is List) {
      for (final e in json['detail']) {
        errors.add(ValidationError(
          loc: List<String>.from(e['loc'] ?? []),
          msg: e['msg'] ?? '',
          type: e['type'] ?? '',
        ));
      }
    }
    return GulaValidationException(
      errors.isEmpty ? 'Validation failed' : errors.first.msg,
      errors: errors,
    );
  }
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

class GulaNetworkException extends GulaException {
  const GulaNetworkException([super.message = 'Network error']);
}

class GulaRateLimitException extends GulaException {
  final int? retryAfterSeconds;

  const GulaRateLimitException([
    super.message = 'Rate limit exceeded',
    this.retryAfterSeconds,
    super.statusCode = 429,
  ]);
}

class GulaServerException extends GulaException {
  const GulaServerException([super.message = 'Internal server error', super.statusCode = 500]);
}

class GulaOfflineException extends GulaException {
  const GulaOfflineException([super.message = 'Device is offline']);
}

GulaException parseDioError(dynamic error, int? statusCode) {
  switch (statusCode) {
    case 401:
      return GulaAuthException();
    case 403:
      return GulaUnauthorizedException();
    case 404:
      return GulaNotFoundException();
    case 409:
      return GulaConflictException();
    case 422:
      if (error is Map<String, dynamic>) {
        return GulaValidationException.fromResponse(error);
      }
      return GulaValidationException();
    case 423:
      return GulaLockedException();
    case 429:
      return GulaRateLimitException();
    case 500:
    case 502:
    case 503:
      return GulaServerException();
    default:
      return GulaException(
        error is Map<String, dynamic>
            ? '${error['detail'] ?? error['message'] ?? 'Unknown error'}'
            : '$error',
        statusCode: statusCode,
        details: error is Map<String, dynamic> ? error : null,
      );
  }
}
