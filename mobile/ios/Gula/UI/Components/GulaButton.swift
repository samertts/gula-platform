import SwiftUI

enum GulaButtonStyle {
    case primary
    case secondary
    case outline
    case ghost
    case danger

    var backgroundColor: Color {
        switch self {
        case .primary: return .gulaPrimary
        case .secondary: return .gulaSurfaceSecondary
        case .outline: return .clear
        case .ghost: return .clear
        case .danger: return .gulaError
        }
    }

    var foregroundColor: Color {
        switch self {
        case .primary: return .white
        case .secondary: return .gulaTextPrimary
        case .outline: return .gulaPrimary
        case .ghost: return .gulaPrimary
        case .danger: return .white
        }
    }

    var borderColor: Color {
        switch self {
        case .outline: return .gulaPrimary
        case .danger: return .gulaError
        default: return .clear
        }
    }
}

struct GulaButton: View {
    let title: String
    let style: GulaButtonStyle
    let icon: Image?
    let isFullWidth: Bool
    let isLoading: Bool
    let isDisabled: Bool
    let action: () -> Void

    @Environment(\.locale) var locale
    @Environment(\.isEnabled) var isEnvironmentEnabled

    init(
        title: String,
        style: GulaButtonStyle = .primary,
        icon: Image? = nil,
        isFullWidth: Bool = true,
        isLoading: Bool = false,
        isDisabled: Bool = false,
        action: @escaping () -> Void
    ) {
        self.title = title
        self.style = style
        self.icon = icon
        self.isFullWidth = isFullWidth
        self.isLoading = isLoading
        self.isDisabled = isDisabled
        self.action = action
    }

    var body: some View {
        Button(action: {
            guard !isLoading else { return }
            action()
        }) {
            HStack(spacing: DesignTokens.Spacing.sm) {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: style.foregroundColor))
                        .scaleEffect(0.8)
                }

                if !locale.isArabic && let icon = icon, !isLoading {
                    icon
                        .imageScale(.medium)
                }

                Text(title)
                    .gulaLabelLarge()
                    .fontWeight(.semibold)

                if locale.isArabic && let icon = icon, !isLoading {
                    icon
                        .imageScale(.medium)
                }
            }
            .frame(maxWidth: isFullWidth ? .infinity : nil)
            .padding(.horizontal, DesignTokens.Spacing.lg)
            .padding(.vertical, DesignTokens.Spacing.md)
            .background(style.backgroundColor)
            .foregroundColor(style.foregroundColor)
            .cornerRadius(DesignTokens.Radius.md)
            .overlay(
                RoundedRectangle(cornerRadius: DesignTokens.Radius.md)
                    .stroke(style.borderColor, lineWidth: style == .outline ? 1.5 : 0)
            )
            .opacity((isDisabled || isLoading) ? 0.5 : 1)
        }
        .disabled(isDisabled || isLoading)
        .buttonStyle(PlainButtonStyle())
    }
}

struct GulaButton_Previews: PreviewProvider {
    static var previews: some View {
        VStack(spacing: 16) {
            GulaButton(title: "primary_button".localized, style: .primary) {}
            GulaButton(title: "secondary_button".localized, style: .secondary) {}
            GulaButton(title: "outline_button".localized, style: .outline) {}
            GulaButton(title: "ghost_button".localized, style: .ghost) {}
            GulaButton(title: "danger_button".localized, style: .danger) {}
            GulaButton(title: "loading_button".localized, isLoading: true) {}
            GulaButton(title: "disabled_button".localized, isDisabled: true) {}
        }
        .padding()
    }
}
