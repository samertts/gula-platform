import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_search_bar.dart';
import '../../widgets/core/gula_table.dart';
import '../../widgets/core/gula_loading.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';
import 'order_provider.dart';

class OrderListPage extends ConsumerStatefulWidget {
  const OrderListPage({super.key});

  @override
  ConsumerState<OrderListPage> createState() => _OrderListPageState();
}

class _OrderListPageState extends ConsumerState<OrderListPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(orderProvider).loadOrders();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(orderProvider);

    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Orders',
            actionLabel: 'New Order',
            onAction: () => context.push('/orders/new'),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              SizedBox(
                width: 300,
                child: GulaSearchBar(hint: 'Search orders...'),
              ),
              const Spacer(),
              GulaButton(
                label: 'Filter',
                variant: GulaButtonVariant.outline,
                icon: Icons.filter_list,
                onPressed: () {},
              ),
            ],
          ),
          const SizedBox(height: 16),
          Expanded(child: _buildContent(state)),
        ],
      ),
    );
  }

  Widget _buildContent(OrderProvider state) {
    if (state.isLoading)
      return const GulaLoading(type: GulaLoadingType.shimmer);
    if (state.hasError) return Center(child: Text('Error: ${state.error}'));

    return GulaTable(
      columns: [
        GulaTableColumn(
          key: 'orderNumber',
          label: 'Order #',
          flex: 1,
          sortable: true,
        ),
        GulaTableColumn(
          key: 'patientName',
          label: 'Patient',
          flex: 2,
          sortable: true,
        ),
        GulaTableColumn(key: 'testTypes', label: 'Tests', flex: 2),
        GulaTableColumn(
          key: 'status',
          label: 'Status',
          flex: 1,
          cellBuilder: (v, row) {
            final statusMap = {
              'pending': GulaBadgeStatus.pending,
              'completed': GulaBadgeStatus.success,
              'validated': GulaBadgeStatus.success,
              'cancelled': GulaBadgeStatus.cancelled,
            };
            return GulaBadge(
              label: v.toString(),
              status: statusMap[v] ?? GulaBadgeStatus.neutral,
            );
          },
        ),
        GulaTableColumn(key: 'doctorName', label: 'Doctor', flex: 1),
        GulaTableColumn(
          key: 'createdAt',
          label: 'Date',
          flex: 1,
          cellBuilder: (v, row) => Text(
            (DateTime.tryParse(
                  v.toString(),
                )?.toLocal().toString().substring(0, 10) ??
                ''),
          ),
        ),
      ],
      rows: state.orders,
      isSortable: true,
      page: state.page,
      totalPages: state.totalPages,
      onPageChanged: (p) => state.loadOrders(page: p),
      contextMenuBuilder: (row) => PopupMenuButton(
        itemBuilder: (context) => [
          const PopupMenuItem(value: 'view', child: Text('View Details')),
          const PopupMenuItem(
            value: 'cancel',
            child: Text('Cancel', style: TextStyle(color: AppColors.error500)),
          ),
        ],
        onSelected: (v) {
          if (v == 'view') context.push('/orders/${row['id']}');
        },
      ),
    );
  }
}
