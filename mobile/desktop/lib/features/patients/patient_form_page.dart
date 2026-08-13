import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/validators.dart';
import '../../widgets/core/gula_button.dart';
import '../../widgets/core/gula_text_field.dart';
import '../../widgets/core/gula_dropdown.dart';
import '../../widgets/layout/section_header.dart';
import '../../widgets/layout/page_container.dart';

class PatientFormPage extends StatefulWidget {
  final String? patientId;

  const PatientFormPage({super.key, this.patientId});

  @override
  State<PatientFormPage> createState() => _PatientFormPageState();
}

class _PatientFormPageState extends State<PatientFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameController = TextEditingController();
  final _fatherNameController = TextEditingController();
  final _grandFatherNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _nationalIdController = TextEditingController();
  final _phoneController = TextEditingController();
  final _emailController = TextEditingController();
  final _addressController = TextEditingController();
  final _cityController = TextEditingController();
  final _notesController = TextEditingController();
  String? _gender;
  String? _bloodGroup;
  DateTime? _dateOfBirth;
  bool _isLoading = false;

  bool get _isEditing => widget.patientId != null;

  @override
  void dispose() {
    _firstNameController.dispose();
    _fatherNameController.dispose();
    _grandFatherNameController.dispose();
    _lastNameController.dispose();
    _nationalIdController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    _addressController.dispose();
    _cityController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1));

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _isEditing
                ? 'Patient updated successfully'
                : 'Patient created successfully',
          ),
          backgroundColor: AppColors.success500,
        ),
      );
      context.pop();
    }
    setState(() => _isLoading = false);
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
                    IconButton(
                      icon: const Icon(Icons.arrow_back),
                      onPressed: () => context.pop(),
                    ),
                    const SizedBox(width: 8),
                    SectionHeader(
                      title: _isEditing ? 'Edit Patient' : 'Add Patient',
                      subtitle: _isEditing
                          ? 'Update patient information'
                          : 'Register a new patient',
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                const Text(
                  'Personal Information',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: GulaTextField(
                        label: 'First Name *',
                        controller: _firstNameController,
                        validator: (v) =>
                            AppValidators.required(v, fieldName: 'First Name'),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: GulaTextField(
                        label: 'Father Name',
                        controller: _fatherNameController,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: GulaTextField(
                        label: 'Grand Father Name',
                        controller: _grandFatherNameController,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: GulaTextField(
                        label: 'Last Name',
                        controller: _lastNameController,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: GulaDropdown<String?>(
                        label: 'Gender *',
                        value: _gender,
                        items: [
                          DropdownMenuItem(
                            value: 'm',
                            child: const Text('Male'),
                          ),
                          DropdownMenuItem(
                            value: 'f',
                            child: const Text('Female'),
                          ),
                        ],
                        onChanged: (v) => setState(() => _gender = v),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: InkWell(
                        onTap: () => _pickDate(context),
                        child: GulaTextField(
                          label: 'Date of Birth',
                          hint: 'YYYY-MM-DD',
                          controller: TextEditingController(
                            text:
                                _dateOfBirth?.toIso8601String().substring(
                                  0,
                                  10,
                                ) ??
                                '',
                          ),
                          readOnly: true,
                          suffixIcon: Icons.calendar_today,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                const Text(
                  'Contact & Identification',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: GulaTextField(
                        label: 'National ID',
                        controller: _nationalIdController,
                        validator: AppValidators.nationalId,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: GulaTextField(
                        label: 'Phone',
                        controller: _phoneController,
                        keyboardType: TextInputType.phone,
                        validator: AppValidators.phone,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: GulaTextField(
                        label: 'Email',
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        validator: AppValidators.email,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: GulaDropdown<String?>(
                        label: 'Blood Group',
                        value: _bloodGroup,
                        items:
                            ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
                                .map(
                                  (bg) => DropdownMenuItem(
                                    value: bg,
                                    child: Text(bg),
                                  ),
                                )
                                .toList(),
                        onChanged: (v) => setState(() => _bloodGroup = v),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: GulaTextField(
                        label: 'City',
                        controller: _cityController,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: GulaTextField(
                        label: 'Address',
                        controller: _addressController,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                GulaTextField(
                  label: 'Notes',
                  controller: _notesController,
                  maxLines: 3,
                ),
                const SizedBox(height: 32),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    GulaButton(
                      label: 'Cancel',
                      variant: GulaButtonVariant.text,
                      onPressed: () => context.pop(),
                    ),
                    const SizedBox(width: 12),
                    GulaButton(
                      label: _isEditing ? 'Update' : 'Save',
                      isLoading: _isLoading,
                      onPressed: _save,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _pickDate(BuildContext context) async {
    final date = await showDatePicker(
      context: context,
      initialDate: _dateOfBirth ?? DateTime(1990),
      firstDate: DateTime(1900),
      lastDate: DateTime.now(),
    );
    if (date != null) setState(() => _dateOfBirth = date);
  }
}
