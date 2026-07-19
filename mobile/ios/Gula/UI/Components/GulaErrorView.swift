import SwiftUI

struct GulaErrorView: View {
    let title: String
    let message: String
    let retryTitle: String?
    let retryAction: (() -> Void)?
    let dismissAction: (() -> Void)?

    init(
        title: String = "error_occurred".localized,
        message: String,
        retryTitle: String? = "retry".localized,
        retryAction: (() -> Void)? = nil,
        dismissAction: (() -> Void)? = nil
    ) {
        self.title = title
        self.message = message
        self.retryTitle = retryTitle
        self.retryAction = retryAction
        self.dismissAction = dismissAction
    }

    var body: some View {
        VStack(spacing: DesignTokens.Spacing.lg) {
            Spacer()

            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 48))
                .foregroundColor(.gulaWarning)

            Text(title)
                .gulaHeadlineSmall()
                .foregroundColor(.gulaTextPrimary)
                .multilineTextAlignment(.center)

            Text(message)
                .gulaBodyMedium()
                .foregroundColor(.gulaTextSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, DesignTokens.Spacing.xxl)

            VStack(spacing: DesignTokens.Spacing.sm) {
                if let retryAction = retryAction, let retryTitle = retryTitle {
                    GulaButton(title: retryTitle, style: .primary, isFullWidth: false) {
                        retryAction()
                    }
                }

                if let dismissAction = dismissAction {
                    GulaButton(title: "dismiss".localized, style: .ghost, isFullWidth: false) {
                        dismissAction()
                    }
                }
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
