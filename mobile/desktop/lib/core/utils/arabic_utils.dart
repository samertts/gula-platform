class ArabicUtils {
  ArabicUtils._();

  static const Map<String, String> _englishToArabicNumbers = {
    '0': '٠',
    '1': '١',
    '2': '٢',
    '3': '٣',
    '4': '٤',
    '5': '٥',
    '6': '٦',
    '7': '٧',
    '8': '٨',
    '9': '٩',
  };

  static const Map<String, String> _arabicToEnglishNumbers = {
    '٠': '0',
    '١': '1',
    '٢': '2',
    '٣': '3',
    '٤': '4',
    '٥': '5',
    '٦': '6',
    '٧': '7',
    '٨': '8',
    '٩': '9',
  };

  static const Map<String, String> _easternArabicToWestern = {
    '٠': '0',
    '١': '1',
    '٢': '2',
    '٣': '3',
    '٤': '4',
    '٥': '5',
    '٦': '6',
    '٧': '7',
    '٨': '8',
    '٩': '9',
  };

  static const Map<String, String> _westernToEasternArabic = {
    '0': '٠',
    '1': '١',
    '2': '٢',
    '3': '٣',
    '4': '٤',
    '5': '٥',
    '6': '٦',
    '7': '٧',
    '8': '٨',
    '9': '٩',
  };

  static String toArabicNumbers(String text) {
    final buffer = StringBuffer();
    for (final char in text.runes) {
      final c = String.fromCharCode(char);
      buffer.write(_englishToArabicNumbers[c] ?? c);
    }
    return buffer.toString();
  }

  static String toEnglishNumbers(String text) {
    final buffer = StringBuffer();
    for (final char in text.runes) {
      final c = String.fromCharCode(char);
      buffer.write(_arabicToEnglishNumbers[c] ?? c);
    }
    return buffer.toString();
  }

  static String convertToArabicNumerals(String text) {
    return text.replaceAllMapped(
      RegExp(r'[0-9]'),
      (match) => _westernToEasternArabic[match.group(0)!]!,
    );
  }

  static String convertToEnglishNumerals(String text) {
    return text.replaceAllMapped(
      RegExp(r'[٠-٩]'),
      (match) => _easternArabicToWestern[match.group(0)!]!,
    );
  }

  static String normalizeArabic(String text) {
    return text
        .replaceAll('إ', 'ا')
        .replaceAll('أ', 'ا')
        .replaceAll('آ', 'ا')
        .replaceAll('ة', 'ه')
        .replaceAll('ى', 'ي')
        .replaceAll(RegExp(r'[ًٌٍَُِّْ]'), '')
        .trim();
  }

  static String stripDiacritics(String text) {
    return text.replaceAll(RegExp(r'[\u064B-\u065F\u0670]'), '');
  }

  static String removeTashkeel(String text) {
    return text.replaceAll(RegExp(r'[ًٌٍٍَُِّْ]'), '');
  }

  static bool containsArabic(String text) {
    return RegExp(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]').hasMatch(text);
  }

  static bool isArabicText(String text) {
    if (text.isEmpty) return false;
    final arabicChars = text.runes.where(
      (r) => r >= 0x0600 && r <= 0x06FF || r >= 0x0750 && r <= 0x077F || r >= 0x08A0 && r <= 0x08FF,
    ).length;
    return arabicChars > text.length * 0.5;
  }

  static String reverseWords(String text) {
    final words = text.split(' ');
    return words.reversed.join(' ');
  }

  static String formatCurrency(double amount, {bool arabic = true}) {
    final formatted = amount.toStringAsFixed(2);
    if (arabic) {
      return '${toArabicNumbers(formatted)} د.ع';
    }
    return '$formatted IQD';
  }

  static String formatPercentage(double value, {bool arabic = true}) {
    final formatted = value.toStringAsFixed(1);
    if (arabic) {
      return '${toArabicNumbers(formatted)}٪';
    }
    return '$formatted%';
  }

  static String genderLabel(String gender, {bool arabic = true}) {
    if (!arabic) return gender == 'm' ? 'Male' : 'Female';
    return gender == 'm' ? 'ذكر' : 'أنثى';
  }

  static String orderStatusLabel(String status, {bool arabic = true}) {
    if (!arabic) return status;
    switch (status) {
      case 'pending':
        return 'قيد الانتظار';
      case 'completed':
        return 'مكتمل';
      case 'validated':
        return 'معتمد';
      case 'cancelled':
        return 'ملغي';
      default:
        return status;
    }
  }

  static String sampleStatusLabel(String status, {bool arabic = true}) {
    if (!arabic) return status;
    switch (status) {
      case 'collected':
        return 'تم جمعها';
      case 'received':
        return 'تم استلامها';
      case 'processing':
        return 'قيد المعالجة';
      case 'analyzed':
        return 'تم التحليل';
      case 'rejected':
        return 'مرفوضة';
      default:
        return status;
    }
  }

  static String resultFlagLabel(String flag, {bool arabic = true}) {
    if (!arabic) {
      switch (flag) {
        case 'h':
          return 'High';
        case 'l':
          return 'Low';
        case 'normal':
          return 'Normal';
        case 'critical':
          return 'Critical';
        default:
          return flag;
      }
    }
    switch (flag) {
      case 'h':
        return 'مرتفع';
      case 'l':
        return 'منخفض';
      case 'normal':
        return 'طبيعي';
      case 'critical':
        return 'حرج';
      default:
        return flag;
    }
  }

  static String bloodGroupLabel(String group, {bool arabic = true}) {
    if (!arabic) return group;
    switch (group.toUpperCase()) {
      case 'A+':
        return 'فصيلة A موجب';
      case 'A-':
        return 'فصيلة A سالب';
      case 'B+':
        return 'فصيلة B موجب';
      case 'B-':
        return 'فصيلة B سالب';
      case 'AB+':
        return 'فصيلة AB موجب';
      case 'AB-':
        return 'فصيلة AB سالب';
      case 'O+':
        return 'فصيلة O موجب';
      case 'O-':
        return 'فصيلة O سالب';
      default:
        return group;
    }
  }
}
