import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_search_bar.dart';
import '../../widgets/core/gula_table.dart';
import '../../widgets/core/gula_loading.dart';
import '../../widgets/core/gula_error_widget.dart';
import '../../widgets/core/gula_badge.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';
import 'patient_provider.dart';

class PatientListPage extends ConsumerStatefulWidget {
  const PatientListPage({super.key});

  @override
  ConsumerState<PatientListPage> createState() => _PatientListPageState();
}

class _PatientListPageState extends ConsumerState<PatientListPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(patientProvider).loadPatients();
    });
  }

  @override
  Widget build(BuildContext context) {
    final patientState = ref.watch(patientProvider);

    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Patients',
            subtitle: '${patientState.totalItems} total patients',
            actionLabel: 'Add Patient',
            onAction: () => context.push('/patients/new'),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              SizedBox(
                width: 300,
                child: GulaSearchBar(
                  hint: 'Search by name, ID, or phone...',
                  onChanged: (query) => ref.read(patientProvider).search(query),
                ),
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
          Expanded(child: _buildContent(patientState)),
        ],
      ),
    );
  }

  Widget _buildContent(PatientProvider state) {
    if (state.isLoading)
      return const GulaLoading(type: GulaLoadingType.shimmer);
    if (state.hasError)
      return GulaErrorWidget(
        message: state.error!,
        onRetry: () => state.loadPatients(),
      );

    final columns = [
      GulaTableColumn(
        key: 'fullName',
        label: 'Name',
        flex: 2,
        sortable: true,
        cellBuilder: (v, row) {
          final name = [
            row['firstName'],
            row['fatherName'],
            row['lastName'],
          ].where((n) => n != null).join(' ');
          return Row(
            children: [
              CircleAvatar(
                radius: 16,
                backgroundColor: row['gender'] == 'f'
                    ? AppColors.secondary50
                    : AppColors.primary50,
                child: Icon(
                  row['gender'] == 'f' ? Icons.female : Icons.male,
                  size: 16,
                  color: row['gender'] == 'f'
                      ? AppColors.secondary500
                      : AppColors.primary500,
                ),
              ),
              const SizedBox(width: 12),
              Text(name, style: const TextStyle(fontWeight: FontWeight.w500)),
            ],
          );
        },
      ),
      GulaTableColumn(key: 'nationalId', label: 'National ID', flex: 1),
      GulaTableColumn(key: 'phone', label: 'Phone', flex: 1),
      GulaTableColumn(
        key: 'gender',
        label: 'Gender',
        flex: 0,
        width: 80,
        cellBuilder: (v, row) => GulaBadge(
          label: v == 'm' ? 'Male' : 'Female',
          status: v == 'm' ? GulaBadgeStatus.info : GulaBadgeStatus.success,
          showDot: false,
        ),
      ),
      GulaTableColumn(key: 'bloodGroup', label: 'Blood', width: 60),
    ];

    return GulaTable(
      columns: columns,
      rows: state.patients,
      isSortable: true,
      isSelectable: true,
      showCheckboxes: true,
      page: state.page,
      totalPages: state.totalPages,
      totalItems: state.totalItems,
      onPageChanged: (p) => state.loadPatients(page: p),
      contextMenuBuilder: (row) => PopupMenuButton(
        itemBuilder: (context) => [
          const PopupMenuItem(value: 'view', child: Text('View Details')),
          const PopupMenuItem(value: 'edit', child: Text('Edit')),
          const PopupMenuItem(
            value: 'delete',
            child: Text('Delete', style: TextStyle(color: AppColors.error500)),
          ),
        ],
        onSelected: (value) {
          final id = row['id'];
          switch (value) {
            case 'view':
              context.push('/patients/$id');
            case 'edit':
              context.push('/patients/$id/edit');
            case 'delete':
              ref.read(patientProvider).deletePatient(id.toString());
          }
        },
      ),
    );
  }
}
