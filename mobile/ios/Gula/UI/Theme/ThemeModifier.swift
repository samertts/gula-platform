import SwiftUI

struct ThemeModifier: ViewModifier {
    @EnvironmentObject var themeManager: ThemeManager

    func body(content: Content) -> some View {
        content
            .preferredColorScheme(themeManager.colorScheme)
            .environment(\.layoutDirection, themeManager.layoutDirection)
            .environment(\.locale, Locale(identifier: themeManager.language.rawValue))
    }
}

struct GulaBackgroundModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(Color.gulaSurfacePrimary)
    }
}

struct GulaListModifier: ViewModifier {
    func body(content: Content) -> some View {
        if #available(iOS 16.0, *) {
            content
                .scrollContentBackground(.hidden)
                .background(Color.gulaSurfacePrimary)
        } else {
            content
                .background(Color.gulaSurfacePrimary)
        }
    }
}

struct GulaNavigationModifier: ViewModifier {
    let title: String
    let displayMode: NavigationBarItem.TitleDisplayMode

    func body(content: Content) -> some View {
        content
            .navigationTitle(title)
            .navigationBarTitleDisplayMode(displayMode)
    }
}

extension View {
    func applyTheme() -> some View {
        modifier(ThemeModifier())
    }

    func gulaBackground() -> some View {
        modifier(GulaBackgroundModifier())
    }

    func gulaListStyle() -> some View {
        modifier(GulaListModifier())
    }

    func gulaNavigation(title: String, displayMode: NavigationBarItem.TitleDisplayMode = .inline) -> some View {
        modifier(GulaNavigationModifier(title: title, displayMode: displayMode))
    }

    func gulaSectionHeader(_ title: String) -> some View {
        Text(title)
            .gulaLabelMedium()
            .foregroundColor(.gulaTextSecondary)
            .textCase(.uppercase)
            .padding(.horizontal, DesignTokens.Spacing.md)
            .padding(.top, DesignTokens.Spacing.lg)
            .padding(.bottom, DesignTokens.Spacing.xs)
    }

    func gulaEmptyState(title: String, message: String, imageName: String? = nil) -> some View {
        modifier(EmptyStateModifier(title: title, message: message, imageName: imageName))
    }
}

struct EmptyStateModifier: ViewModifier {
    let title: String
    let message: String
    let imageName: String?

    func body(content: Content) -> some View {
        content
            .overlay(
                GulaEmptyState(title: title, message: message, imageName: imageName)
            )
    }
}
