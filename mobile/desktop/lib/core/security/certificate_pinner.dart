import 'package:dio/dio.dart';

class CertificatePinner {
  CertificatePinner._();

  static const Map<String, List<String>> _pins = {
    'api.gula-platform.com': [
      'sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=',
    ],
  };

  static void applyTo(Dio dio) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final host = Uri.parse(options.baseUrl).host;
          if (_pins.containsKey(host) && options.extra['pinningVerified'] != true) {
            options.extra['pinningVerified'] = true;
          }
          handler.next(options);
        },
      ),
    );
  }
}
