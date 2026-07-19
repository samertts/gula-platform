import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_table.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';

class OrderDetailPage extends StatelessWidget {
  final String orderId;
  const OrderDetailPage({super.key, required this.orderId});

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
                const Expanded(child: SectionHeader(title: 'Order #ORD-2025-0891')),
                GulaButton(label: 'Print', variant: GulaButtonVariant.outline, icon: Icons.print, onPressed: () {}),
                const SizedBox(width: 8),
                GulaButton(label: 'Cancel', variant: GulaButtonVariant.danger, onPressed: () {}),
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
                        const Text('Order Information', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                        const Divider(height: 24),
                        _infoRow('Status', 'Pending', GulaBadge(label: 'Pending', status: GulaBadgeStatus.pending)),
                        _infoRow('Patient', 'Ahmed Ali'),
                        _infoRow('Doctor', 'Dr. Ali Hasan'),
                        _infoRow('Created', '2025-03-21 09:30'),
                        _infoRow('Priority', 'Routine'),
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
                        const Text('Test Results', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                        const Divider(height: 24),
                        _resultItem('Complete Blood Count', 'Completed'),
                        _resultItem('Liver Function Test', 'Pending'),
                        _resultItem('Lipid Profile', 'Pending'),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            GulaCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Samples', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                  const Divider(height: 24),
                  GulaTable(
                    columns: [
                      GulaTableColumn(key: 'barcode', label: 'Barcode', flex: 1),
                      GulaTableColumn(key: 'type', label: 'Type', flex: 1),
                      GulaTableColumn(key: 'status', label: 'Status', flex: 1),
                    ],
                    rows: [
                      {'barcode': 'BL20250321-001', 'type': 'Blood', 'status': 'Collected'},
                      {'barcode': 'BL20250321-002', 'type': 'Blood', 'status': 'Processing'},
                    ],
                    onRefresh: () {},
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _infoRow(String label, String value, [Widget? badge]) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(width: 100, child: Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13))),
          badge ?? Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  Widget _resultItem(String test, String status) {
    return ListTile(
      dense: true,
      title: Text(test, style: const TextStyle(fontSize: 13)),
      trailing: GulaBadge(label: status, status: status == 'Completed' ? GulaBadgeStatus.success : GulaBadgeStatus.pending),
    );
  }
}
