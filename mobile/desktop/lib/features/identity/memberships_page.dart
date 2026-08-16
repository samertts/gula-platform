import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers/app_providers.dart';

class MembershipsPage extends ConsumerWidget {
  const MembershipsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProviderProvider);
    final memberships = auth.memberships;
    return Scaffold(
      appBar: AppBar(title: const Text('Memberships & Contexts')),
      body: memberships.isEmpty
          ? const Center(
              child: Text(
                'No memberships are currently reflected by the server.',
              ),
            )
          : ListView.separated(
              padding: const EdgeInsets.all(20),
              itemCount: memberships.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final item = memberships[index];
                final status = item['status']?.toString() ?? 'unknown';
                final scope =
                    item['scope']?.toString() ??
                    item['workspace_id']?.toString() ??
                    'server-defined';
                return Card(
                  child: ListTile(
                    title: Text(
                      item['organization_name']?.toString() ??
                          item['organization_id']?.toString() ??
                          'Organization',
                    ),
                    subtitle: Text(
                      'Facility: ${item['facility_name'] ?? item['facility_id'] ?? '—'}\nWorkspace: $scope\nRole: ${item['role'] ?? 'server-defined'}',
                    ),
                    isThreeLine: true,
                    trailing: Chip(label: Text(status)),
                  ),
                );
              },
            ),
    );
  }
}
