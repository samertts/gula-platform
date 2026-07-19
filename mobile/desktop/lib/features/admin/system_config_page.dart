import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../widgets/core/gula_card.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_text_field.dart';
import '../../widgets/layout/page_container.dart';
import '../../widgets/layout/section_header.dart';

class SystemConfigPage extends StatefulWidget {
  const SystemConfigPage({super.key});

  @override
  State<SystemConfigPage> createState() => _SystemConfigPageState();
}

class _SystemConfigPageState extends State<SystemConfigPage> {
  final _labNameController = TextEditingController(text: 'Central Lab');
  final _addressController = TextEditingController(text: 'Baghdad, Iraq');
  final _phoneController = TextEditingController(text: '+964 770 123 4567');

  @override
  void dispose() {
    _labNameController.dispose();
    _addressController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: SingleChildScrollView(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 700),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(title: 'System Configuration'),
              const SizedBox(height: 24),
              GulaCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('General Settings', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    const Divider(height: 24),
                    GulaTextField(label: 'Laboratory Name', controller: _labNameController),
                    const SizedBox(height: 16),
                    GulaTextField(label: 'Address', controller: _addressController),
                    const SizedBox(height: 16),
                    GulaTextField(label: 'Phone', controller: _phoneController, keyboardType: TextInputType.phone),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              GulaCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Sync Settings', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    const Divider(height: 24),
                    const ListTile(
                      title: Text('Auto Sync'),
                      subtitle: Text('Synchronize data every 30 seconds'),
                      trailing: Switch(value: true, onChanged: null),
                    ),
                    const ListTile(
                      title: Text('Sync on Wi-Fi Only'),
                      subtitle: Text('Only sync when connected to Wi-Fi'),
                      trailing: Switch(value: false, onChanged: null),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              GulaCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Security Settings', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    const Divider(height: 24),
                    const ListTile(
                      title: Text('Two-Factor Authentication'),
                      subtitle: Text('Require MFA for all users'),
                      trailing: Switch(value: true, onChanged: null),
                    ),
                    const ListTile(
                      title: Text('Session Timeout'),
                      subtitle: Text('Auto logout after 120 minutes of inactivity'),
                      trailing: Switch(value: true, onChanged: null),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: End,
                children: [
                  GulaButton(label: 'Reset to Defaults', variant: GulaButtonVariant.text, onPressed: () {}),
                  const SizedBox(width: 12),
                  GulaButton(label: 'Save Configuration', onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Configuration saved'), backgroundColor: AppColors.success500),
                    );
                  }),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
