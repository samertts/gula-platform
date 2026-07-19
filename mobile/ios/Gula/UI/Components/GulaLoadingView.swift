import SwiftUI

struct GulaLoadingView: View {
    let message: String?
    let scale: CGFloat

    init(message: String? = nil, scale: CGFloat = 1.0) {
        self.message = message
        self.scale = scale
    }

    var body: some View {
        VStack(spacing: DesignTokens.Spacing.md) {
            ProgressView()
                .scaleEffect(scale)
                .tint(.gulaPrimary)

            if let message = message {
                Text(message)
                    .gulaBodyMedium()
                    .foregroundColor(.gulaTextSecondary)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

struct GulaPageLoadingView: View {
    var body: some View {
        VStack(spacing: DesignTokens.Spacing.lg) {
            ProgressView()
                .scaleEffect(1.5)
                .tint(.gulaPrimary)

            Text("loading".localized)
                .gulaBodyLarge()
                .foregroundColor(.gulaTextSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.gulaSurfacePrimary)
    }
}

struct GulaInlineLoading: View {
    var body: some View {
        HStack(spacing: DesignTokens.Spacing.sm) {
            ProgressView()
                .scaleEffect(0.8)
                .tint(.gulaPrimary)
            Text("loading".localized)
                .gulaBodySmall()
                .foregroundColor(.gulaTextSecondary)
        }
        .padding(.vertical, DesignTokens.Spacing.xs)
    }
}
