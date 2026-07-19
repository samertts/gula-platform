import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/core/gula_search_bar.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';

class RadiologyPage extends StatefulWidget {
  const RadiologyPage({super.key});

  @override
  State<RadiologyPage> createState() => _RadiologyPageState();
}

class _RadiologyPageState extends State<RadiologyPage> {
  final _studies = List.generate(8, (i) => {
    'id': 'RAD-${2025000 + i}',
    'patient': ['Ali Hassan', 'Mariam Khalid', 'Omar Jassim', 'Noor Abbas'][i % 4],
    'study': ['Chest X-Ray', 'Abdominal Ultrasound', 'CT Head', 'MRI Lumbar Spine', 'Mammogram', 'Bone Density', 'Echocardiogram', 'Carotid Doppler'][i],
    'status': ['pending', 'completed', 'reviewed', 'pending', 'completed', 'reviewed', 'pending', 'completed'][i],
    'date': DateTime.now().subtract(Duration(days: i)).toIso8601String(),
  });

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(title: 'Radiology'),
          const SizedBox(height: 16),
          SizedBox(width: 300, child: GulaSearchBar(hint: 'Search radiology studies...')),
          const SizedBox(height: 16),
          Expanded(
            child: ListView.builder(
              itemCount: _studies.length,
              itemBuilder: (context, index) {
                final s = _studies[index];
                return GulaCard(
                  child: ListTile(
                    leading: Container(
                      width: 40, height: 40,
                      decoration: BoxDecoration(color: AppColors.info50, borderRadius: BorderRadius.circular(8)),
                      child: const Icon(Icons.radiology, color: AppColors.info500),
                    ),
                    title: Text(s['study'], style: const TextStyle(fontWeight: FontWeight.w500)),
                    subtitle: Text('${s['patient']} • ${s['id']}'),
                    trailing: _buildStatusBadge(s['status']),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
    switch (status) {
      case 'pending': return const GulaBadge(label: 'Pending', status: GulaBadgeStatus.pending);
      case 'completed': return const GulaBadge(label: 'Completed', status: GulaBadgeStatus.success);
      case 'reviewed': return const GulaBadge(label: 'Reviewed', status: GulaBadgeStatus.info);
      default: return GulaBadge(label: status, status: GulaBadgeStatus.neutral);
    }
  }
}
