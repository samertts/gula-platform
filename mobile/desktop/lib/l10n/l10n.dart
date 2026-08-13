import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/providers/app_providers.dart';

class AppLocalization {
  final Locale locale;

  AppLocalization(this.locale);

  static AppLocalization? of(BuildContext context) {
    return Localizations.of<AppLocalization>(context, AppLocalization);
  }

  static const LocalizationsDelegate<AppLocalization> delegate =
      _AppLocalizationDelegate();

  static const List<Locale> supportedLocales = [
    Locale('ar', 'IQ'),
    Locale('en', 'US'),
  ];

  static const Locale fallbackLocale = Locale('ar', 'IQ');

  static String? _getValue(String key, Map<String, dynamic> translations) {
    return translations[key] as String?;
  }

  String translate(String key) {
    final translations = locale.languageCode == 'ar'
        ? arTranslations
        : enTranslations;
    return _getValue(key, translations) ?? key;
  }

  static String tr(BuildContext context, String key) {
    final localization = of(context);
    return localization?.translate(key) ?? key;
  }

  static final Map<String, dynamic> arTranslations = {
    'appName': 'منصة GULA',
    'login': 'تسجيل الدخول',
    'logout': 'تسجيل الخروج',
    'email': 'البريد الإلكتروني',
    'password': 'كلمة المرور',
    'dashboard': 'لوحة التحكم',
    'patients': 'المرضى',
    'orders': 'الطلبات',
    'samples': 'العينات',
    'results': 'النتائج',
    'reports': 'التقارير',
    'notifications': 'الإشعارات',
    'settings': 'الإعدادات',
    'search': 'بحث',
    'save': 'حفظ',
    'cancel': 'إلغاء',
    'delete': 'حذف',
    'edit': 'تعديل',
    'print': 'طباعة',
    'noData': 'لا توجد بيانات',
    'loading': 'جارٍ التحميل...',
    'errorOccurred': 'حدث خطأ',
    'retry': 'إعادة المحاولة',
    'noInternet': 'لا يوجد اتصال بالإنترنت',
    'offline': 'غير متصل',
    'online': 'متصل',
    'sync': 'مزامنة',
  };

  static final Map<String, dynamic> enTranslations = {
    'appName': 'GULA Platform',
    'login': 'Login',
    'logout': 'Logout',
    'email': 'Email',
    'password': 'Password',
    'dashboard': 'Dashboard',
    'patients': 'Patients',
    'orders': 'Orders',
    'samples': 'Samples',
    'results': 'Results',
    'reports': 'Reports',
    'notifications': 'Notifications',
    'settings': 'Settings',
    'search': 'Search',
    'save': 'Save',
    'cancel': 'Cancel',
    'delete': 'Delete',
    'edit': 'Edit',
    'print': 'Print',
    'noData': 'No data available',
    'loading': 'Loading...',
    'errorOccurred': 'An error occurred',
    'retry': 'Retry',
    'noInternet': 'No internet connection',
    'offline': 'Offline',
    'online': 'Online',
    'sync': 'Sync',
  };
}

class _AppLocalizationDelegate extends LocalizationsDelegate<AppLocalization> {
  const _AppLocalizationDelegate();

  @override
  bool isSupported(Locale locale) {
    return ['ar', 'en'].contains(locale.languageCode);
  }

  @override
  Future<AppLocalization> load(Locale locale) async {
    return AppLocalization(locale);
  }

  @override
  bool shouldReload(_AppLocalizationDelegate old) => false;
}

extension AppLocalizationExtension on BuildContext {
  String tr(String key) => AppLocalization.tr(this, key);
}
