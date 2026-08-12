import 'package:intl/intl.dart';

import 'constants.dart';

class AppDateFormatter {
  AppDateFormatter._();

  static String formatFull(DateTime date, {String? locale}) {
    final fmt = DateFormat(AppConstants.dateFormatFull, locale ?? 'ar');
    return fmt.format(date);
  }

  static String formatDate(DateTime date, {String? locale}) {
    final fmt = DateFormat(AppConstants.dateFormatDate, locale ?? 'ar');
    return fmt.format(date);
  }

  static String formatTime(DateTime date, {String? locale}) {
    final fmt = DateFormat(AppConstants.dateFormatTime, locale ?? 'ar');
    return fmt.format(date);
  }

  static String formatShort(DateTime date, {String? locale}) {
    final fmt = DateFormat(AppConstants.dateFormatShort, locale ?? 'ar');
    return fmt.format(date);
  }

  static String formatDisplay(DateTime date, {String? locale}) {
    final fmt = DateFormat(AppConstants.dateFormatDisplay, locale ?? 'ar');
    return fmt.format(date);
  }

  static String formatDisplayArabic(DateTime date) {
    final fmt = DateFormat(AppConstants.dateFormatDisplayArabic, 'ar');
    return fmt.format(date);
  }

  static String formatRelative(DateTime date, {String? locale}) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inSeconds < 60) {
      return locale == 'ar' ? 'الآن' : 'Just now';
    } else if (diff.inMinutes < 60) {
      final minutes = diff.inMinutes;
      return locale == 'ar' ? 'قبل $minutes دقيقة' : '$minutes min ago';
    } else if (diff.inHours < 24) {
      final hours = diff.inHours;
      return locale == 'ar' ? 'قبل $hours ساعة' : '$hours hr ago';
    } else if (diff.inDays < 7) {
      final days = diff.inDays;
      return locale == 'ar' ? 'قبل $days يوم' : '$days days ago';
    } else {
      return formatDisplay(date, locale: locale);
    }
  }

  static String formatAge(DateTime birthDate, {String? locale}) {
    final now = DateTime.now();
    int years = now.year - birthDate.year;
    int months = now.month - birthDate.month;
    int days = now.day - birthDate.day;

    if (days < 0) {
      months--;
      days += DateTime(now.year, now.month, 0).day;
    }
    if (months < 0) {
      years--;
      months += 12;
    }

    if (years > 0) {
      return locale == 'ar'
          ? '$years سنة و $months شهر'
          : '$years yr, $months mo';
    } else if (months > 0) {
      return locale == 'ar'
          ? '$months شهر و $days يوم'
          : '$months mo, $days days';
    } else {
      return locale == 'ar' ? '$days يوم' : '$days days';
    }
  }

  static String formatDuration(Duration duration, {String? locale}) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes.remainder(60);
    final seconds = duration.inSeconds.remainder(60);

    if (hours > 0) {
      return locale == 'ar'
          ? '$hours ساعة $minutes دقيقة'
          : '${hours}h ${minutes}m';
    } else if (minutes > 0) {
      return locale == 'ar'
          ? '$minutes دقيقة $seconds ثانية'
          : '${minutes}m ${seconds}s';
    } else {
      return locale == 'ar' ? '$seconds ثانية' : '${seconds}s';
    }
  }

  static String toIso8601(DateTime date) => date.toIso8601String();

  static DateTime? parseIso8601(String date) => DateTime.tryParse(date);

  static String formatForApi(DateTime date) => date.toIso8601String();

  static DateTime parseFromApi(String date) => DateTime.parse(date);

  static String formatTimeSlot(DateTime start, DateTime end, {String? locale}) {
    final timeFmt = DateFormat('HH:mm', locale ?? 'ar');
    return '${timeFmt.format(start)} - ${timeFmt.format(end)}';
  }
}
