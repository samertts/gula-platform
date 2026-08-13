import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../widgets/core/gula_table.dart';
import '../../widgets/core/gula_loading.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';
import 'billing_provider.dart';

class BillingPage extends ConsumerStatefulWidget {
  const BillingPage({super.key});

  @override
  ConsumerState<BillingPage> createState() => _BillingPageState();
}

class _BillingPageState extends ConsumerState<BillingPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(billingProvider).loadInvoices();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(billingProvider);

    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(title: 'Billing'),
          const SizedBox(height: 16),
          Expanded(child: _buildContent(state)),
        ],
      ),
    );
  }

  Widget _buildContent(BillingProvider state) {
    if (state.isLoading) return const GulaLoading(type: GulaLoadingType.shimmer);

    return GulaTable(
      columns: [
        GulaTableColumn(key: 'invoiceNumber', label: 'Invoice #', flex: 1),
        GulaTableColumn(key: 'patientName', label: 'Patient', flex: 2),
        GulaTableColumn(key: 'amount', label: 'Amount', flex: 1,
          cellBuilder: (v, row) => Text('\$$v', style: const TextStyle(fontWeight: FontWeight.w600))),
        GulaTableColumn(key: 'status', label: 'Status', flex: 1,
          cellBuilder: (v, row) {
            final statusMap = {
              'paid': GulaBadgeStatus.success,
              'pending': GulaBadgeStatus.pending,
              'overdue': GulaBadgeStatus.error,
              'cancelled': GulaBadgeStatus.cancelled,
            };
            return GulaBadge(label: v.toString(), status: statusMap[v] ?? GulaBadgeStatus.neutral);
          },
        ),
        GulaTableColumn(key: 'date', label: 'Date', flex: 1,
          cellBuilder: (v, row) => Text(DateTime.tryParse(v.toString())?.toLocal().toString().substring(0, 10) ?? '')),
      ],
      rows: state.invoices,
      isSortable: true,
    );
  }
}
