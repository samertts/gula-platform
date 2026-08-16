import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_endpoints.dart';
import '../../core/providers/app_providers.dart';

class AccountRequestPage extends ConsumerStatefulWidget {
  const AccountRequestPage({super.key});

  @override
  ConsumerState<AccountRequestPage> createState() => _AccountRequestPageState();
}

class _AccountRequestPageState extends ConsumerState<AccountRequestPage> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  bool _loading = false;
  bool _submitted = false;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _phone.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = null; });
    try {
      await ref.read(authProviderProvider).manager.apiClient.post(
        ApiEndpoints.accountRequests,
        data: {
          'display_name': _name.text.trim(),
          'email': _email.text.trim(),
          'phone': _phone.text.trim().isEmpty ? null : _phone.text.trim(),
          'requested_account_type': 'citizen',
        },
        idempotent: true,
      );
      if (mounted) setState(() { _loading = false; _submitted = true; });
    } catch (_) {
      if (mounted) setState(() { _loading = false; _error = 'The request could not be submitted. Please try again later.'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Request an account')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: _submitted
                ? const Column(mainAxisSize: MainAxisSize.min, children: [Icon(Icons.schedule, size: 56), SizedBox(height: 16), Text('Request received. It is pending review and does not create a session yet.')])
                : Form(
                    key: _formKey,
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                      TextFormField(controller: _name, decoration: const InputDecoration(labelText: 'Name'), validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null),
                      TextFormField(controller: _email, decoration: const InputDecoration(labelText: 'Email'), keyboardType: TextInputType.emailAddress, validator: (v) => v == null || !v.contains('@') ? 'Enter a valid email' : null),
                      TextFormField(controller: _phone, decoration: const InputDecoration(labelText: 'Phone (optional)'), keyboardType: TextInputType.phone),
                      if (_error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, style: const TextStyle(color: Colors.red))),
                      const SizedBox(height: 20),
                      FilledButton(onPressed: _loading ? null : _submit, child: Text(_loading ? 'Submitting…' : 'Submit request')),
                    ]),
                  ),
          ),
        ),
      ),
    );
  }
}
