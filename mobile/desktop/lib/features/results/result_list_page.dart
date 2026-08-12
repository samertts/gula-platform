import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_search_bar.dart';
import '../../widgets/core/gula_table.dart';
import '../../widgets/core/gula_loading.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/data/critical_value_flag.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';
import 'result_provider.dart';

class ResultListPage extends ConsumerStatefulWidget {
  const ResultListPage({super.key});

  @override
  ConsumerState<ResultListPage> createState() => _ResultListPageState();
}

class _ResultListPageState extends ConsumerState<ResultListPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(resultProvider).loadResults();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(resultProvider);

    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Results',
            actionLabel: 'Enter Result',
            onAction: () => context.push('/results/entry'),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              SizedBox(width: 300, child: GulaSearchBar(hint: 'Search results...')),
              const Spacer(),
              GulaButton(label: 'Validation Queue', variant: GulaButtonVariant.outline, icon: Icons.verified, onPressed: () => context.push('/results/validation')),
            ],
          ),
          const SizedBox(height: 16),
          Expanded(child: _buildContent(state)),
        ],
      ),
    );
  }

  Widget _buildContent(ResultProvider state) {
    if (state.isLoading) return const GulaLoading(type: GulaLoadingType.shimmer);

    return GulaTable(
      columns: [
        GulaTableColumn(key: 'testName', label: 'Test', flex: 2, sortable: true),
        GulaTableColumn(key: 'result', label: 'Result', flex: 1,
          cellBuilder: (v, row) => Row(
            children: [
              Text(v.toString(), style: const TextStyle(fontWeight: FontWeight.w600)),
              if (row['flag'] != null && row['flag'] != 'normal') ...[
                const SizedBox(width: 8),
                CriticalValueFlag(flag: row['flag']),
              ],
            ],
          ),
        ),
        GulaTableColumn(key: 'unit', label: 'Unit', flex: 1),
        GulaTableColumn(key: 'referenceRange', label: 'Ref Range', flex: 1),
        GulaTableColumn(key: 'patientName', label: 'Patient', flex: 1),
        GulaTableColumn(key: 'status', label: 'Status', flex: 1,
          cellBuilder: (v, row) => GulaBadge(
            label: v.toString(),
            status: v == 'verified' ? GulaBadgeStatus.success : v == 'completed' ? GulaBadgeStatus.info : GulaBadgeStatus.pending,
          ),
        ),
      ],
      rows: state.results,
      isSortable: true,
      page: state.page,
      totalPages: state.totalPages,
      onPageChanged: (p) => state.loadResults(page: p),
    );
  }
}
