import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import 'gula_button.dart';

class GulaDialog {
  static Future<T?> show<T>(BuildContext context, {
    required String title,
    required Widget content,
    String? confirmLabel,
    String? cancelLabel,
    VoidCallback? onConfirm,
    VoidCallback? onCancel,
    Color? confirmColor,
    bool showCancel = true,
    bool isDismissible = true,
    bool isDestructive = false,
  }) {
    return showDialog<T>(
      context: context,
      barrierDismissible: isDismissible,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: content,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusXl),
        ),
        actions: [
          if (showCancel)
            GulaButton(
              label: cancelLabel ?? 'Cancel',
              variant: GulaButtonVariant.text,
              onPressed: () {
                onCancel?.call();
                Navigator.of(context).pop();
              },
            ),
          GulaButton(
            label: confirmLabel ?? 'Confirm',
            variant: isDestructive ? GulaButtonVariant.danger : GulaButtonVariant.primary,
            color: confirmColor,
            onPressed: () {
              onConfirm?.call();
              Navigator.of(context).pop(true);
            },
          ),
        ],
      ),
    );
  }

  static Future<bool?> confirm(
    BuildContext context, {
    required String title,
    required String message,
    String confirmLabel = 'Confirm',
    String cancelLabel = 'Cancel',
    bool isDestructive = false,
  }) {
    return show<bool>(
      context,
      title: title,
      content: Text(message),
      confirmLabel: confirmLabel,
      cancelLabel: cancelLabel,
      isDestructive: isDestructive,
    );
  }

  static Future<bool?> delete(
    BuildContext context, {
    required String title,
    required String message,
    String confirmLabel = 'Delete',
  }) {
    return confirm(
      context,
      title: title,
      message: message,
      confirmLabel: confirmLabel,
      isDestructive: true,
    );
  }

  static void showInfo(
    BuildContext context, {
    required String title,
    required String message,
  }) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            const Icon(Icons.info_outline, color: AppColors.info500),
            const SizedBox(width: 8),
            Text(title),
          ],
        ),
        content: Text(message),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusXl),
        ),
        actions: [
          GulaButton(
            label: 'OK',
            onPressed: () => Navigator.of(context).pop(),
          ),
        ],
      ),
    );
  }

  static void showError(
    BuildContext context, {
    required String title,
    required String message,
  }) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            const Icon(Icons.error_outline, color: AppColors.error500),
            const SizedBox(width: 8),
            Text(title),
          ],
        ),
        content: Text(message),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppDimensions.radiusXl),
        ),
        actions: [
          GulaButton(
            label: 'OK',
            onPressed: () => Navigator.of(context).pop(),
          ),
        ],
      ),
    );
  }

  static Future<T?> showCustom<T>(
    BuildContext context, {
    required WidgetBuilder builder,
    bool isDismissible = true,
  }) {
    return showDialog<T>(
      context: context,
      barrierDismissible: isDismissible,
      builder: builder,
    );
  }
}
