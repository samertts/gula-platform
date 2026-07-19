import SwiftUI

struct BiometricSetupView: View {
    let onEnable: () -> Void
    let onSkip: () -> Void
    @Environment(\.locale) var locale

    var body: some View {
        VStack(spacing: DesignTokens.Spacing.xl) {
            Spacer()

            Image(systemName: BiometricAuth.biometryType == .faceID ? "faceid" : "touchid")
                .font(.system(size: 72))
                .foregroundColor(.gulaPrimary)

            Text("biometric_setup_title".localized)
                .gulaHeadlineMedium()
                .foregroundColor(.gulaTextPrimary)
                .multilineTextAlignment(.center)

            Text(BiometricAuth.biometryType == .faceID
                 ? "biometric_faceid_description".localized
                 : "biometric_touchid_description".localized)
                .gulaBodyMedium()
                .foregroundColor(.gulaTextSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, DesignTokens.Spacing.xl)

            VStack(spacing: DesignTokens.Spacing.sm) {
                HStack(spacing: DesignTokens.Spacing.md) {
                    Image(systemName: "checkmark.shield.fill")
                        .foregroundColor(.gulaSuccess)
                    Text("biometric_fast_login".localized)
                        .gulaBodySmall()
                        .foregroundColor(.gulaTextSecondary)
                    Spacer()
                }
                HStack(spacing: DesignTokens.Spacing.md) {
                    Image(systemName: "lock.fill")
                        .foregroundColor(.gulaSuccess)
                    Text("biometric_secure".localized)
                        .gulaBodySmall()
                        .foregroundColor(.gulaTextSecondary)
                    Spacer()
                }
            }
            .padding(.horizontal, DesignTokens.Spacing.xxl)

            VStack(spacing: DesignTokens.Spacing.md) {
                GulaButton(
                    title: BiometricAuth.biometryType == .faceID
                        ? "enable_faceid".localized
                        : "enable_touchid".localized,
                    style: .primary
                ) {
                    onEnable()
                }

                GulaButton(title: "skip".localized, style: .ghost) {
                    onSkip()
                }
            }
            .padding(.horizontal, DesignTokens.Spacing.xxl)

            Spacer()
        }
        .padding()
        .background(Color.gulaSurfacePrimary)
    }
}
