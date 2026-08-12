import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';

import '../../core/theme/app_colors.dart';

enum GulaLoadingType { spinner, shimmer, skeleton, linear }

class GulaLoading extends StatelessWidget {
  final GulaLoadingType type;
  final String? message;
  final double? size;
  final Color? color;

  const GulaLoading({
    super.key,
    this.type = GulaLoadingType.spinner,
    this.message,
    this.size,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    switch (type) {
      case GulaLoadingType.spinner:
        return _buildSpinner(context);
      case GulaLoadingType.shimmer:
        return _buildShimmer();
      case GulaLoadingType.skeleton:
        return _buildSkeleton();
      case GulaLoadingType.linear:
        return _buildLinear(context);
    }
  }

  Widget _buildSpinner(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularProgressIndicator(
            strokeWidth: 3,
            valueColor: AlwaysStoppedAnimation<Color>(
              color ?? AppColors.primary500,
            ),
            strokeCap: StrokeCap.round,
          ),
          if (message != null) ...[
            const SizedBox(height: 16),
            Text(
              message!,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 14,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildShimmer() {
    return Shimmer.fromColors(
      baseColor: AppColors.neutral200,
      highlightColor: AppColors.neutral100,
      child: Column(
        children: List.generate(6, (index) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
          child: Container(
            height: 16,
            decoration: BoxDecoration(
              color: AppColors.neutral200,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
        )),
      ),
    );
  }

  Widget _buildSkeleton() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _skeletonBlock(width: 200, height: 20),
          const SizedBox(height: 16),
          _skeletonBlock(width: double.infinity, height: 14),
          const SizedBox(height: 8),
          _skeletonBlock(width: double.infinity, height: 14),
          const SizedBox(height: 8),
          _skeletonBlock(width: 300, height: 14),
          const SizedBox(height: 24),
          _skeletonBlock(width: double.infinity, height: 40),
          const SizedBox(height: 8),
          _skeletonBlock(width: double.infinity, height: 40),
          const SizedBox(height: 8),
          _skeletonBlock(width: double.infinity, height: 40),
        ],
      ),
    );
  }

  Widget _skeletonBlock({double? width, double? height}) {
    return Shimmer.fromColors(
      baseColor: AppColors.neutral200,
      highlightColor: AppColors.neutral100,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: AppColors.neutral200,
          borderRadius: BorderRadius.circular(4),
        ),
      ),
    );
  }

  Widget _buildLinear(BuildContext context) {
    return LinearProgressIndicator(
      backgroundColor: AppColors.primary100,
      valueColor: AlwaysStoppedAnimation<Color>(
        color ?? AppColors.primary500,
      ),
    );
  }
}
