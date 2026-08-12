import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_search_bar.dart';
import '../../widgets/core/gula_table.dart';
import '../../widgets/core/gula_loading.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';
import 'inventory_provider.dart';

class InventoryPage extends ConsumerStatefulWidget {
  const InventoryPage({super.key});

  @override
  ConsumerState<InventoryPage> createState() => _InventoryPageState();
}

class _InventoryPageState extends ConsumerState<InventoryPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(inventoryProvider).loadItems();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(inventoryProvider);

    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(title: 'Inventory'),
          const SizedBox(height: 16),
          SizedBox(width: 300, child: GulaSearchBar(hint: 'Search inventory...')),
          const SizedBox(height: 16),
          Expanded(child: _buildContent(state)),
        ],
      ),
    );
  }

  Widget _buildContent(InventoryProvider state) {
    if (state.isLoading) return const GulaLoading(type: GulaLoadingType.shimmer);

    return GulaTable(
      columns: [
        GulaTableColumn(key: 'name', label: 'Item', flex: 2, sortable: true),
        GulaTableColumn(key: 'category', label: 'Category', flex: 1),
        GulaTableColumn(key: 'quantity', label: 'Quantity', flex: 1,
          cellBuilder: (v, row) {
            final qty = v as int;
            final minQty = row['minQuantity'] as int;
            final isLow = qty <= minQty;
            return Row(
              children: [
                Text(qty.toString(), style: TextStyle(fontWeight: FontWeight.w600, color: isLow ? AppColors.error500 : AppColors.textPrimary)),
                if (isLow) ...[
                  const SizedBox(width: 8),
                  const GulaBadge(label: 'Low Stock', status: GulaBadgeStatus.error),
                ],
              ],
            );
          },
        ),
        GulaTableColumn(key: 'unit', label: 'Unit', flex: 1),
        GulaTableColumn(key: 'expiryDate', label: 'Expiry', flex: 1,
          cellBuilder: (v, row) {
            final date = DateTime.tryParse(v.toString());
            if (date == null) return const SizedBox.shrink();
            final isExpiring = date.difference(DateTime.now()).inDays < 30;
            return Text(
              date.toLocal().toString().substring(0, 10),
              style: TextStyle(color: isExpiring ? AppColors.error500 : AppColors.textPrimary),
            );
          },
        ),
      ],
      rows: state.items,
      isSortable: true,
    );
  }
}
