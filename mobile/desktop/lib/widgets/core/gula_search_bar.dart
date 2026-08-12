import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../core/utils/constants.dart';

class GulaSearchBar extends StatefulWidget {
  final String hint;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final VoidCallback? onClear;
  final bool autoFocus;
  final TextEditingController? controller;
  final double? width;
  final double? height;
  final List<String>? suggestions;

  const GulaSearchBar({
    super.key,
    this.hint = 'Search...',
    this.onChanged,
    this.onSubmitted,
    this.onClear,
    this.autoFocus = false,
    this.controller,
    this.width,
    this.height,
    this.suggestions,
  });

  @override
  State<GulaSearchBar> createState() => _GulaSearchBarState();
}

class _GulaSearchBarState extends State<GulaSearchBar> {
  late TextEditingController _controller;
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _controller = widget.controller ?? TextEditingController();
  }

  @override
  void dispose() {
    if (widget.controller == null) {
      _controller.dispose();
    }
    _debounce?.cancel();
    super.dispose();
  }

  void _onSearchChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(
      const Duration(milliseconds: AppConstants.searchDebounceMilliseconds),
      () {
        widget.onChanged?.call(value);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: widget.width,
      height: widget.height ?? 40,
      child: TextField(
        controller: _controller,
        autofocus: widget.autoFocus,
        onChanged: _onSearchChanged,
        onSubmitted: widget.onSubmitted,
        textInputAction: TextInputAction.search,
        decoration: InputDecoration(
          hintText: widget.hint,
          prefixIcon: const Icon(Icons.search, size: 20, color: AppColors.textSecondary),
          suffixIcon: _controller.text.isNotEmpty
              ? IconButton(
                  icon: const Icon(Icons.clear, size: 18, color: AppColors.textSecondary),
                  onPressed: () {
                    _controller.clear();
                    widget.onClear?.call();
                    widget.onChanged?.call('');
                  },
                )
              : null,
          filled: true,
          fillColor: AppColors.neutral50,
          contentPadding: const EdgeInsets.symmetric(vertical: 10),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppDimensions.radiusLg),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppDimensions.radiusLg),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppDimensions.radiusLg),
            borderSide: const BorderSide(color: AppColors.primary500),
          ),
        ),
      ),
    );
  }
}
