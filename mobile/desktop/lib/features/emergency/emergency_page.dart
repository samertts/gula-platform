import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';

class EmergencyPage extends StatefulWidget {
  const EmergencyPage({super.key});

  @override
  State<EmergencyPage> createState() => _EmergencyPageState();
}

class _EmergencyPageState extends State<EmergencyPage> {
  final _patients = List.generate(
    5,
    (i) => {
      'name': [
        'Ahmed Ali',
        'Emergency Case 2',
        'Trauma Patient',
        'Cardiac Arrest',
        'Accident Victim',
      ][i],
      'priority': ['critical', 'high', 'high', 'critical', 'medium'][i],
      'condition': [
        'Chest Pain',
        'Severe Bleeding',
        'Head Trauma',
        'Cardiac Arrest',
        'Fracture',
      ][i],
      'time': DateTime.now().subtract(Duration(minutes: i * 10)),
      'vitals': {'bp': '140/90', 'hr': '110', 'o2': '94%', 'temp': '37.2°C'},
    },
  );

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: SectionHeader(
                  title: 'Emergency Department',
                  subtitle: '${_patients.length} active patients',
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: AppColors.error50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.error200),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.warning, color: AppColors.error500, size: 20),
                    SizedBox(width: 8),
                    Text(
                      '2 Critical',
                      style: TextStyle(
                        color: AppColors.error500,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Expanded(
            child: ListView.builder(
              itemCount: _patients.length,
              itemBuilder: (context, index) {
                final p = _patients[index];
                final vitals = p['vitals'] as Map<String, String>;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: GulaCard(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Container(
                            width: 8,
                            height: 80,
                            decoration: BoxDecoration(
                              color: p['priority'] == 'critical'
                                  ? AppColors.critical
                                  : p['priority'] == 'high'
                                  ? AppColors.urgent
                                  : AppColors.warning500,
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Text(
                                      p['name']?.toString() ?? '',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                        fontSize: 16,
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    GulaBadge(
                                      label: p['priority']
                                          .toString()
                                          .toUpperCase(),
                                      status: p['priority'] == 'critical'
                                          ? GulaBadgeStatus.critical
                                          : p['priority'] == 'high'
                                          ? GulaBadgeStatus.urgent
                                          : GulaBadgeStatus.warning,
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  p['condition']?.toString() ?? '',
                                  style: const TextStyle(
                                    fontSize: 14,
                                    color: AppColors.textSecondary,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Row(
                                  children: [
                                    _vitalChip('BP', vitals['bp'] ?? ''),
                                    const SizedBox(width: 8),
                                    _vitalChip('HR', vitals['hr'] ?? ''),
                                    const SizedBox(width: 8),
                                    _vitalChip('O2', vitals['o2'] ?? ''),
                                    const SizedBox(width: 8),
                                    _vitalChip('Temp', vitals['temp'] ?? ''),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              GulaButton(
                                label: 'Assess',
                                height: 36,
                                onPressed: () {},
                              ),
                              const SizedBox(height: 8),
                              GulaButton(
                                label: 'Orders',
                                variant: GulaButtonVariant.outline,
                                height: 36,
                                onPressed: () {},
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _vitalChip(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.neutral50,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        '$label: $value',
        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
      ),
    );
  }
}
