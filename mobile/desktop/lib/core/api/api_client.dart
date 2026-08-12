import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import 'api_interceptor.dart';
import 'api_exceptions.dart';
import '../security/certificate_pinner.dart';

class ApiClient {
  late final Dio _dio;
  final String baseUrl;
  final String Function() getToken;
  final String Function() getRefreshToken;
  final Future<bool> Function() onRefreshToken;
  final void Function() onAuthFailure;
  final bool enableLogging;
  final bool enableCertificatePinning;
  final Duration connectTimeout;
  final Duration receiveTimeout;
  final Duration sendTimeout;

  ApiClient({
    required this.baseUrl,
    required this.getToken,
    required this.getRefreshToken,
    required this.onRefreshToken,
    required this.onAuthFailure,
    this.enableLogging = kDebugMode,
    this.enableCertificatePinning = false,
    this.connectTimeout = const Duration(seconds: 15),
    this.receiveTimeout = const Duration(seconds: 30),
    this.sendTimeout = const Duration(seconds: 15),
  }) {
    _initialize();
  }

  Dio get dio => _dio;

  void _initialize() {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: connectTimeout,
        receiveTimeout: receiveTimeout,
        sendTimeout: sendTimeout,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Accept-Language': 'ar',
        },
      ),
    );

    _dio.interceptors.addAll([
      AuthInterceptor(
        getToken: getToken,
        getRefreshToken: getRefreshToken,
        onRefreshToken: onRefreshToken,
        onAuthFailure: onAuthFailure,
      ),
      RetryInterceptor(dio: _dio, maxRetries: 3),
      ErrorMappingInterceptor(),
      if (enableLogging) LoggingInterceptor(),
    ]);

    if (enableCertificatePinning) {
      CertificatePinner.applyTo(_dio);
    }
  }

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    bool idempotent = false,
  }) {
    final opts = (options ?? Options()).copyWith();
    if (idempotent) {
      opts.extra ??= {};
      opts.extra!['idempotent'] = true;
    }
    return _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: opts,
      cancelToken: cancelToken,
    );
  }

  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.put<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.patch<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  Future<Response<T>> delete<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) {
    return _dio.delete<T>(
      path,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  Future<Response<List<int>>> download(
    String url, {
    Map<String, dynamic>? queryParameters,
    CancelToken? cancelToken,
  }) {
    return _dio.get<List<int>>(
      url,
      queryParameters: queryParameters,
      options: Options(responseType: ResponseType.bytes),
      cancelToken: cancelToken,
    );
  }

  void dispose() {
    _dio.close();
  }
}
