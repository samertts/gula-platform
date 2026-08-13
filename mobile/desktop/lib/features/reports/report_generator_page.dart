import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/layout/page_container.dart';
import '../../widgets/layout/section_header.dart';

class ReportGeneratorPage extends StatefulWidget {
  const ReportGeneratorPage({super.key});

  @override
  State<ReportGeneratorPage> createState() => _ReportGeneratorPageState();
}

class _ReportGeneratorPageState extends State<ReportGeneratorPage> {
  String _reportType = 'Laboratory Summary';

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Generate Report',
            subtitle: 'Create a report from authorized laboratory data',
            trailing: GulaButton(
              label: 'Back to Reports',
              variant: GulaButtonVariant.outline,
              onPressed: () => context.go('/reports'),
            ),
          ),
          const SizedBox(height: 16),
          GulaCard(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Report Type',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    value: _reportType,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                    ),
                    items: const [
                      DropdownMenuItem(
                        value: 'Laboratory Summary',
                        child: Text('Laboratory Summary'),
                      ),
                      DropdownMenuItem(
                        value: 'Quality Control',
                        child: Text('Quality Control'),
                      ),
                      DropdownMenuItem(
                        value: 'Turnaround Time',
                        child: Text('Turnaround Time'),
                      ),
                    ],
                    onChanged: (value) {
                      if (value != null) {
                        setState(() => _reportType = value);
                      }
                    },
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Reports must be generated only from data the active user is authorized to access.',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 24),
                  GulaButton(
                    label: 'Generate',
                    icon: Icons.description_outlined,
                    onPressed: () => context.go('/reports/generated'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
