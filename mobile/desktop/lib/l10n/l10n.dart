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
    Locale('ar'),
    Locale('en', 'US'),
    Locale('ku'),
    Locale('tk'),
    Locale('syr'),
    Locale('fa'),
  ];

  static const Locale fallbackLocale = Locale('ar', 'IQ');

  static String? _getValue(String key, Map<String, dynamic> translations) {
    return translations[key] as String?;
  }

  String translate(String key) {
    final translations = switch (locale.languageCode) {
      'ar' => arTranslations,
      'ku' => kuTranslations,
      'tk' => tkTranslations,
      'syr' => syrTranslations,
      'fa' => faTranslations,
      _ => enTranslations,
    };
    return _getValue(key, translations) ??
        _getValue(key, enTranslations) ??
        key;
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
    'memberships': 'العضويات والسياقات',
    'workspace': 'مساحة العمل',
    'securityCenter': 'مركز الأمان',
    'sessionExpired': 'انتهت الجلسة. يرجى تسجيل الدخول مجدداً.',
    'accountRequestPending': 'تم استلام طلب الحساب وهو قيد المراجعة.',
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
    'memberships': 'Memberships & Contexts',
    'workspace': 'Workspace',
    'securityCenter': 'Security Center',
    'sessionExpired': 'Your session expired. Please sign in again.',
    'accountRequestPending':
        'Your account request was received and is pending review.',
  };

  static final Map<String, dynamic> kuTranslations = {
    'appName': 'پلاتفۆرمی GULA',
    'login': 'چوونەژوورەوە',
    'logout': 'دەرچوون',
    'memberships': 'ئەندامێتی و کۆنتێکست',
    'workspace': 'شوێنی کار',
    'securityCenter': 'ناوەندی ئاسایش',
  };
  static final Map<String, dynamic> tkTranslations = {
    'appName': 'GULA Platformasy',
    'login': 'Ulgama girmek',
    'logout': 'Çykmak',
    'memberships': 'Agzalyk we kontekstler',
    'workspace': 'Iş meýdany',
    'securityCenter': 'Howpsuzlyk merkezi',
  };
  static final Map<String, dynamic> syrTranslations = {
    'appName': 'ܦܠܛܦܘܪܡܐ ܕܓܘܠܐ',
    'login': 'ܥܘܠ ܠܢܝܫܡܐ',
    'logout': 'ܦܘܩ',
    'memberships': 'ܚܒܪܘܬܐ ܘܩܢܛܟܣܛ',
    'workspace': 'ܦܢܝܬܐ ܕܦܘܠܚܢܐ',
    'securityCenter': 'ܡܨܥܬܐ ܕܚܘܣܝܢܐ',
  };
  static final Map<String, dynamic> faTranslations = {
    'appName': 'پلتفرم GULA',
    'login': 'ورود',
    'logout': 'خروج',
    'memberships': 'عضویت‌ها و زمینه‌ها',
    'workspace': 'فضای کاری',
    'securityCenter': 'مرکز امنیت',
  };
}

class _AppLocalizationDelegate extends LocalizationsDelegate<AppLocalization> {
  const _AppLocalizationDelegate();

  @override
  bool isSupported(Locale locale) {
    return ['ar', 'en', 'ku', 'tk', 'syr', 'fa'].contains(locale.languageCode);
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
