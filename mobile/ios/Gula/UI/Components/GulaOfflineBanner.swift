import SwiftUI

struct GulaOfflineBanner: View {
    @EnvironmentObject var networkMonitor: NetworkMonitor

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: DesignTokens.Spacing.sm) {
                Image(systemName: "wifi.slash")
                    .font(.system(size: 14))
                    .foregroundColor(.white)

                Text("offline_message".localized)
                    .gulaLabelMedium()
                    .foregroundColor(.white)

                Spacer()

                if !networkMonitor.isConnected {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(0.7)
                }
            }
            .padding(.horizontal, DesignTokens.Spacing.md)
            .padding(.vertical, DesignTokens.Spacing.sm)
            .background(Color.gulaWarning)
        }
    }
}

struct GulaOfflineBannerModifier: ViewModifier {
    @EnvironmentObject var networkMonitor: NetworkMonitor

    func body(content: Content) -> some View {
        content
            .overlay(alignment: .top) {
                if !networkMonitor.isConnected {
                    GulaOfflineBanner()
                        .transition(.move(edge: .top))
                        .animation(.easeInOut, value: networkMonitor.isConnected)
                }
            }
    }
}

extension View {
    func withOfflineBanner() -> some View {
        modifier(GulaOfflineBannerModifier())
    }
}
