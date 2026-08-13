import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_table.dart';
import '../../widgets/core/gula_loading.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';
import 'admin_provider.dart';

class AuditLogPage extends ConsumerStatefulWidget {
  const AuditLogPage({super.key});

  @override
  ConsumerState<AuditLogPage> createState() => _AuditLogPageState();
}

class _AuditLogPageState extends ConsumerState<AuditLogPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(adminProvider).loadAuditLogs();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(adminProvider);

    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(
            title: 'Audit Log',
            subtitle: 'Immutable record of all system actions',
          ),
          const SizedBox(height: 16),
          Expanded(child: _buildContent(state)),
        ],
      ),
    );
  }

  Widget _buildContent(AdminProvider state) {
    if (state.isLoadingAudit)
      return const GulaLoading(type: GulaLoadingType.shimmer);

    return GulaTable(
      columns: [
        GulaTableColumn(
          key: 'action',
          label: 'Action',
          flex: 1,
          cellBuilder: (v, row) {
            Color c;
            switch (v.toString()) {
              case 'CREATE':
                c = AppColors.success500;
              case 'UPDATE':
                c = AppColors.info500;
              case 'DELETE':
                c = AppColors.error500;
              case 'VIEW':
                c = AppColors.neutral500;
              case 'LOGIN':
                c = AppColors.primary500;
              default:
                c = AppColors.neutral500;
            }
            return Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: c.withOpacity(0.1),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                v.toString(),
                style: TextStyle(
                  color: c,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            );
          },
        ),
        GulaTableColumn(key: 'entity', label: 'Entity', flex: 1),
        GulaTableColumn(key: 'entityId', label: 'Entity ID', flex: 1),
        GulaTableColumn(key: 'user', label: 'User', flex: 1),
        GulaTableColumn(
          key: 'timestamp',
          label: 'Timestamp',
          flex: 1,
          cellBuilder: (v, row) => Text(
            DateTime.tryParse(
                  v.toString(),
                )?.toLocal().toString().substring(0, 19) ??
                '',
          ),
        ),
        GulaTableColumn(key: 'details', label: 'Details', flex: 2),
      ],
      rows: state.auditLogs,
    );
  }
}
