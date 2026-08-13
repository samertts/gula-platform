import 'package:flutter/foundation.dart';

const String productionApiHost = 'api.gula-platform.org';
const Set<String> _debugHttpsHosts = {
  productionApiHost,
  'staging-api.gula-platform.com',
};
const Set<String> _localHosts = {'localhost', '127.0.0.1', '::1', '10.0.2.2'};

bool isApprovedApiRequest(Uri uri, {bool allowDebugEndpoints = kDebugMode}) {
  final host = uri.host.toLowerCase().replaceFirst(RegExp(r'\.$'), '');
  final isProduction =
      uri.scheme == 'https' &&
      host == productionApiHost &&
      (uri.port == 0 || uri.port == 443);
  final isDebugHttps =
      allowDebugEndpoints &&
      uri.scheme == 'https' &&
      _debugHttpsHosts.contains(host) &&
      (uri.port == 0 || uri.port == 443);
  final isLocal =
      allowDebugEndpoints &&
      uri.scheme == 'http' &&
      _localHosts.contains(host) &&
      (uri.port == 0 || uri.port == 8000 || uri.port == 8080);
  return uri.userInfo.isEmpty &&
      uri.fragment.isEmpty &&
      (isProduction || isDebugHttps || isLocal);
}

String validateApiBaseUrl(
  String rawUrl, {
  bool allowDebugEndpoints = kDebugMode,
}) {
  final trimmed = rawUrl.trim();
  final uri = Uri.tryParse(trimmed);
  if (uri == null || !uri.hasScheme || uri.host.isEmpty) {
    throw const FormatException('API URL must be an absolute URL');
  }
  if (uri.userInfo.isNotEmpty ||
      uri.query.isNotEmpty ||
      uri.fragment.isNotEmpty) {
    throw const FormatException(
      'API URL must not contain credentials, query, or fragment',
    );
  }

  final host = uri.host.toLowerCase().replaceFirst(RegExp(r'\.$'), '');
  final isProduction =
      uri.scheme == 'https' &&
      host == productionApiHost &&
      (uri.port == 0 || uri.port == 443) &&
      uri.path.startsWith('/api/v1');
  final isDebugHttps =
      allowDebugEndpoints &&
      uri.scheme == 'https' &&
      _debugHttpsHosts.contains(host) &&
      (uri.port == 0 || uri.port == 443) &&
      uri.path.startsWith('/api/v1');
  final isLocal =
      allowDebugEndpoints &&
      uri.scheme == 'http' &&
      _localHosts.contains(host) &&
      (uri.port == 0 || uri.port == 8000 || uri.port == 8080);

  if (!isProduction && !isDebugHttps && !isLocal) {
    throw const FormatException('API URL is not an approved endpoint');
  }

  final normalizedPath = uri.path.replaceFirst(RegExp(r'/+$'), '');
  return uri
      .replace(path: normalizedPath.isEmpty ? '/' : normalizedPath)
      .toString();
}
