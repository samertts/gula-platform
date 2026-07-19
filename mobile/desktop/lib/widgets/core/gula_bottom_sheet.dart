import 'package:flutter/material.dart';

import '../../core/theme/app_dimensions.dart';

class GulaBottomSheet {
  static Future<T?> show<T>(
    BuildContext context, {
    required Widget child,
    String? title,
    double? height,
    bool isDismissible = true,
    bool showDragHandle = true,
  }) {
    return showModalBottomSheet<T>(
      context: context,
      isScrollControlled: true,
      isDismissible: isDismissible,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(AppDimensions.radiusXl),
        ),
      ),
      builder: (context) => Container(
        constraints: BoxConstraints(
          maxHeight: height ?? MediaQuery.of(context).size.height * 0.85,
        ),
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (showDragHandle)
              Container(
                margin: const EdgeInsets.only(top: 8, bottom: 4),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            if (title != null)
              Padding(
                padding: const EdgeInsets.all(AppDimensions.space4),
                child: Text(
                  title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            Flexible(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(
                  AppDimensions.space4,
                  0,
                  AppDimensions.space4,
                  AppDimensions.space4,
                ),
                child: child,
              ),
            ),
          ],
        ),
      ),
    );
  }

  static Future<T?> showOptions<T>(
    BuildContext context, {
    required String title,
    required List<BottomSheetOption<T>> options,
  }) {
    return show<T>(
      context,
      title: title,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: options.map((option) => ListTile(
          leading: option.icon != null ? Icon(option.icon) : null,
          title: Text(option.label),
          subtitle: option.subtitle != null ? Text(option.subtitle!) : null,
          trailing: option.trailing,
          onTap: () {
            Navigator.of(context).pop(option.value);
          },
        )).toList(),
      ),
    );
  }
}

class BottomSheetOption<T> {
  final String label;
  final String? subtitle;
  final IconData? icon;
  final Widget? trailing;
  final T value;

  BottomSheetOption({
    required this.label,
    this.subtitle,
    this.icon,
    this.trailing,
    required this.value,
  });
}
