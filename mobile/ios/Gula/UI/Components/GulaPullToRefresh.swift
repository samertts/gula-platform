import SwiftUI

struct GulaPullToRefresh: ViewModifier {
    let isRefreshing: Bool
    let onRefresh: () -> Void

    func body(content: Content) -> some View {
        if #available(iOS 15.0, *) {
            content
                .refreshable {
                    await withCheckedContinuation { continuation in
                        onRefresh()
                        continuation.resume()
                    }
                }
        } else {
            content
                .overlay(
                    PullToRefreshView(isRefreshing: isRefreshing, onRefresh: onRefresh)
                )
        }
    }
}

struct PullToRefreshView: View {
    let isRefreshing: Bool
    let onRefresh: () -> Void

    var body: some View {
        VStack {
            if isRefreshing {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle(tint: .gulaPrimary))
                    .padding()
            }
            Spacer()
        }
        .frame(maxWidth: .infinity)
    }
}

extension View {
    func gulaPullToRefresh(isRefreshing: Bool, onRefresh: @escaping () -> Void) -> some View {
        modifier(GulaPullToRefresh(isRefreshing: isRefreshing, onRefresh: onRefresh))
    }
}
