import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import 'api_exceptions.dart';
import '../security/api_url_validator.dart';

class EndpointGuardInterceptor extends Interceptor {
  final bool allowDebugEndpoints;

  EndpointGuardInterceptor({this.allowDebugEndpoints = kDebugMode});

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (isApprovedApiRequest(
      options.uri,
      allowDebugEndpoints: allowDebugEndpoints,
    )) {
      handler.next(options);
      return;
    }

    handler.reject(
      DioException(
        requestOptions: options,
        error: StateError('Request target is not an approved API endpoint.'),
        type: DioExceptionType.unknown,
      ),
    );
  }
}

class AuthInterceptor extends Interceptor {
  final Dio dio;
  final String Function() getToken;
  final String Function()? getRefreshToken;
  final Future<bool> Function()? onRefreshToken;
  final void Function()? onAuthFailure;

  AuthInterceptor({
    required this.dio,
    required this.getToken,
    this.getRefreshToken,
    this.onRefreshToken,
    this.onAuthFailure,
  });

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = getToken();
    if (token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    options.headers['Accept'] = 'application/json';
    options.headers['Content-Type'] = 'application/json';
    options.headers['Accept-Language'] = 'ar';
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401 &&
        err.requestOptions.extra['skipAuthRefresh'] != true &&
        getRefreshToken != null) {
      final refreshToken = getRefreshToken!();
      if (refreshToken.isNotEmpty && onRefreshToken != null) {
        try {
          final refreshed = await onRefreshToken!();
          if (refreshed) {
            final opts = err.requestOptions;
            opts.headers['Authorization'] = 'Bearer ${getToken()}';
            try {
              final response = await dio.fetch(opts);
              handler.resolve(response);
              return;
            } catch (_) {}
          }
        } catch (_) {
          onAuthFailure?.call();
        }
      }
    }
    handler.next(err);
  }
}

class RetryInterceptor extends Interceptor {
  final Dio dio;
  final int maxRetries;

  RetryInterceptor({required this.dio, this.maxRetries = 3});

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (_isRetryable(err)) {
      final retryCount = err.requestOptions.extra['retryCount'] as int? ?? 0;
      if (retryCount < maxRetries) {
        err.requestOptions.extra['retryCount'] = retryCount + 1;
        await Future.delayed(Duration(seconds: (retryCount + 1) * 2));
        try {
          final response = await dio.fetch(err.requestOptions);
          handler.resolve(response);
          return;
        } catch (_) {}
      }
    }
    handler.next(err);
  }

  bool _isRetryable(DioException err) {
    return err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.connectionError ||
        err.type == DioExceptionType.badResponse &&
            err.response != null &&
            err.response!.statusCode! >= 500 &&
            err.response!.statusCode! <= 599;
  }
}

class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    debugPrint('[API →] ${options.method} ${options.uri}');
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    debugPrint('[API ←] ${response.statusCode} ${response.requestOptions.uri}');
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    debugPrint(
      '[API ✗] ${err.response?.statusCode} ${err.requestOptions.uri}: ${err.message}',
    );
    handler.next(err);
  }
}

class ErrorMappingInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final data = err.response?.data;
    final map = data is Map<String, dynamic> ? data : null;
    final statusCode = err.response?.statusCode;

    if (err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.receiveTimeout) {
      handler.reject(
        DioException(
          requestOptions: err.requestOptions,
          error: NetworkException('Connection timed out'),
          type: err.type,
        ),
      );
      return;
    }

    if (err.type == DioExceptionType.connectionError) {
      handler.reject(
        DioException(
          requestOptions: err.requestOptions,
          error: NetworkException('No internet connection'),
          type: err.type,
        ),
      );
      return;
    }

    final apiError = parseApiError(map, statusCode);
    handler.reject(
      DioException(
        requestOptions: err.requestOptions,
        error: apiError,
        response: err.response,
        type: err.type,
      ),
    );
  }
}
