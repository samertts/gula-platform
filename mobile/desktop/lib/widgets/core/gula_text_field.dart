import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';

class GulaTextField extends StatelessWidget {
  final String? label;
  final String? hint;
  final String? errorText;
  final String? helperText;
  final TextEditingController? controller;
  final ValueChanged<String>? onChanged;
  final FormFieldSetter<String>? onSaved;
  final String? Function(String?)? validator;
  final TextInputType? keyboardType;
  final bool obscureText;
  final bool enabled;
  final bool readOnly;
  final bool autofocus;
  final int? maxLines;
  final int? minLines;
  final int? maxLength;
  final TextInputAction? textInputAction;
  final IconData? prefixIcon;
  final IconData? suffixIcon;
  final Widget? prefix;
  final Widget? suffix;
  final VoidCallback? onSuffixIconTap;
  final VoidCallback? onTap;
  final FocusNode? focusNode;
  final String? initialValue;
  final TextCapitalization textCapitalization;
  final double? borderRadius;
  final Color? fillColor;

  const GulaTextField({
    super.key,
    this.label,
    this.hint,
    this.errorText,
    this.helperText,
    this.controller,
    this.onChanged,
    this.onSaved,
    this.validator,
    this.keyboardType,
    this.obscureText = false,
    this.enabled = true,
    this.readOnly = false,
    this.autofocus = false,
    this.maxLines = 1,
    this.minLines,
    this.maxLength,
    this.textInputAction,
    this.prefixIcon,
    this.suffixIcon,
    this.prefix,
    this.suffix,
    this.onSuffixIconTap,
    this.onTap,
    this.focusNode,
    this.initialValue,
    this.textCapitalization = TextCapitalization.none,
    this.borderRadius,
    this.fillColor,
  });

  @override
  Widget build(BuildContext context) {
    final isRtl = Directionality.of(context) == TextDirection.rtl;
    final effectiveRadius = borderRadius ?? AppDimensions.radiusMd;

    return TextFormField(
      controller: controller,
      initialValue: initialValue,
      onChanged: onChanged,
      onSaved: onSaved,
      validator: validator,
      keyboardType: keyboardType,
      obscureText: obscureText,
      enabled: enabled,
      readOnly: readOnly,
      autofocus: autofocus,
      maxLines: maxLines,
      minLines: minLines,
      maxLength: maxLength,
      textInputAction: textInputAction,
      onTap: onTap,
      focusNode: focusNode,
      textCapitalization: textCapitalization,
      textDirection: isRtl ? TextDirection.rtl : TextDirection.ltr,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        errorText: errorText,
        helperText: helperText,
        prefixIcon: prefixIcon != null
            ? Icon(prefixIcon, size: 20, color: AppColors.textSecondary)
            : prefix,
        suffixIcon: suffixIcon != null
            ? InkWell(
                onTap: onSuffixIconTap,
                child: Icon(suffixIcon, size: 20, color: AppColors.textSecondary),
              )
            : suffix,
        filled: true,
        fillColor: fillColor ?? (enabled ? AppColors.surfaceLight : AppColors.neutral50),
        contentPadding: EdgeInsets.symmetric(
          horizontal: isRtl ? 16 : 12,
          vertical: 12,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(effectiveRadius),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(effectiveRadius),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(effectiveRadius),
          borderSide: const BorderSide(color: AppColors.primary500, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(effectiveRadius),
          borderSide: const BorderSide(color: AppColors.error500),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(effectiveRadius),
          borderSide: const BorderSide(color: AppColors.error500, width: 2),
        ),
        disabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(effectiveRadius),
          borderSide: const BorderSide(color: AppColors.neutral200),
        ),
        labelStyle: TextStyle(
          color: errorText != null ? AppColors.error500 : AppColors.textSecondary,
          fontSize: 14,
        ),
        hintStyle: const TextStyle(color: AppColors.neutral400, fontSize: 14),
        errorStyle: const TextStyle(color: AppColors.error500, fontSize: 12),
        helperStyle: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
        counterStyle: const TextStyle(color: AppColors.textSecondary, fontSize: 11),
      ),
    );
  }
}
