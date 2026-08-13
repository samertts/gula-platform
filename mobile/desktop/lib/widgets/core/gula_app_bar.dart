import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import 'gula_sync_indicator.dart';
import 'gula_search_bar.dart';

class GulaAppBar extends StatelessWidget implements PreferredSizeWidget {
  final VoidCallback? onMenuTap;
  final GulaSyncIndicator? syncIndicator;
  final String? userName;
  final VoidCallback? onLogout;

  const GulaAppBar({
    super.key,
    this.onMenuTap,
    this.syncIndicator,
    this.userName,
    this.onLogout,
  });

  @override
  Size get preferredSize => const Size.fromHeight(AppDimensions.appBarHeight);

  @override
  Widget build(BuildContext context) {
    return Container(
      height: AppDimensions.appBarHeight,
      decoration: BoxDecoration(
        color:
            Theme.of(context).appBarTheme.backgroundColor ??
            AppColors.surfaceLight,
        border: Border(bottom: BorderSide(color: AppColors.divider)),
      ),
      child: Row(
        children: [
          const SizedBox(width: 8),
          if (onMenuTap != null)
            IconButton(
              icon: const Icon(Icons.menu, size: 20),
              onPressed: onMenuTap,
              color: AppColors.textSecondary,
            ),
          const SizedBox(width: 8),
          SizedBox(
            width: 300,
            child: GulaSearchBar(
              hint: 'Search patients, orders, samples...',
              onSubmitted: (query) {
                if (query.isNotEmpty) {
                  context.push('/search', extra: query);
                }
              },
            ),
          ),
          const Spacer(),
          if (syncIndicator != null) ...[
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: syncIndicator,
            ),
          ],
          const SizedBox(width: 8),
          _buildNotificationIcon(context),
          const SizedBox(width: 4),
          _buildUserMenu(context),
          const SizedBox(width: 8),
        ],
      ),
    );
  }

  Widget _buildNotificationIcon(BuildContext context) {
    return IconButton(
      icon: Stack(
        clipBehavior: Clip.none,
        children: [
          const Icon(
            Icons.notifications_outlined,
            size: 20,
            color: AppColors.textSecondary,
          ),
          Positioned(
            right: -4,
            top: -4,
            child: Container(
              width: 8,
              height: 8,
              decoration: const BoxDecoration(
                color: AppColors.error500,
                shape: BoxShape.circle,
              ),
            ),
          ),
        ],
      ),
      onPressed: () => context.push('/notifications'),
    );
  }

  Widget _buildUserMenu(BuildContext context) {
    return PopupMenuButton<String>(
      offset: const Offset(0, 48),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppDimensions.radiusMd),
      ),
      onSelected: (value) {
        switch (value) {
          case 'settings':
            context.push('/settings');
          case 'logout':
            onLogout?.call();
        }
      },
      itemBuilder: (context) => [
        PopupMenuItem(
          value: 'profile',
          enabled: false,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                userName ?? 'User',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
              const Text(
                'View profile',
                style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
            ],
          ),
        ),
        const PopupMenuDivider(),
        const PopupMenuItem(
          value: 'settings',
          child: ListTile(
            leading: Icon(Icons.settings_outlined, size: 20),
            title: Text('Settings'),
            contentPadding: EdgeInsets.zero,
            dense: true,
          ),
        ),
        const PopupMenuDivider(),
        const PopupMenuItem(
          value: 'logout',
          child: ListTile(
            leading: Icon(Icons.logout, size: 20, color: AppColors.error500),
            title: Text('Logout', style: TextStyle(color: AppColors.error500)),
            contentPadding: EdgeInsets.zero,
            dense: true,
          ),
        ),
      ],
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircleAvatar(
              radius: 16,
              backgroundColor: AppColors.primary100,
              child: Text(
                (userName?.isNotEmpty == true ? userName![0] : 'U')
                    .toUpperCase(),
                style: const TextStyle(
                  color: AppColors.primary700,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(width: 8),
            const Icon(
              Icons.arrow_drop_down,
              size: 18,
              color: AppColors.textSecondary,
            ),
          ],
        ),
      ),
    );
  }
}
