import SwiftUI

enum AlertType {
    case info
    case success
    case warning
    case error

    var icon: String {
        switch self {
        case .info: return "info.circle.fill"
        case .success: return "checkmark.circle.fill"
        case .warning: return "exclamationmark.triangle.fill"
        case .error: return "xmark.circle.fill"
        }
    }

    var color: Color {
        switch self {
        case .info: return .gulaInfo
        case .success: return .gulaSuccess
        case .warning: return .gulaWarning
        case .error: return .gulaError
        }
    }

    var title: String {
        switch self {
        case .info: return "alert_info".localized
        case .success: return "alert_success".localized
        case .warning: return "alert_warning".localized
        case .error: return "alert_error".localized
        }
    }
}

struct GulaAlert: View {
    let type: AlertType
    let message: String
    let onDismiss: (() -> Void)?

    @Environment(\.locale) var locale

    init(
        type: AlertType,
        message: String,
        onDismiss: (() -> Void)? = nil
    ) {
        self.type = type
        self.message = message
        self.onDismiss = onDismiss
    }

    var body: some View {
        HStack(alignment: .top, spacing: DesignTokens.Spacing.sm) {
            Image(systemName: type.icon)
                .foregroundColor(type.color)
                .font(.system(size: 18))

            VStack(alignment: .leading, spacing: 2) {
                Text(type.title)
                    .gulaLabelMedium()
                    .foregroundColor(type.color)
                Text(message)
                    .gulaBodySmall()
                    .foregroundColor(.gulaTextSecondary)
            }

            if locale.isArabic {
                Spacer()
            }

            if let onDismiss = onDismiss {
                Button(action: onDismiss) {
                    Image(systemName: "xmark")
                        .foregroundColor(.gulaTextTertiary)
                        .font(.caption)
                }
                .buttonStyle(PlainButtonStyle())
            }

            if !locale.isArabic {
                Spacer()
            }
        }
        .padding(DesignTokens.Spacing.md)
        .background(type.color.opacity(0.1))
        .cornerRadius(DesignTokens.Radius.md)
        .overlay(
            RoundedRectangle(cornerRadius: DesignTokens.Radius.md)
                .stroke(type.color.opacity(0.3), lineWidth: 1)
        )
    }
}
