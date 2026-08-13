import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/validators.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_text_field.dart';
import '../../widgets/core/gula_dropdown.dart';
import '../../widgets/layout/page_container.dart';

class OrderCreatePage extends StatefulWidget {
  const OrderCreatePage({super.key});

  @override
  State<OrderCreatePage> createState() => _OrderCreatePageState();
}

class _OrderCreatePageState extends State<OrderCreatePage> {
  final _formKey = GlobalKey<FormState>();
  final _patientSearchController = TextEditingController();
  final _notesController = TextEditingController();
  String? _selectedPatient;
  String? _priority;
  List<String> _selectedTests = [];
  bool _isLoading = false;

  final _availableTests = [
    'Complete Blood Count', 'Liver Function Test', 'Lipid Profile',
    'Renal Function Test', 'Thyroid Panel', 'Blood Glucose',
    'Hemoglobin A1C', 'Vitamin D', 'Iron Studies', 'Coagulation Profile',
  ];

  @override
  void dispose() {
    _patientSearchController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedTests.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select at least one test'), backgroundColor: AppColors.error500),
      );
      return;
    }

    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Order created successfully'), backgroundColor: AppColors.success500),
      );
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: SingleChildScrollView(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 800),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
                    const SizedBox(width: 8),
                    const Text('New Order', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
                  ],
                ),
                const SizedBox(height: 24),
                const Text('Patient Information', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                const SizedBox(height: 16),
                GulaTextField(
                  label: 'Search Patient *',
                  hint: 'Search by name or national ID',
                  controller: _patientSearchController,
                  prefixIcon: Icons.search,
                  validator: (v) => AppValidators.required(v, fieldName: 'Patient'),
                ),
                const SizedBox(height: 16),
                const Text('Order Details', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                const SizedBox(height: 16),
                GulaDropdown<String?>(
                  label: 'Priority',
                  value: _priority,
                  items: ['Routine', 'Urgent', 'STAT']
                      .map((p) => DropdownMenuItem(value: p, child: Text(p))).toList(),
                  onChanged: (v) => setState(() => _priority = v),
                ),
                const SizedBox(height: 16),
                const Text('Select Tests *', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    border: Border.all(color: AppColors.border),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _availableTests.map((test) => FilterChip(
                      label: Text(test, style: const TextStyle(fontSize: 12)),
                      selected: _selectedTests.contains(test),
                      onSelected: (selected) {
                        setState(() {
                          if (selected) {
                            _selectedTests.add(test);
                          } else {
                            _selectedTests.remove(test);
                          }
                        });
                      },
                      selectedColor: AppColors.primary100,
                      checkmarkColor: AppColors.primary700,
                    )).toList(),
                  ),
                ),
                const SizedBox(height: 16),
                GulaTextField(label: 'Notes', controller: _notesController, maxLines: 3),
                const SizedBox(height: 32),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    GulaButton(label: 'Cancel', variant: GulaButtonVariant.text, onPressed: () => context.pop()),
                    const SizedBox(width: 12),
                    GulaButton(label: 'Create Order', isLoading: _isLoading, onPressed: _submit),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
