import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';

class PharmacyPage extends StatefulWidget {
  const PharmacyPage({super.key});

  @override
  State<PharmacyPage> createState() => _PharmacyPageState();
}

class _PharmacyPageState extends State<PharmacyPage> {
  final _medications = List.generate(12, (i) => {
    'name': ['Amoxicillin', 'Metformin', 'Omeprazole', 'Atorvastatin', 'Lisinopril', 'Metoprolol', 'Losartan', 'Levothyroxine', 'Albuterol', 'Pantoprazole', 'Gabapentin', 'Sertraline'][i],
    'dosage': ['500mg', '850mg', '20mg', '10mg', '10mg', '50mg', '50mg', '100mcg', '90mcg', '40mg', '300mg', '50mg'][i],
    'quantity': [200, 150, 100, 80, 120, 90, 110, 60, 50, 70, 40, 85][i],
    'expiry': ['2026-03', '2025-12', '2025-09', '2026-06', '2025-11', '2026-01', '2025-10', '2025-08', '2025-07', '2026-04', '2025-06', '2026-02'][i],
  });

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(title: 'Pharmacy'),
          const SizedBox(height: 16),
          Expanded(
            child: GridView.builder(
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                childAspectRatio: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
              ),
              itemCount: _medications.length,
              itemBuilder: (context, index) {
                final med = _medications[index];
                return GulaCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(med['name'], style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                      const SizedBox(height: 4),
                      Text('${med['dosage']} • Qty: ${med['quantity']}',
                          style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                      const SizedBox(height: 8),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          GulaBadge(label: 'Exp: ${med['expiry']}', status: GulaBadgeStatus.neutral, showDot: false),
                          if (med['quantity'] < 60)
                            const GulaBadge(label: 'Low', status: GulaBadgeStatus.error),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
