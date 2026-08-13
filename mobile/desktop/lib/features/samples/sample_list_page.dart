import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../widgets/core/gula_search_bar.dart';
import '../../widgets/core/gula_table.dart';
import '../../widgets/core/gula_loading.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';
import 'sample_provider.dart';

class SampleListPage extends ConsumerStatefulWidget {
  const SampleListPage({super.key});

  @override
  ConsumerState<SampleListPage> createState() => _SampleListPageState();
}

class _SampleListPageState extends ConsumerState<SampleListPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(sampleProvider).loadSamples();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(sampleProvider);

    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Samples',
            actionLabel: 'Collect Sample',
            onAction: () => context.push('/samples/collect'),
          ),
          const SizedBox(height: 16),
          SizedBox(width: 300, child: GulaSearchBar(hint: 'Search by barcode...')),
          const SizedBox(height: 16),
          Expanded(child: _buildContent(state)),
        ],
      ),
    );
  }

  Widget _buildContent(SampleProvider state) {
    if (state.isLoading) return const GulaLoading(type: GulaLoadingType.shimmer);

    return GulaTable(
      columns: [
        GulaTableColumn(key: 'barcode', label: 'Barcode', flex: 1, sortable: true,
          cellBuilder: (v, row) => Text(v.toString(), style: const TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.w600))),
        GulaTableColumn(key: 'sampleType', label: 'Type', flex: 1),
        GulaTableColumn(key: 'patientName', label: 'Patient', flex: 2),
        GulaTableColumn(key: 'status', label: 'Status', flex: 1,
          cellBuilder: (v, row) {
            final statusMap = {
              'collected': GulaBadgeStatus.info,
              'received': GulaBadgeStatus.pending,
              'processing': GulaBadgeStatus.warning,
              'analyzed': GulaBadgeStatus.success,
              'rejected': GulaBadgeStatus.error,
            };
            return GulaBadge(label: v.toString(), status: statusMap[v] ?? GulaBadgeStatus.neutral);
          },
        ),
        GulaTableColumn(key: 'collectedAt', label: 'Collected', flex: 1,
          cellBuilder: (v, row) => Text(DateTime.tryParse(v.toString())?.toLocal().toString().substring(0, 16) ?? '')),
      ],
      rows: state.samples,
      isSortable: true,
      page: state.page,
      totalPages: state.totalPages,
      onPageChanged: (p) => state.loadSamples(page: p),
    );
  }
}
