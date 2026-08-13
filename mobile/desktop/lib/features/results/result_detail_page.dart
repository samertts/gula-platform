import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/data/critical_value_flag.dart';
import '../../widgets/layout/page_container.dart';
import '../../widgets/layout/section_header.dart';

class ResultDetailPage extends StatelessWidget {
  final String resultId;
  const ResultDetailPage({super.key, required this.resultId});

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
                const SizedBox(width: 8),
                const Expanded(child: SectionHeader(title: 'Result Details')),
                GulaButton(label: 'Print', variant: GulaButtonVariant.outline, icon: Icons.print, onPressed: () {}),
                const SizedBox(width: 8),
                GulaButton(label: 'Validate', icon: Icons.verified, onPressed: () {}),
              ],
            ),
            const SizedBox(height: 16),
            GulaCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Test Information', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                  const Divider(height: 24),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          children: [
                            _row('Patient', 'Ahmed Ali'),
                            _row('Test', 'Hemoglobin'),
                            _row('Order #', 'ORD-2025-0891'),
                          ],
                        ),
                      ),
                      Expanded(
                        child: Column(
                          children: [
                            _row('Result', '14.2', Row(
                              children: [
                                const Text('14.2', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                                const SizedBox(width: 8),
                                const Text('g/dL', style: TextStyle(color: AppColors.textSecondary)),
                                const SizedBox(width: 12),
                                CriticalValueFlag(flag: 'normal'),
                              ],
                            )),
                            _row('Reference Range', '13.5 - 17.5'),
                            _row('Status', 'Pending', const GulaBadge(label: 'Pending', status: GulaBadgeStatus.pending)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            GulaCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Performed By', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                  const Divider(height: 24),
                  _row('Analyzed By', 'Tech. Ali'),
                  _row('Instrument', 'Sysmex XN-1000'),
                  _row('Date', '2025-03-21 11:30'),
                  const SizedBox(height: 16),
                  const Text('Validation', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                  const Divider(height: 24),
                  _row('Status', 'Pending Validation'),
                  _row('Validated By', '—'),
                  _row('Validated At', '—'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _row(String label, String value, [Widget? customValue]) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(width: 140, child: Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13))),
          Expanded(child: customValue ?? Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500))),
        ],
      ),
    );
  }
}
