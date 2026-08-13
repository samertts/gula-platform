import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_text_field.dart';
import '../../widgets/layout/page_container.dart';

class ResultEntryPage extends StatefulWidget {
  const ResultEntryPage({super.key});

  @override
  State<ResultEntryPage> createState() => _ResultEntryPageState();
}

class _ResultEntryPageState extends State<ResultEntryPage> {
  final _orderController = TextEditingController();
  final Map<String, TextEditingController> _resultControllers = {};
  bool _isLoading = false;

  final _tests = ['Hemoglobin', 'WBC', 'RBC', 'Platelets', 'Hematocrit', 'MCV', 'MCH', 'MCHC'];
  final _units = ['g/dL', 'K/uL', 'M/uL', 'K/uL', '%', 'fL', 'pg', 'g/dL'];
  final _references = ['13.5-17.5', '4.5-11.0', '4.7-6.1', '150-400', '42-50', '80-100', '27-34', '32-36'];

  @override
  void initState() {
    super.initState();
    for (final test in _tests) {
      _resultControllers[test] = TextEditingController();
    }
  }

  @override
  void dispose() {
    _orderController.dispose();
    for (final c in _resultControllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Results submitted for validation'), backgroundColor: AppColors.success500),
      );
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: SingleChildScrollView(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 900),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
                  const SizedBox(width: 8),
                  const Text('Result Entry', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
                ],
              ),
              const SizedBox(height: 24),
              GulaTextField(
                label: 'Order Number',
                hint: 'Scan or enter order barcode',
                controller: _orderController,
                prefixIcon: Icons.qr_code_scanner,
              ),
              const SizedBox(height: 24),
              const Text('CBC - Complete Blood Count', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              const SizedBox(height: 16),
              ...List.generate(_tests.length, (i) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  children: [
                    SizedBox(width: 150, child: Text(_tests[i], style: const TextStyle(fontSize: 14))),
                    SizedBox(width: 120, child: Text('Ref: ${_references[i]}', style: const TextStyle(fontSize: 12, color: AppColors.textSecondary))),
                    SizedBox(
                      width: 120,
                      child: GulaTextField(
                        controller: _resultControllers[_tests[i]],
                        hint: 'Result',
                        keyboardType: TextInputType.number,
                      ),
                    ),
                    SizedBox(width: 80, child: Text(_units[i], style: const TextStyle(fontSize: 13, color: AppColors.textSecondary))),
                  ],
                ),
              )),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  GulaButton(label: 'Cancel', variant: GulaButtonVariant.text, onPressed: () => context.pop()),
                  const SizedBox(width: 12),
                  GulaButton(label: 'Submit for Validation', isLoading: _isLoading, onPressed: _submit),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
