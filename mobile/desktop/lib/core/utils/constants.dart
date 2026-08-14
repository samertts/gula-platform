class AppConstants {
  AppConstants._();

  static const String appName = 'GULA Platform';
  static const String appVersion = '2.5.0';
  static const String appBuildNumber = '1';
  static const String packageName = 'com.gula.platform.desktop';
  static const String companyName = 'GULA Platform';
  static const String copyright =
      'Copyright © 2025 GULA Platform. All rights reserved.';

  static const String defaultApiUrl = 'https://api.gula-platform.org/api/v1';
  static const String sentryDsn = '';
  static const String syncChannelName = 'gula_sync';

  static const int connectTimeoutSeconds = 15;
  static const int receiveTimeoutSeconds = 30;
  static const int sendTimeoutSeconds = 15;
  static const int maxRetries = 3;
  static const int retryBaseDelaySeconds = 2;

  static const int syncIntervalSeconds = 30;
  static const int conflictRetryMaxAttempts = 5;
  static const int syncBatchSize = 100;

  static const int maxLoginAttempts = 5;
  static const int lockoutDurationMinutes = 15;
  static const int sessionTimeoutMinutes = 120;

  static const int searchDebounceMilliseconds = 300;
  static const int maxSearchResults = 50;
  static const int defaultPageSize = 50;

  static const int cacheMaxAgeDays = 30;
  static const int offlineDataMaxAgeDays = 90;

  static const int kpiRefreshSeconds = 60;
  static const int notificationPollSeconds = 30;
  static const int healthCheckSeconds = 60;

  static const String appStoreUrl =
      'https://apps.apple.com/app/gula-platform/id0000000000';
  static const String playStoreUrl =
      'https://github.com/samertts/gula-platform/releases';
  static const String githubReleaseUrl =
      'https://github.com/samertts/gula-platform/releases';
  static const String supportEmail = 'support@gula-platform.com';
  static const String privacyPolicyUrl = 'https://gula-platform.com/privacy';
  static const String termsOfServiceUrl = 'https://gula-platform.com/terms';

  static const String dateFormatFull = 'yyyy-MM-dd HH:mm:ss';
  static const String dateFormatDate = 'yyyy-MM-dd';
  static const String dateFormatTime = 'HH:mm:ss';
  static const String dateFormatShort = 'yyyy-MM-dd HH:mm';
  static const String dateFormatArabic = 'yyyy/MM/dd';
  static const String dateFormatArabicFull = 'yyyy/MM/dd HH:mm:ss';
  static const String dateFormatDisplay = 'dd MMM yyyy';
  static const String dateFormatDisplayArabic = 'dd MMMM yyyy';

  static const double minDesktopWidth = 800;
  static const double minDesktopHeight = 600;
  static const double defaultDesktopWidth = 1280;
  static const double defaultDesktopHeight = 800;

  static final RegExp nationalIdRegex = RegExp(r'^\d{14}$');
  static final RegExp phoneRegex = RegExp(r'^\+?964\d{10}$');
  static final RegExp emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
  static final RegExp iqNationalIdRegex = RegExp(r'^\d{14}$');
  static final RegExp sampleBarcodeRegex = RegExp(r'^[A-Z0-9]{6,20}$');
  static final RegExp hcvCodeRegex = RegExp(r'^[A-Z]{2}\d{8}$');
}
