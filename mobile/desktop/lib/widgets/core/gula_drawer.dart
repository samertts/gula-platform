import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';

class GulaDrawer extends StatelessWidget {
  final String userName;
  final String userEmail;
  final String userRole;

  const GulaDrawer({
    super.key,
    required this.userName,
    required this.userEmail,
    required this.userRole,
  });

  static const List<Map<String, dynamic>> _menuItems = [
    {
      'label': 'Dashboard',
      'route': '/dashboard',
      'icon': Icons.dashboard_outlined,
    },
    {'label': 'Patients', 'route': '/patients', 'icon': Icons.people_outline},
    {'label': 'Orders', 'route': '/orders', 'icon': Icons.assignment_outlined},
    {'label': 'Samples', 'route': '/samples', 'icon': Icons.science_outlined},
    {
      'label': 'Results',
      'route': '/results',
      'icon': Icons.description_outlined,
    },
    {
      'label': 'Reports',
      'route': '/reports',
      'icon': Icons.assessment_outlined,
    },
    {
      'label': 'Notifications',
      'route': '/notifications',
      'icon': Icons.notifications_outlined,
    },
    {
      'label': 'Settings',
      'route': '/settings',
      'icon': Icons.settings_outlined,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: Column(
        children: [
          _buildHeader(),
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              children: _menuItems
                  .map((item) => _buildMenuItem(context, item))
                  .toList(),
            ),
          ),
          const Divider(height: 1),
          _buildFooter(context),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return DrawerHeader(
      decoration: const BoxDecoration(color: AppColors.primary700),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          const CircleAvatar(
            radius: 28,
            backgroundColor: Colors.white24,
            child: Icon(Icons.person, color: Colors.white, size: 32),
          ),
          const SizedBox(height: 12),
          Text(
            userName,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
          ),
          Text(
            userEmail,
            style: const TextStyle(color: Colors.white70, fontSize: 13),
          ),
        ],
      ),
    );
  }

  Widget _buildMenuItem(BuildContext context, Map<String, dynamic> item) {
    final location = GoRouterState.of(context).matchedLocation;
    final isActive = location.startsWith(item['route'] as String);

    return ListTile(
      leading: Icon(
        item['icon'] as IconData,
        color: isActive ? AppColors.primary500 : AppColors.textSecondary,
      ),
      title: Text(
        item['label'] as String,
        style: TextStyle(
          color: isActive ? AppColors.primary700 : AppColors.textPrimary,
          fontWeight: isActive ? FontWeight.w600 : FontWeight.w400,
        ),
      ),
      selected: isActive,
      selectedTileColor: AppColors.primary50,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
      ),
      onTap: () {
        Navigator.of(context).pop();
        context.go(item['route'] as String);
      },
    );
  }

  Widget _buildFooter(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          const Icon(Icons.logout, size: 20, color: AppColors.error500),
          const SizedBox(width: 12),
          GestureDetector(
            onTap: () {
              Navigator.of(context).pop();
            },
            child: const Text(
              'Logout',
              style: TextStyle(color: AppColors.error500, fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }
}
