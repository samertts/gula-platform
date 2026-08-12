import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../widgets/charts/kpi_card.dart';
import '../../widgets/charts/bar_chart_widget.dart';
import '../../widgets/charts/pie_chart_widget.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_loading.dart';
import '../../widgets/core/gula_error_widget.dart';
import '../../widgets/layout/section_header.dart';
import 'dashboard_provider.dart';

class DashboardPage extends ConsumerStatefulWidget {
  const DashboardPage({super.key});

  @override
  ConsumerState<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends ConsumerState<DashboardPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(dashboardProvider).loadDashboard();
    });
  }

  @override
  Widget build(BuildContext context) {
    final dashboardState = ref.watch(dashboardProvider).state;

    if (dashboardState.isLoading) {
      return const GulaLoading(type: GulaLoadingType.shimmer);
    }

    if (dashboardState.hasError) {
      return GulaErrorWidget(
        title: 'Dashboard Error',
        message: dashboardState.error ?? 'Failed to load dashboard',
        onRetry: () => ref.read(dashboardProvider).loadDashboard(),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppDimensions.space4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Dashboard',
            subtitle: 'Overview of laboratory operations',
          ),
          const SizedBox(height: 8),
          _buildKpiGrid(dashboardState),
          const SizedBox(height: 24),
          _buildMainContent(dashboardState),
        ],
      ),
    );
  }

  Widget _buildKpiGrid(DashboardState state) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final crossAxisCount = constraints.maxWidth > 1200 ? 4 : (constraints.maxWidth > 800 ? 3 : 2);
        return GridView.count(
          crossAxisCount: crossAxisCount,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          childAspectRatio: 1.6,
          mainAxisSpacing: 8,
          crossAxisSpacing: 8,
          children: [
            KpiCard(
              title: 'Total Patients',
              value: '${state.totalPatients}',
              icon: Icons.people_outline,
              color: AppColors.primary500,
              trendValue: 12.5,
            ),
            KpiCard(
              title: 'Total Orders',
              value: '${state.totalOrders}',
              icon: Icons.assignment_outlined,
              color: AppColors.info500,
              trendValue: 8.3,
            ),
            KpiCard(
              title: 'Critical Results',
              value: '${state.criticalResults}',
              icon: Icons.warning_amber_outlined,
              color: AppColors.error500,
              trendValue: -2.1,
              trendColor: AppColors.success500,
            ),
            KpiCard(
              title: 'Pending Results',
              value: '${state.pendingResults}',
              icon: Icons.pending_outlined,
              color: AppColors.warning500,
              trendValue: 5.0,
            ),
          ],
        );
      },
    );
  }

  Widget _buildMainContent(DashboardState state) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth > 1000;
        if (isWide) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(flex: 2, child: _buildLeftColumn(state)),
              const SizedBox(width: 16),
              Expanded(flex: 1, child: _buildRightColumn(state)),
            ],
          );
        }
        return Column(
          children: [
            _buildLeftColumn(state),
            const SizedBox(height: 16),
            _buildRightColumn(state),
          ],
        );
      },
    );
  }

  Widget _buildLeftColumn(DashboardState state) {
    return Column(
      children: [
        GulaCard(
          padding: const EdgeInsets.all(AppDimensions.space4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SectionHeader(
                title: 'Orders This Week',
                actionLabel: 'View All',
                actionIcon: Icons.arrow_forward,
                onAction: () => context.push('/orders'),
              ),
              const SizedBox(height: 16),
              SizedBox(
                height: 250,
                child: BarChartWidget(
                  data: state.ordersByDay.map((d) => BarChartData(
                    label: d['day'] as String,
                    value: (d['orders'] as num).toDouble(),
                  )).toList(),
                  showLegend: false,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        GulaCard(
          padding: const EdgeInsets.all(AppDimensions.space4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SectionHeader(title: 'Recent Activity'),
              const SizedBox(height: 12),
              ...state.recentActivities.take(5).map((activity) => _buildActivityItem(activity)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildRightColumn(DashboardState state) {
    return Column(
      children: [
        GulaCard(
          padding: const EdgeInsets.all(AppDimensions.space4),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SectionHeader(title: 'Results Status'),
              const SizedBox(height: 16),
              SizedBox(
                height: 200,
                child: PieChartWidget(
                  data: [
                    PieChartDataItem(label: 'Completed', value: 45, color: AppColors.success500),
                    PieChartDataItem(label: 'Pending', value: 15, color: AppColors.warning500),
                    PieChartDataItem(label: 'Validated', value: 30, color: AppColors.info500),
                    PieChartDataItem(label: 'Critical', value: 3, color: AppColors.error500),
                  ],
                  showLegend: true,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: KpiCard(
                title: 'Today Orders',
                value: '${state.todayOrders}',
                icon: Icons.today_outlined,
                color: AppColors.primary500,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: KpiCard(
                title: 'Today Samples',
                value: '${state.todaySamples}',
                icon: Icons.science_outlined,
                color: AppColors.accent500,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildActivityItem(RecentActivity activity) {
    IconData icon;
    Color color;
    switch (activity.type) {
      case 'result':
        icon = Icons.description;
        color = AppColors.info500;
      case 'order':
        icon = Icons.assignment;
        color = AppColors.primary500;
      case 'sample':
        icon = Icons.science;
        color = AppColors.accent500;
      case 'patient':
        icon = Icons.person_add;
        color = AppColors.success500;
      default:
        icon = Icons.notifications;
        color = AppColors.neutral500;
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 16),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(activity.title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                if (activity.subtitle != null)
                  Text(activity.subtitle!, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
              ],
            ),
          ),
          Text(
            _formatTime(activity.timestamp),
            style: const TextStyle(fontSize: 11, color: AppColors.neutral400),
          ),
        ],
      ),
    );
  }

  String _formatTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 60) return '${diff.inMinutes}m';
    if (diff.inHours < 24) return '${diff.inHours}h';
    return '${diff.inDays}d';
  }
}
