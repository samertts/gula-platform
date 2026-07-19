import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';

class GulaTab {
  final String label;
  final IconData? icon;
  final Widget content;
  final int? badgeCount;
  final bool enabled;

  GulaTab({
    required this.label,
    this.icon,
    required this.content,
    this.badgeCount,
    this.enabled = true,
  });
}

class GulaTabs extends StatefulWidget {
  final List<GulaTab> tabs;
  final int initialIndex;
  final ValueChanged<int>? onTabChanged;
  final bool isScrollable;

  const GulaTabs({
    super.key,
    required this.tabs,
    this.initialIndex = 0,
    this.onTabChanged,
    this.isScrollable = false,
  });

  @override
  State<GulaTabs> createState() => _GulaTabsState();
}

class _GulaTabsState extends State<GulaTabs> with TickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(
      length: widget.tabs.length,
      vsync: this,
      initialIndex: widget.initialIndex,
    );
    _tabController.addListener(_onTabChanged);
  }

  void _onTabChanged() {
    if (!_tabController.indexIsChanging) {
      widget.onTabChanged?.call(_tabController.index);
    }
  }

  @override
  void dispose() {
    _tabController.removeListener(_onTabChanged);
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TabBar(
          controller: _tabController,
          isScrollable: widget.isScrollable,
          tabAlignment: widget.isScrollable ? TabAlignment.start : null,
          indicatorColor: AppColors.primary500,
          indicatorWeight: 3,
          labelColor: AppColors.primary700,
          unselectedLabelColor: AppColors.textSecondary,
          labelStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
          unselectedLabelStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w400),
          tabs: widget.tabs.map((tab) {
            return Tab(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (tab.icon != null) ...[
                    Icon(tab.icon, size: 18),
                    const SizedBox(width: 6),
                  ],
                  Text(tab.label),
                  if (tab.badgeCount != null) ...[
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                      decoration: BoxDecoration(
                        color: AppColors.error500,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        '${tab.badgeCount}',
                        style: const TextStyle(color: Colors.white, fontSize: 11),
                      ),
                    ),
                  ],
                ],
              ),
            );
          }).toList(),
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: widget.tabs.map((tab) => tab.content).toList(),
          ),
        ),
      ],
    );
  }
}
