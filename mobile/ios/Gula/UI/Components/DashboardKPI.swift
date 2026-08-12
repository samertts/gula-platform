import SwiftUI

struct DashboardKPI: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    let trend: String?
    let trendDirection: TrendDirection?

    enum TrendDirection {
        case up, down, stable

        var icon: String {
            switch self {
            case .up: return "arrow.up.right"
            case .down: return "arrow.down.right"
            case .stable: return "arrow.right"
            }
        }

        var color: Color {
            switch self {
            case .up: return .gulaSuccess
            case .down: return .gulaError
            case .stable: return .gulaTextTertiary
            }
        }
    }

    init(
        title: String,
        value: String,
        icon: String,
        color: Color = .gulaPrimary,
        trend: String? = nil,
        trendDirection: TrendDirection? = nil
    ) {
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        self.trend = trend
        self.trendDirection = trendDirection
    }

    var body: some View {
        VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
            HStack(spacing: DesignTokens.Spacing.sm) {
                Image(systemName: icon)
                    .font(.system(size: 18))
                    .foregroundColor(color)
                    .frame(width: 36, height: 36)
                    .background(color.opacity(0.1))
                    .cornerRadius(DesignTokens.Radius.sm)

                Spacer()

                if let trend = trend, let direction = trendDirection {
                    HStack(spacing: 2) {
                        Image(systemName: direction.icon)
                            .font(.system(size: 10))
                        Text(trend)
                            .gulaLabelSmall()
                    }
                    .foregroundColor(direction.color)
                }
            }

            Text(value)
                .gulaTitleLarge()
                .fontWeight(.bold)
                .foregroundColor(.gulaTextPrimary)

            Text(title)
                .gulaLabelSmall()
                .foregroundColor(.gulaTextSecondary)
                .lineLimit(1)
        }
        .padding(DesignTokens.Spacing.md)
        .background(Color.gulaSurfacePrimary)
        .cornerRadius(DesignTokens.Radius.lg)
        .shadow(color: Color.black.opacity(0.04), radius: 4, x: 0, y: 2)
    }
}

struct DashboardQuickAction: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: DesignTokens.Spacing.sm) {
                Image(systemName: icon)
                    .font(.system(size: 24))
                    .foregroundColor(color)
                    .frame(width: 48, height: 48)
                    .background(color.opacity(0.1))
                    .cornerRadius(DesignTokens.Radius.md)

                Text(title)
                    .gulaLabelSmall()
                    .foregroundColor(.gulaTextPrimary)
                    .lineLimit(1)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, DesignTokens.Spacing.sm)
        }
        .buttonStyle(PlainButtonStyle())
    }
}
