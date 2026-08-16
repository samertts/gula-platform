import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers/app_providers.dart';

class WorkspacePage extends ConsumerStatefulWidget {
  const WorkspacePage({super.key});

  @override
  ConsumerState<WorkspacePage> createState() => _WorkspacePageState();
}

class _WorkspacePageState extends ConsumerState<WorkspacePage> {
  String? _selected;
  bool _loading = false;
  String? _error;

  Future<void> _switch() async {
    final id = _selected;
    if (id == null || id.isEmpty) return;
    setState(() { _loading = true; _error = null; });
    try {
      await ref.read(authProviderProvider).switchWorkspace(id);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Workspace context approved by server.')));
    } catch (_) {
      if (mounted) setState(() => _error = 'Workspace switching was denied by the server. The previous context was kept.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProviderProvider);
    final workspaces = auth.workspaces;
    return Scaffold(
      appBar: AppBar(title: const Text('Workspace context')),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          const Text('Choose a workspace explicitly. Authorization remains server-side.'),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: _selected,
            decoration: const InputDecoration(labelText: 'Workspace'),
            items: workspaces.map((item) {
              final id = item['id']?.toString() ?? item['uuid']?.toString();
              return id == null ? null : DropdownMenuItem(value: id, child: Text(item['name']?.toString() ?? id));
            }).whereType<DropdownMenuItem<String>>().toList(),
            onChanged: _loading ? null : (value) => setState(() => _selected = value),
          ),
          const SizedBox(height: 16),
          FilledButton(onPressed: _loading ? null : _switch, child: Text(_loading ? 'Approving…' : 'Use workspace')),
          if (_error != null) ...[const SizedBox(height: 12), Text(_error!, style: TextStyle(color: Colors.red))],
          if (auth.workspaceContext != null) ...[const SizedBox(height: 20), Text('Current context: ${auth.workspaceContext}')],
        ]),
      ),
    );
  }
}
