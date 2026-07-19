import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';

class SidebarItem {
  final String label;
  final String route;
  final IconData icon;
  final List<String>? roles;
  final List<SidebarItem>? children;

  SidebarItem({
    required this.label,
    required this.route,
    required this.icon,
    this.roles,
    this.children,
  });
}

class GulaSidebar extends StatelessWidget {
  final bool isCollapsed;
  final VoidCallback onToggle;
  final String userRole;
  final String userName;
  final String userEmail;

  const GulaSidebar({
    super.key,
    this.isCollapsed = false,
    required this.onToggle,
    required this.userRole,
    required this.userName,
    required this.userEmail,
  });

  static const List<SidebarItem> _items = [
    SidebarItem(label: 'Dashboard', route: '/dashboard', icon: Icons.dashboard_outlined),
    SidebarItem(label: 'Patients', route: '/patients', icon: Icons.people_outline),
    SidebarItem(label: 'Orders', route: '/orders', icon: Icons.assignment_outlined),
    SidebarItem(label: 'Samples', route: '/samples', icon: Icons.science_outlined),
    SidebarItem(label: 'Results', route: '/results', icon: Icons.description_outlined),
    SidebarItem(label: 'Reports', route: '/reports', icon: Icons.assessment_outlined),
    SidebarItem(label: 'Notifications', route: '/notifications', icon: Icons.notifications_outlined),
    SidebarItem(label: 'Inventory', route: '/inventory', icon: Icons.inventory_2_outlined),
    SidebarItem(label: 'Billing', route: '/billing', icon: Icons.payments_outlined),
    SidebarItem(label: 'Pharmacy', route: '/pharmacy', icon: Icons.medical_services_outlined),
    SidebarItem(label: 'Radiology', route: '/radiology', icon: Icons.radiology_outlined),
    SidebarItem(label: 'Blood Bank', route: '/bloodbank', icon: Icons.bloodtype_outlined),
    SidebarItem(label: 'Emergency', route: '/emergency', icon: Icons.local_hospital_outlined),
    SidebarItem(label: 'Settings', route: '/settings', icon: Icons.settings_outlined),
  ];

  @override
  Widget build(BuildContext context) {
    final width = isCollapsed
        ? AppDimensions.sidebarCollapsedWidth
        : AppDimensions.sidebarWidth;

    return AnimatedContainer(
      duration: AppDimensions.durationNormal,
      width: width,
      decoration: BoxDecoration(
        color: AppColors.neutral900,
        border: Border(
          right: BorderSide(color: AppColors.neutral800),
        ),
      ),
      child: Column(
        children: [
          _buildHeader(),
          const Divider(color: AppColors.neutral800, height: 1),
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              children: _items.map((item) => _buildMenuItem(context, item)).toList(),
            ),
          ),
          const Divider(color: AppColors.neutral800, height: 1),
          _buildUserInfo(),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      height: AppDimensions.appBarHeight,
      padding: const EdgeInsets.symmetric(horizontal: AppDimensions.space4),
      child: Row(
        children: [
          if (!isCollapsed) ...[
            Container(
              width: 32,
              height: 32,
              decoration: const BoxDecoration(
                color: AppColors.primary500,
                borderRadius: BorderRadius.all(Radius.circular(8)),
              ),
              child: const Icon(Icons.science, color: Colors.white, size: 18),
            ),
            const SizedBox(width: 12),
            const Expanded(
              child: Text(
                'GULA',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
          IconButton(
            icon: Icon(
              isCollapsed ? Icons.menu_open : Icons.menu,
              color: AppColors.neutral400,
              size: 20,
            ),
            onPressed: onToggle,
          ),
        ],
      ),
    );
  }

  Widget _buildMenuItem(BuildContext context, SidebarItem item) {
    final location = GoRouterState.of(context).matchedLocation;
    final isActive = location.startsWith(item.route);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
        color: isActive ? AppColors.primary700 : Colors.transparent,
      ),
      child: Tooltip(
        message: isCollapsed ? item.label : '',
        waitDuration: const Duration(milliseconds: 500),
        child: ListTile(
          dense: true,
          leading: Icon(
            item.icon,
            color: isActive ? Colors.white : AppColors.neutral400,
            size: 20,
          ),
          title: isCollapsed
              ? null
              : Text(
                  item.label,
                  style: TextStyle(
                    color: isActive ? Colors.white : AppColors.neutral300,
                    fontSize: 14,
                    fontWeight: isActive ? FontWeight.w600 : FontWeight.w400,
                  ),
                ),
          onTap: () {
            if (location != item.route) {
              context.go(item.route);
            }
          },
          contentPadding: EdgeInsets.symmetric(
            horizontal: isCollapsed ? 0 : 12,
            vertical: 0,
          ),
          horizontalTitleGap: 0,
          minLeadingWidth: isCollapsed ? 0 : 24,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
          ),
        ),
      ),
    );
  }

  Widget _buildUserInfo() {
    return Container(
      padding: const EdgeInsets.all(AppDimensions.space3),
      child: isCollapsed
          ? CircleAvatar(
              radius: 16,
              backgroundColor: AppColors.primary500,
              child: Text(
                userName.isNotEmpty ? userName[0].toUpperCase() : 'U',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            )
          : Row(
              children: [
                CircleAvatar(
                  radius: 18,
                  backgroundColor: AppColors.primary500,
                  child: Text(
                    userName.isNotEmpty ? userName[0].toUpperCase() : 'U',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        userName,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                      Text(
                        userRole,
                        style: const TextStyle(
                          color: AppColors.neutral400,
                          fontSize: 11,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}
