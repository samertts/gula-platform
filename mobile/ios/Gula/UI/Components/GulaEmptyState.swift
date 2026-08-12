import SwiftUI

struct GulaEmptyState: View {
    let title: String
    let message: String
    let imageName: String?
    let actionTitle: String?
    let action: (() -> Void)?

    init(
        title: String,
        message: String,
        imageName: String? = nil,
        actionTitle: String? = nil,
        action: (() -> Void)? = nil
    ) {
        self.title = title
        self.message = message
        self.imageName = imageName
        self.actionTitle = actionTitle
        self.action = action
    }

    var body: some View {
        VStack(spacing: DesignTokens.Spacing.lg) {
            Spacer()

            if let imageName = imageName {
                Image(systemName: imageName)
                    .font(.system(size: 48))
                    .foregroundColor(.gulaTextTertiary)
            } else {
                Image(systemName: "tray")
                    .font(.system(size: 48))
                    .foregroundColor(.gulaTextTertiary)
            }

            Text(title)
                .gulaHeadlineSmall()
                .foregroundColor(.gulaTextPrimary)
                .multilineTextAlignment(.center)

            Text(message)
                .gulaBodyMedium()
                .foregroundColor(.gulaTextSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, DesignTokens.Spacing.xxl)

            if let actionTitle = actionTitle, let action = action {
                GulaButton(title: actionTitle, style: .outline, isFullWidth: false) {
                    action()
                }
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
