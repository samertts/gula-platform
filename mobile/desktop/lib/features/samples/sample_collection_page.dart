import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/validators.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_text_field.dart';
import '../../widgets/core/gula_dropdown.dart';
import '../../widgets/layout/page_container.dart';

class SampleCollectionPage extends StatefulWidget {
  const SampleCollectionPage({super.key});

  @override
  State<SampleCollectionPage> createState() => _SampleCollectionPageState();
}

class _SampleCollectionPageState extends State<SampleCollectionPage> {
  final _formKey = GlobalKey<FormState>();
  final _barcodeController = TextEditingController();
  final _patientController = TextEditingController();
  final _volumeController = TextEditingController();
  String? _sampleType;
  String? _containerType;
  bool _isLoading = false;

  @override
  void dispose() {
    _barcodeController.dispose();
    _patientController.dispose();
    _volumeController.dispose();
    super.dispose();
  }

  Future<void> _collect() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sample collected successfully'), backgroundColor: AppColors.success500),
      );
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return PageContainer(
      child: SingleChildScrollView(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 600),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
                    const SizedBox(width: 8),
                    const Text('Sample Collection', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
                  ],
                ),
                const SizedBox(height: 24),
                GulaTextField(
                  label: 'Barcode *',
                  hint: 'Scan or enter barcode',
                  controller: _barcodeController,
                  prefixIcon: Icons.qr_code_scanner,
                  validator: AppValidators.sampleBarcode,
                ),
                const SizedBox(height: 16),
                GulaTextField(
                  label: 'Patient *',
                  hint: 'Search patient',
                  controller: _patientController,
                  prefixIcon: Icons.search,
                  validator: (v) => AppValidators.required(v, fieldName: 'Patient'),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: GulaDropdown<String?>(
                        label: 'Sample Type *',
                        value: _sampleType,
                        items: ['Blood', 'Urine', 'Stool', 'Swab', 'Serum', 'Plasma']
                            .map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                        onChanged: (v) => setState(() => _sampleType = v),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: GulaDropdown<String?>(
                        label: 'Container',
                        value: _containerType,
                        items: ['EDTA Tube', 'Plain Tube', 'Citrate Tube', 'Sterile Container', 'Swab']
                            .map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                        onChanged: (v) => setState(() => _containerType = v),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                GulaTextField(label: 'Volume (mL)', controller: _volumeController, keyboardType: TextInputType.number),
                const SizedBox(height: 32),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    GulaButton(label: 'Cancel', variant: GulaButtonVariant.text, onPressed: () => context.pop()),
                    const SizedBox(width: 12),
                    GulaButton(label: 'Collect Sample', isLoading: _isLoading, onPressed: _collect),
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
