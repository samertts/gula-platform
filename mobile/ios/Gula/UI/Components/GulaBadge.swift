import SwiftUI

enum BadgeStyle {
    case status(String)
    case count(Int)
    case dot(Color)
    case custom(text: String, color: Color)
}

struct GulaBadge: View {
    let style: BadgeStyle
    let size: BadgeSize

    enum BadgeSize {
        case small
        case medium
        case large

        var fontSize: GulaFontStyle {
            switch self {
            case .small: return .labelSmall
            case .medium: return .labelMedium
            case .large: return .labelLarge
            }
        }

        var padding: CGFloat {
            switch self {
            case .small: return 4
            case .medium: return 6
            case .large: return 8
            }
        }
    }

    init(_ style: BadgeStyle, size: BadgeSize = .medium) {
        self.style = style
        self.size = size
    }

    var body: some View {
        switch style {
        case .status(let status):
            statusBadge(status)
        case .count(let count):
            countBadge(count)
        case .dot(let color):
            dotBadge(color)
        case .custom(let text, let color):
            customBadge(text: text, color: color)
        }
    }

    private func statusBadge(_ status: String) -> some View {
        Text(statusDisplayName(for: status))
            .gulaFont(size.fontSize)
            .foregroundColor(.white)
            .padding(.horizontal, size.padding)
            .padding(.vertical, size.padding / 2)
            .background(Color.statusColor(for: status))
            .cornerRadius(4)
    }

    private func countBadge(_ count: Int) -> some View {
        Text("\(count)")
            .gulaFont(size.fontSize)
            .foregroundColor(.white)
            .frame(minWidth: 20, minHeight: 20)
            .padding(.horizontal, 6)
            .background(Color.gulaCritical)
            .clipShape(Capsule())
    }

    private func dotBadge(_ color: Color) -> some View {
        Circle()
            .fill(color)
            .frame(width: 8, height: 8)
    }

    private func customBadge(text: String, color: Color) -> some View {
        Text(text)
            .gulaFont(size.fontSize)
            .foregroundColor(.white)
            .padding(.horizontal, size.padding)
            .padding(.vertical, size.padding / 2)
            .background(color)
            .cornerRadius(4)
    }

    private func statusDisplayName(for status: String) -> String {
        switch status.lowercased() {
        case "active": return "status_active".localized
        case "pending": return "status_pending".localized
        case "completed": return "status_completed".localized
        case "cancelled": return "status_cancelled".localized
        case "verified": return "status_verified".localized
        case "rejected": return "status_rejected".localized
        case "processing": return "status_processing".localized
        case "collected": return "status_collected".localized
        case "received": return "status_received".localized
        case "critical": return "status_critical".localized
        default: return status.capitalized
        }
    }
}
