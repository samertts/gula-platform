import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_loading.dart';
import '../../widgets/data/notification_tile.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';
import '../../core/theme/app_colors.dart';
import 'notification_provider.dart';

class NotificationListPage extends ConsumerStatefulWidget {
  const NotificationListPage({super.key});

  @override
  ConsumerState<NotificationListPage> createState() => _NotificationListPageState();
}

class _NotificationListPageState extends ConsumerState<NotificationListPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(notificationListProvider).loadNotifications();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(notificationListProvider);

    return PageContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: 'Notifications',
            subtitle: '${state.unreadCount} unread',
            trailing: state.unreadCount > 0
                ? GulaButton(label: 'Mark All Read', variant: GulaButtonVariant.text, onPressed: () => ref.read(notificationListProvider).markAllAsRead())
                : null,
          ),
          const SizedBox(height: 16),
          Expanded(child: _buildList(state)),
        ],
      ),
    );
  }

  Widget _buildList(NotificationProvider state) {
    if (state.isLoading) return const GulaLoading(type: GulaLoadingType.shimmer);

    return ListView.separated(
      itemCount: state.notifications.length,
      separatorBuilder: (_, __) => const Divider(height: 1),
      itemBuilder: (context, index) {
        final n = state.notifications[index];
        return NotificationTile(
          id: n['id'],
          title: n['title'],
          body: n['body'],
          type: n['type'],
          severity: n['severity'],
          isRead: n['isRead'] == 1,
          createdAt: DateTime.parse(n['createdAt']),
          onTap: () => ref.read(notificationListProvider).markAsRead(n['id']),
        );
      },
    );
  }
}
