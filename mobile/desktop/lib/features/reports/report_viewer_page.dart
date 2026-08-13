import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/layout/page_container.dart';
import '../../widgets/layout/section_header.dart';

class ReportViewerPage extends StatelessWidget {
  final String reportId;

  const ReportViewerPage({
    super.key,
    required this.reportId,
  });

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Report $reportId',
            subtitle: 'Report details are loaded from an authorized source',
            trailing: GulaButton(
              label: 'Back to Reports',
              variant: GulaButtonVariant.outline,
              onPressed: () => context.go('/reports'),
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: Center(
              child: GulaCard(
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.description_outlined,
                        size: 56,
                        color: AppColors.neutral400,
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        'Report preview',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Report identifier: $reportId',
                        style: const TextStyle(color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
