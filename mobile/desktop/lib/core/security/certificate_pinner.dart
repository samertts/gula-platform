import 'package:dio/dio.dart';

/// Desktop certificate pinning must be implemented by a native transport
/// adapter before it is enabled. The previous interceptor only marked a
/// request as verified and did not inspect the peer certificate.
class CertificatePinner {
  CertificatePinner._();

  static const String productionHost = 'api.gula-platform.org';

  /// Fail closed rather than providing a false security guarantee.
  ///
  /// `ApiClient.enableCertificatePinning` remains disabled by default. If a
  /// desktop release enables it before a native SPKI-pinning adapter is wired,
  /// requests fail immediately instead of silently proceeding without pinning.
  static void applyTo(Dio dio) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final uri = options.uri;
          final isProductionHttps =
              uri.scheme == 'https' && uri.host == productionHost;

          handler.reject(
            DioException(
              requestOptions: options,
              error: StateError(
                isProductionHttps
                    ? 'Native certificate pinning adapter is not configured for desktop.'
                    : 'Certificate pinning is restricted to the production API host.',
              ),
              type: DioExceptionType.unknown,
            ),
          );
        },
      ),
    );
  }
}
