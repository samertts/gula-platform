import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';

class PatientDetailPage extends StatelessWidget {
  final String patientId;

  const PatientDetailPage({super.key, required this.patientId});

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back),
                  onPressed: () => context.pop(),
                ),
                const SizedBox(width: 8),
                const Expanded(child: SectionHeader(title: 'Patient Details')),
                GulaButton(
                  label: 'Edit',
                  variant: GulaButtonVariant.outline,
                  icon: Icons.edit,
                  onPressed: () {},
                ),
                const SizedBox(width: 8),
                GulaButton(
                  label: 'New Order',
                  icon: Icons.add,
                  onPressed: () {},
                ),
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
                        Row(
                          children: [
                            const CircleAvatar(
                              radius: 32,
                              backgroundColor: AppColors.primary100,
                              child: Icon(
                                Icons.person,
                                size: 32,
                                color: AppColors.primary700,
                              ),
                            ),
                            const SizedBox(width: 16),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Ahmed Jasim Al-Tamimi',
                                  style: TextStyle(
                                    fontSize: 20,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    const GulaBadge(
                                      label: 'Male',
                                      status: GulaBadgeStatus.info,
                                      showDot: false,
                                    ),
                                    const SizedBox(width: 8),
                                    GulaBadge(
                                      label: 'A+',
                                      status: GulaBadgeStatus.neutral,
                                      showDot: false,
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ],
                        ),
                        const Divider(height: 32),
                        _detailRow('National ID', '10000000000001'),
                        _detailRow('Date of Birth', '1985-05-15 (40 years)'),
                        _detailRow('Phone', '07701234567'),
                        _detailRow('Email', 'ahmed@example.com'),
                        _detailRow('Address', 'Baghdad, Karrada'),
                        _detailRow('Occupation', 'Engineer'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    children: [
                      GulaCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SectionHeader(title: 'Recent Orders'),
                            const Divider(height: 1),
                            _orderItem(
                              'ORD-2025-0891',
                              'CBC, LFT',
                              'Completed',
                            ),
                            _orderItem(
                              'ORD-2025-0850',
                              'Thyroid Panel',
                              'Pending',
                            ),
                            _orderItem(
                              'ORD-2025-0812',
                              'Lipid Profile',
                              'Validated',
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      GulaCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SectionHeader(title: 'Recent Results'),
                            const Divider(height: 1),
                            _resultItem('Hemoglobin', '14.2', 'g/dL', 'Normal'),
                            _resultItem('WBC', '8.5', 'K/uL', 'Normal'),
                            _resultItem('Glucose', '95', 'mg/dL', 'Normal'),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 13,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }

  Widget _orderItem(String orderNum, String tests, String status) {
    return ListTile(
      dense: true,
      title: Text('#$orderNum', style: const TextStyle(fontSize: 13)),
      subtitle: Text(tests, style: const TextStyle(fontSize: 12)),
      trailing: GulaBadge(
        label: status,
        status: status == 'Completed'
            ? GulaBadgeStatus.success
            : GulaBadgeStatus.pending,
      ),
    );
  }

  Widget _resultItem(String test, String value, String unit, String flag) {
    return ListTile(
      dense: true,
      title: Text(test, style: const TextStyle(fontSize: 13)),
      trailing: Text(
        '$value $unit',
        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
      ),
    );
  }
}
