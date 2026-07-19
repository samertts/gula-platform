import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_table.dart';
import '../../widgets/core/gula_loading.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';
import 'admin_provider.dart';

class UserManagementPage extends ConsumerStatefulWidget {
  const UserManagementPage({super.key});

  @override
  ConsumerState<UserManagementPage> createState() => _UserManagementPageState();
}

class _UserManagementPageState extends ConsumerState<UserManagementPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(adminProvider).loadUsers();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(adminProvider);

    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(title: 'User Management', actionLabel: 'Add User', onAction: () {}),
          const SizedBox(height: 16),
          Expanded(child: _buildContent(state)),
        ],
      ),
    );
  }

  Widget _buildContent(AdminProvider state) {
    if (state.isLoadingUsers) return const GulaLoading(type: GulaLoadingType.shimmer);

    return GulaTable(
      columns: [
        GulaTableColumn(key: 'name', label: 'Name', flex: 2),
        GulaTableColumn(key: 'email', label: 'Email', flex: 2),
        GulaTableColumn(key: 'role', label: 'Role', flex: 1,
          cellBuilder: (v, row) => GulaBadge(label: v.toString(), status: v == 'labAdmin' ? GulaBadgeStatus.info : GulaBadgeStatus.neutral)),
        GulaTableColumn(key: 'status', label: 'Status', flex: 1,
          cellBuilder: (v, row) => GulaBadge(label: v.toString(), status: v == 'active' ? GulaBadgeStatus.success : GulaBadgeStatus.cancelled)),
        GulaTableColumn(key: 'actions', label: 'Actions', flex: 1,
          cellBuilder: (v, row) => Row(
            children: [
              GulaButton(label: 'Edit', variant: GulaButtonVariant.text, height: 32, onPressed: () {}),
              GulaButton(label: 'Suspend', variant: GulaButtonVariant.danger, height: 32, onPressed: () {}),
            ],
          ),
        ),
      ],
      rows: state.users,
    );
  }
}
