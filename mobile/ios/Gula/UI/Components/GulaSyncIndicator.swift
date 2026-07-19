import SwiftUI

struct GulaSyncIndicator: View {
    @EnvironmentObject var syncEngine: SyncEngine

    var body: some View {
        HStack(spacing: DesignTokens.Spacing.xs) {
            if syncEngine.isSyncing {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle(tint: .gulaPrimary))
                    .scaleEffect(0.7)

                Text("syncing".localized)
                    .gulaLabelSmall()
                    .foregroundColor(.gulaTextSecondary)

                if syncEngine.syncProgress > 0 {
                    Text("\(Int(syncEngine.syncProgress * 100))%")
                        .gulaLabelSmall()
                        .foregroundColor(.gulaTextTertiary)
                }
            } else if let lastSync = syncEngine.lastSyncDate {
                Image(systemName: "checkmark.icloud.fill")
                    .font(.system(size: 12))
                    .foregroundColor(.gulaSuccess)

                Text("synced_at".localized + " " + lastSync.formatted(date: .abbreviated, time: .shortened))
                    .gulaLabelSmall()
                    .foregroundColor(.gulaTextTertiary)
            }
        }
        .padding(.horizontal, DesignTokens.Spacing.sm)
        .padding(.vertical, DesignTokens.Spacing.xxs)
        .background(Color.gulaSurfaceSecondary.opacity(0.9))
        .cornerRadius(DesignTokens.Radius.full)
        .shadow(color: Color.black.opacity(0.1), radius: 4, x: 0, y: 2)
    }
}
