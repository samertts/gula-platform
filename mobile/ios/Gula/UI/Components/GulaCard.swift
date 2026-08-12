import SwiftUI

enum GulaCardStyle {
    case elevated
    case outlined
    case filled
}

struct GulaCard<Content: View>: View {
    let style: GulaCardStyle
    let header: (() -> AnyView)?
    let content: Content
    let footer: (() -> AnyView)?

    init(
        style: GulaCardStyle = .elevated,
        @ViewBuilder content: () -> Content
    ) {
        self.style = style
        self.content = content()
        self.header = nil
        self.footer = nil
    }

    init<Header: View, Footer: View>(
        style: GulaCardStyle = .elevated,
        @ViewBuilder content: () -> Content,
        @ViewBuilder header: () -> Header,
        @ViewBuilder footer: () -> Footer
    ) {
        self.style = style
        self.content = content()
        self.header = { AnyView(header()) }
        self.footer = { AnyView(footer()) }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            if let header = header {
                header()
                    .padding(.horizontal, DesignTokens.Spacing.md)
                    .padding(.vertical, DesignTokens.Spacing.sm)
                    .background(cardBackground)
            }

            content
                .padding(DesignTokens.Spacing.md)

            if let footer = footer {
                Divider()
                footer()
                    .padding(.horizontal, DesignTokens.Spacing.md)
                    .padding(.vertical, DesignTokens.Spacing.sm)
                    .background(cardBackground)
            }
        }
        .background(cardBackground)
        .cornerRadius(DesignTokens.Radius.lg)
        .overlay(
            RoundedRectangle(cornerRadius: DesignTokens.Radius.lg)
                .stroke(style == .outlined ? Color.gulaBorder : Color.clear, lineWidth: 1)
        )
        .shadow(
            color: style == .elevated ? Color.black.opacity(0.08) : .clear,
            radius: style == .elevated ? 8 : 0,
            x: 0,
            y: style == .elevated ? 4 : 0
        )
    }

    private var cardBackground: Color {
        switch style {
        case .elevated, .outlined: return Color.gulaSurfacePrimary
        case .filled: return Color.gulaSurfaceSecondary
        }
    }
}
