import SwiftUI

struct MFAView: View {
    @Binding var mfaCode: String
    let onSubmit: () -> Void
    @Environment(\.dismiss) var dismiss
    @Environment(\.locale) var locale

    @FocusState private var focusedField: Bool

    var body: some View {
        VStack(spacing: DesignTokens.Spacing.xl) {
            Spacer()

            Image(systemName: "lock.shield.fill")
                .font(.system(size: 64))
                .foregroundColor(.gulaPrimary)

            Text("mfa_title".localized)
                .gulaHeadlineMedium()
                .foregroundColor(.gulaTextPrimary)

            Text("mfa_instructions".localized)
                .gulaBodyMedium()
                .foregroundColor(.gulaTextSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, DesignTokens.Spacing.xl)

            TextField("mfa_code_placeholder".localized, text: $mfaCode)
                .gulaTitleLarge()
                .fontWeight(.bold)
                .multilineTextAlignment(.center)
                .keyboardType(.numberPad)
                .textContentType(.oneTimeCode)
                .padding()
                .background(Color.gulaSurfaceSecondary)
                .cornerRadius(DesignTokens.Radius.md)
                .padding(.horizontal, DesignTokens.Spacing.xxl)
                .focused($focusedField)

            GulaButton(title: "verify".localized, isDisabled: mfaCode.count < 4) {
                onSubmit()
            }
            .padding(.horizontal, DesignTokens.Spacing.xxl)

            Button("mfa_resend_code".localized) {
            }
            .gulaBodyMedium()
            .foregroundColor(.gulaPrimary)

            Spacer()
        }
        .padding()
        .background(Color.gulaSurfacePrimary)
        .onAppear {
            focusedField = true
        }
    }
}
