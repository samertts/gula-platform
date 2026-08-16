import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_endpoints.dart';
import '../../core/providers/app_providers.dart';

class SecurityCenterPage extends ConsumerStatefulWidget {
  const SecurityCenterPage({super.key});

  @override
  ConsumerState<SecurityCenterPage> createState() => _SecurityCenterPageState();
}

class _SecurityCenterPageState extends ConsumerState<SecurityCenterPage> {
  bool _loading = true;
  bool _terminating = false;
  String? _error;
  Map<String, dynamic>? _mfa;
  List<dynamic> _devices = const [];
  List<dynamic> _sessions = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final auth = ref.read(authProviderProvider);
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final mfaResponse = await auth.manager.apiClient.get(
        ApiEndpoints.mfaStatus,
      );
      final devicesResponse = await auth.manager.apiClient.get(
        ApiEndpoints.mfaDevices,
      );
      final accountId = auth.workspaceContext?['account_id']?.toString();
      if (accountId != null) {
        final sessionsResponse = await auth.manager.apiClient.get(
          ApiEndpoints.accountSessions(accountId),
        );
        final body = sessionsResponse.data;
        _sessions = body is Map<String, dynamic>
            ? (body['sessions'] as List? ?? const [])
            : (body is List ? body : const []);
      }
      final mfaBody = mfaResponse.data;
      final deviceBody = devicesResponse.data;
      _mfa = mfaBody is Map<String, dynamic> ? mfaBody : null;
      _devices = deviceBody is Map<String, dynamic>
          ? (deviceBody['devices'] as List? ?? const [])
          : (deviceBody is List ? deviceBody : const []);
    } catch (_) {
      _error = 'Some security details are unavailable. No cached values are shown as current.';
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _logoutAll() async {
    final accountId = ref
        .read(authProviderProvider)
        .workspaceContext?['account_id']
        ?.toString();
    if (accountId == null) return;
    setState(() => _terminating = true);
    try {
      await ref
          .read(authProviderProvider)
          .manager
          .apiClient
          .post(ApiEndpoints.terminateAllSessions(accountId), data: {});
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Other sessions were terminated by the server.'),
          ),
        );
    } catch (_) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('The server did not approve terminating sessions.'),
          ),
        );
    } finally {
      if (mounted) setState(() => _terminating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Security Center')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  if (_error != null)
                    Text(_error!, style: const TextStyle(color: Colors.orange)),
                  Card(
                    child: ListTile(
                      title: const Text('MFA status'),
                      subtitle: Text(
                        _mfa?['enabled'] == true ? 'Enabled' : 'Not enabled',
                      ),
                    ),
                  ),
                  Card(
                    child: ListTile(
                      title: const Text('MFA devices'),
                      subtitle: Text(
                        '${_devices.length} server-reflected device(s)',
                      ),
                    ),
                  ),
                  Card(
                    child: ListTile(
                      title: const Text('Current sessions'),
                      subtitle: Text(
                        '${_sessions.length} server-reflected session(s)',
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  FilledButton(
                    onPressed: _terminating ? null : _logoutAll,
                    child: Text(
                      _terminating
                          ? 'Terminating…'
                          : 'Logout all other sessions',
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
