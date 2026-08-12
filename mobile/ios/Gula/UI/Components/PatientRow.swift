import SwiftUI

struct PatientRow: View {
    let patient: PatientEntity
    @Environment(\.locale) var locale

    var body: some View {
        HStack(spacing: DesignTokens.Spacing.md) {
            Circle()
                .fill(patientGenderColor)
                .frame(width: 44, height: 44)
                .overlay(
                    Text(initials)
                        .gulaLabelMedium()
                        .foregroundColor(.white)
                )

            VStack(alignment: locale.isArabic ? .trailing : .leading, spacing: 4) {
                Text(patient.fullName)
                    .gulaBodyLarge()
                    .fontWeight(.semibold)
                    .foregroundColor(.gulaTextPrimary)

                HStack(spacing: DesignTokens.Spacing.xs) {
                    Image(systemName: "phone.fill")
                        .font(.system(size: 10))
                        .foregroundColor(.gulaTextTertiary)
                    Text(patient.phone)
                        .gulaLabelSmall()
                        .foregroundColor(.gulaTextSecondary)

                    if let gender = patient.gender {
                        Text("•")
                            .foregroundColor(.gulaTextTertiary)
                        Text(genderDisplayName(gender))
                            .gulaLabelSmall()
                            .foregroundColor(.gulaTextSecondary)
                    }
                }
            }

            Spacer()

            GulaBadge(.status(patient.status), size: .small)
        }
        .padding(.vertical, DesignTokens.Spacing.xs)
        .padding(.horizontal, DesignTokens.Spacing.md)
        .contentShape(Rectangle())
    }

    private var initials: String {
        let parts = patient.fullName.split(separator: " ")
        let first = parts.first?.prefix(1) ?? ""
        let last = parts.dropFirst().first?.prefix(1) ?? ""
        return "\(first)\(last)".uppercased()
    }

    private var patientGenderColor: Color {
        switch patient.gender?.lowercased() {
        case "male", "m": return .gulaInfo
        case "female", "f": return .gulaAccent
        default: return .gulaSecondary
        }
    }

    private func genderDisplayName(_ gender: String) -> String {
        switch gender.lowercased() {
        case "male", "m": return "male".localized
        case "female", "f": return "female".localized
        default: return gender
        }
    }
}
