import SwiftUI

struct LoginView: View {
    @StateObject private var viewModel = AuthViewModel()
    @EnvironmentObject var themeManager: ThemeManager
    @Environment(\.locale) var locale

    var body: some View {
        ScrollView {
            VStack(spacing: DesignTokens.Spacing.xl) {
                Spacer().frame(height: 60)

                VStack(spacing: DesignTokens.Spacing.sm) {
                    Image(systemName: "cross.case.fill")
                        .font(.system(size: 60))
                        .foregroundColor(.gulaPrimary)

                    Text("app_name".localized)
                        .gulaDisplaySmall()
                        .fontWeight(.bold)
                        .foregroundColor(.gulaPrimary)

                    Text("app_subtitle".localized)
                        .gulaBodyMedium()
                        .foregroundColor(.gulaTextSecondary)
                        .multilineTextAlignment(.center)
                }

                Spacer().frame(height: 20)

                if let errorMessage = viewModel.errorMessage {
                    GulaAlert(type: .error, message: errorMessage, onDismiss: {
                        viewModel.errorMessage = nil
                    })
                }

                VStack(spacing: DesignTokens.Spacing.md) {
                    GulaTextField(
                        title: "email".localized,
                        text: $viewModel.email,
                        placeholder: "email_placeholder".localized,
                        error: viewModel.validationErrors["email"],
                        keyboardType: .emailAddress,
                        textContentType: .emailAddress,
                        submitLabel: .next
                    )

                    GulaTextField(
                        title: "password".localized,
                        text: $viewModel.password,
                        placeholder: "password_placeholder".localized,
                        error: viewModel.validationErrors["password"],
                        isSecure: true,
                        textContentType: .password,
                        submitLabel: .done
                    )

                    HStack {
                        Toggle("remember_me".localized, isOn: $viewModel.rememberMe)
                            .gulaLabelMedium()
                            .tint(.gulaPrimary)

                        Spacer()

                        Button("forgot_password".localized) {
                        }
                        .gulaLabelMedium()
                        .foregroundColor(.gulaPrimary)
                    }
                }

                GulaButton(
                    title: "login".localized,
                    style: .primary,
                    isLoading: viewModel.isLoading,
                    isDisabled: !viewModel.isFormValid
                ) {
                    viewModel.login()
                }

                if viewModel.canUseBiometric {
                    VStack(spacing: DesignTokens.Spacing.sm) {
                        Text("or".localized)
                            .gulaBodySmall()
                            .foregroundColor(.gulaTextTertiary)

                        Button(action: { viewModel.loginWithBiometric() }) {
                            HStack(spacing: DesignTokens.Spacing.sm) {
                                Image(systemName: BiometricAuth.biometryType == .faceID ? "faceid" : "touchid")
                                    .font(.title2)
                                Text(BiometricAuth.biometryType == .faceID ? "login_with_faceid".localized : "login_with_touchid".localized)
                                    .gulaBodyMedium()
                            }
                            .foregroundColor(.gulaPrimary)
                        }
                    }
                }

                Spacer()
            }
            .padding(.horizontal, DesignTokens.Spacing.xl)
        }
        .background(Color.gulaSurfacePrimary)
        .onAppear {
            viewModel.checkForSavedCredentials()
        }
        .sheet(isPresented: $viewModel.showMFA) {
            MFAView(mfaCode: $viewModel.mfaCode, onSubmit: { viewModel.loginWithMFA() })
        }
        .sheet(isPresented: $viewModel.showBiometricSetup) {
            BiometricSetupView(
                onEnable: { viewModel.enableBiometric() },
                onSkip: { viewModel.skipBiometric() }
            )
        }
    }
}
