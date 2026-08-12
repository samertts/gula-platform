import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../core/gula_card.dart';
import '../core/gula_badge.dart';

class PatientCard extends StatelessWidget {
  final String id;
  final String firstName;
  final String? fatherName;
  final String? lastName;
  final String gender;
  final String? dateOfBirth;
  final String? nationalId;
  final String? phone;
  final String? bloodGroup;
  final VoidCallback? onTap;
  final VoidCallback? onEdit;

  const PatientCard({
    super.key,
    required this.id,
    required this.firstName,
    this.fatherName,
    this.lastName,
    required this.gender,
    this.dateOfBirth,
    this.nationalId,
    this.phone,
    this.bloodGroup,
    this.onTap,
    this.onEdit,
  });

  @override
  Widget build(BuildContext context) {
    final fullName = [firstName, fatherName, lastName]
        .where((n) => n != null && n.isNotEmpty)
        .join(' ');

    return GulaCard(
      onTap: onTap,
      variant: GulaCardVariant.outlined,
      padding: const EdgeInsets.all(AppDimensions.space3),
      child: Row(
        children: [
          CircleAvatar(
            radius: 24,
            backgroundColor: gender == 'f' ? AppColors.secondary50 : AppColors.primary50,
            child: Icon(
              gender == 'f' ? Icons.female : Icons.male,
              color: gender == 'f' ? AppColors.secondary500 : AppColors.primary500,
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  fullName,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    if (nationalId != null) ...[
                      const Icon(Icons.badge_outlined, size: 14, color: AppColors.textSecondary),
                      const SizedBox(width: 4),
                      Text(
                        nationalId!,
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                      const SizedBox(width: 12),
                    ],
                    if (phone != null) ...[
                      const Icon(Icons.phone_outlined, size: 14, color: AppColors.textSecondary),
                      const SizedBox(width: 4),
                      Text(
                        phone!,
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    GulaBadge(
                      label: gender == 'm' ? 'Male' : 'Female',
                      status: gender == 'm' ? GulaBadgeStatus.info : GulaBadgeStatus.success,
                      showDot: false,
                    ),
                    if (bloodGroup != null) ...[
                      const SizedBox(width: 8),
                      GulaBadge(
                        label: bloodGroup!,
                        status: GulaBadgeStatus.neutral,
                        showDot: false,
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
          if (onEdit != null)
            IconButton(
              icon: const Icon(Icons.edit_outlined, size: 18),
              onPressed: onEdit,
              color: AppColors.textSecondary,
            ),
        ],
      ),
    );
  }
}
