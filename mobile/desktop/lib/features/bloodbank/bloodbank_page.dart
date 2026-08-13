import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';

class BloodBankPage extends StatefulWidget {
  const BloodBankPage({super.key});

  @override
  State<BloodBankPage> createState() => _BloodBankPageState();
}

class _BloodBankPageState extends State<BloodBankPage> {
  final _units = [
    {'group': 'A+', 'units': 25, 'status': 'available'},
    {'group': 'A-', 'units': 8, 'status': 'low'},
    {'group': 'B+', 'units': 30, 'status': 'available'},
    {'group': 'B-', 'units': 5, 'status': 'critical'},
    {'group': 'AB+', 'units': 12, 'status': 'available'},
    {'group': 'AB-', 'units': 3, 'status': 'critical'},
    {'group': 'O+', 'units': 45, 'status': 'available'},
    {'group': 'O-', 'units': 15, 'status': 'low'},
  ];

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(title: 'Blood Bank'),
          const SizedBox(height: 16),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 4,
              childAspectRatio: 1.5,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
            ),
            itemCount: _units.length,
            itemBuilder: (context, index) {
              final u = _units[index];
              Color bgColor;
              switch (u['status']) {
                case 'critical': bgColor = AppColors.error50;
                case 'low': bgColor = AppColors.warning50;
                default: bgColor = AppColors.success50;
              }
              Color borderColor;
              switch (u['status']) {
                case 'critical': borderColor = AppColors.error200;
                case 'low': borderColor = AppColors.warning200;
                default: borderColor = AppColors.success200;
              }
              return Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: bgColor,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: borderColor),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(u['group']?.toString() ?? '', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text('${u['units']} units', style: const TextStyle(fontSize: 14)),
                    const SizedBox(height: 4),
                    GulaBadge(
                      label: u['status'].toString(),
                      status: u['status'] == 'available' ? GulaBadgeStatus.success
                          : u['status'] == 'low' ? GulaBadgeStatus.warning
                          : GulaBadgeStatus.error,
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
