import 'constants.dart';

class AppValidators {
  AppValidators._();

  static String? required(String? value, {String? fieldName}) {
    if (value == null || value.trim().isEmpty) {
      return fieldName != null ? '$fieldName مطلوب' : 'هذا الحقل مطلوب';
    }
    return null;
  }

  static String? email(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    if (!AppConstants.emailRegex.hasMatch(value.trim())) {
      return 'البريد الإلكتروني غير صالح';
    }
    return null;
  }

  static String? phone(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    final cleaned = value.replaceAll(RegExp(r'[\s\-\(\)]'), '');
    if (!AppConstants.phoneRegex.hasMatch(cleaned)) {
      return 'رقم الهاتف غير صالح';
    }
    return null;
  }

  static String? nationalId(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    final cleaned = value.replaceAll(RegExp(r'[\s\-]'), '');
    if (!AppConstants.iqNationalIdRegex.hasMatch(cleaned)) {
      return 'الرقم الوطني يجب أن يكون 14 رقمًا';
    }
    return null;
  }

  static String? password(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    if (value.length < 8) {
      return 'كلمة المرور يجب أن تكون 8 أحرف على الأقل';
    }
    if (!RegExp(r'[A-Z]').hasMatch(value)) {
      return 'يجب أن تحتوي على حرف كبير واحد على الأقل';
    }
    if (!RegExp(r'[a-z]').hasMatch(value)) {
      return 'يجب أن تحتوي على حرف صغير واحد على الأقل';
    }
    if (!RegExp(r'[0-9]').hasMatch(value)) {
      return 'يجب أن تحتوي على رقم واحد على الأقل';
    }
    return null;
  }

  static String? confirmPassword(String? value, String? original) {
    if (value == null || value.trim().isEmpty) return null;
    if (value != original) {
      return 'كلمة المرور غير متطابقة';
    }
    return null;
  }

  static String? sampleBarcode(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    if (!AppConstants.sampleBarcodeRegex.hasMatch(value.trim())) {
      return 'باركود العينة غير صالح';
    }
    return null;
  }

  static String? numeric(String? value, {String? fieldName}) {
    if (value == null || value.trim().isEmpty) return null;
    if (!RegExp(r'^\d+(\.\d+)?$').hasMatch(value.trim())) {
      return fieldName != null ? '$fieldName يجب أن يكون رقمًا' : 'يجب أن يكون رقمًا';
    }
    return null;
  }

  static String? minLength(String? value, int min, {String? fieldName}) {
    if (value == null || value.trim().isEmpty) return null;
    if (value.trim().length < min) {
      return fieldName != null
          ? '$fieldName يجب أن يكون $min أحرف على الأقل'
          : 'يجب أن يكون $min أحرف على الأقل';
    }
    return null;
  }

  static String? maxLength(String? value, int max, {String? fieldName}) {
    if (value == null || value.trim().isEmpty) return null;
    if (value.trim().length > max) {
      return fieldName != null
          ? '$fieldName يجب أن لا يتجاوز $max حرفًا'
          : 'يجب أن لا يتجاوز $max حرفًا';
    }
    return null;
  }

  static String? range(String? value, num min, num max, {String? fieldName}) {
    if (value == null || value.trim().isEmpty) return null;
    final num? parsed = num.tryParse(value.trim());
    if (parsed == null) {
      return fieldName != null ? '$fieldName يجب أن يكون رقمًا' : 'يجب أن يكون رقمًا';
    }
    if (parsed < min || parsed > max) {
      return fieldName != null
          ? '$fieldName يجب أن يكون بين $min و $max'
          : 'يجب أن يكون بين $min و $max';
    }
    return null;
  }

  static String? url(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    final uri = Uri.tryParse(value.trim());
    if (uri?.hasScheme != true) {
      return 'رابط غير صالح';
    }
    return null;
  }

  static String? hcvCode(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    if (!AppConstants.hcvCodeRegex.hasMatch(value.trim())) {
      return 'رمز HCV غير صالح';
    }
    return null;
  }

  static String? requiredDropDown(dynamic value, {String? fieldName}) {
    if (value == null) {
      return fieldName != null ? 'يرجى اختيار $fieldName' : 'يرجى الاختيار';
    }
    return null;
  }

  static String? combined(List<String? Function()> validators) {
    for (final validator in validators) {
      final result = validator();
      if (result != null) return result;
    }
    return null;
  }
}
