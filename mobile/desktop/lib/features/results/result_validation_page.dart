import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_table.dart';
import '../../widgets/data/critical_value_flag.dart';
import '../../widgets/layout/page_container.dart';
import '../../widgets/layout/section_header.dart';

class ResultValidationPage extends StatefulWidget {
  const ResultValidationPage({super.key});

  @override
  State<ResultValidationPage> createState() => _ResultValidationPageState();
}

class _ResultValidationPageState extends State<ResultValidationPage> {
  final _pendingItems = List.generate(8, (i) => {
    'id': '${i + 1}',
    'testName': ['Hemoglobin', 'WBC', 'Glucose', 'Creatinine'][i % 4],
    'result': ['14.2', '8.5', '95', '0.9', '16.1', '12.3', '110', '0.7'][i],
    'unit': ['g/dL', 'K/uL', 'mg/dL', 'mg/dL'][i % 4],
    'flag': ['normal', 'normal', 'normal', 'normal', 'h', 'normal', 'h', 'normal'][i],
    'patientName': ['Ahmed Ali', 'Sara Mohammed', 'Hussein Jassim', 'Noor Hasan'][i % 4],
  });

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Result Validation',
            subtitle: '${_pendingItems.length} results pending validation',
          ),
          const SizedBox(height: 16),
          Expanded(
            child: GulaTable(
              columns: [
                GulaTableColumn(key: 'testName', label: 'Test', flex: 2),
                GulaTableColumn(key: 'result', label: 'Result', flex: 1,
                  cellBuilder: (v, row) => Row(
                    children: [
                      Text(v.toString(), style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                      if (row['flag'] != 'normal') ...[
                        const SizedBox(width: 8),
                        CriticalValueFlag(flag: row['flag']?.toString() ?? ''),
                      ],
                    ],
                  ),
                ),
                GulaTableColumn(key: 'unit', label: 'Unit', flex: 1),
                GulaTableColumn(key: 'patientName', label: 'Patient', flex: 1),
                GulaTableColumn(key: 'actions', label: 'Actions', flex: 2,
                  cellBuilder: (v, row) => Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      GulaButton(label: 'Approve', height: 32, onPressed: () {
                        setState(() => _pendingItems.remove(row));
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Result approved'), backgroundColor: AppColors.success500),
                        );
                      }),
                      const SizedBox(width: 8),
                      GulaButton(label: 'Reject', variant: GulaButtonVariant.danger, height: 32, onPressed: () {}),
                    ],
                  ),
                ),
              ],
              rows: _pendingItems,
              onRefresh: () {},
            ),
          ),
        ],
      ),
    );
  }
}
