import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/layout/page_container.dart';
import '../../widgets/layout/section_header.dart';

class SampleDetailPage extends StatelessWidget {
  final String sampleId;
  const SampleDetailPage({super.key, required this.sampleId});

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
                const Expanded(child: SectionHeader(title: 'Sample BL20250321-001')),
                GulaButton(label: 'Print Label', variant: GulaButtonVariant.outline, icon: Icons.print, onPressed: () {}),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: GulaCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Sample Information', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                        const Divider(height: 24),
                        _row('Barcode', 'BL20250321-001'),
                        _row('Type', 'Blood'),
                        _row('Status', 'Processing', const GulaBadge(label: 'Processing', status: GulaBadgeStatus.warning)),
                        _row('Container', 'EDTA Tube'),
                        _row('Volume', '5 mL'),
                        _row('Patient', 'Ahmed Ali'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: GulaCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Collection Details', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                        const Divider(height: 24),
                        _row('Collected By', 'Nurse Fatima'),
                        _row('Collected At', '2025-03-21 09:35'),
                        _row('Received By', 'Tech. Ali'),
                        _row('Received At', '2025-03-21 10:00'),
                        _row('Location', 'Room 2, Fridge B3'),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _row(String label, String value, [Widget? badge]) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(width: 120, child: Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13))),
          badge ?? Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
