import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/layout/page_container.dart';
import '../../widgets/layout/section_header.dart';

class ReportListPage extends StatelessWidget {
  const ReportListPage({super.key});

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Reports',
            subtitle: 'Generate, review, and export clinical reports',
            trailing: GulaButton(
              label: 'Generate Report',
              icon: Icons.add,
              onPressed: () => context.go('/reports/generate'),
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
                        Icons.assessment_outlined,
                        size: 56,
                        color: AppColors.neutral400,
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        'No reports yet',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Create a report to view it here.',
                        style: TextStyle(color: AppColors.textSecondary),
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
