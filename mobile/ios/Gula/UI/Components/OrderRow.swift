import SwiftUI

struct OrderRow: View {
    let order: OrderEntity
    @Environment(\.locale) var locale

    var body: some View {
        HStack(spacing: DesignTokens.Spacing.md) {
            VStack(alignment: locale.isArabic ? .trailing : .leading, spacing: 4) {
                HStack(spacing: DesignTokens.Spacing.xs) {
                    Image(systemName: "list.clipboard")
                        .font(.system(size: 14))
                        .foregroundColor(.gulaPrimary)

                    Text("order_id_prefix".localized + " #\(order.id)")
                        .gulaBodyMedium()
                        .fontWeight(.semibold)
                        .foregroundColor(.gulaTextPrimary)
                }

                if let doctorName = order.doctorName {
                    HStack(spacing: DesignTokens.Spacing.xs) {
                        Image(systemName: "stethoscope")
                            .font(.system(size: 10))
                            .foregroundColor(.gulaTextTertiary)
                        Text(doctorName)
                            .gulaLabelSmall()
                            .foregroundColor(.gulaTextSecondary)
                    }
                }

                if let createdAt = order.createdAt {
                    Text(createdAt.formatted(date: .abbreviated, time: .shortened))
                        .gulaLabelSmall()
                        .foregroundColor(.gulaTextTertiary)
                }
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 4) {
                GulaBadge(.status(order.status), size: .small)

                if let priority = order.priority, priority != "routine" {
                    Text(priorityDisplayName(priority))
                        .gulaLabelSmall()
                        .foregroundColor(Color.priorityColor(for: priority))
                }
            }
        }
        .padding(.vertical, DesignTokens.Spacing.xs)
        .padding(.horizontal, DesignTokens.Spacing.md)
        .contentShape(Rectangle())
    }

    private func priorityDisplayName(_ priority: String) -> String {
        switch priority.lowercased() {
        case "urgent": return "priority_urgent".localized
        case "stat": return "priority_stat".localized
        case "high": return "priority_high".localized
        default: return priority
        }
    }
}
