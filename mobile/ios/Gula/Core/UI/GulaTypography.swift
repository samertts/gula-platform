import SwiftUI

enum GulaFontStyle {
    case displayLarge
    case displayMedium
    case displaySmall
    case headlineLarge
    case headlineMedium
    case headlineSmall
    case titleLarge
    case titleMedium
    case titleSmall
    case bodyLarge
    case bodyMedium
    case bodySmall
    case labelLarge
    case labelMedium
    case labelSmall

    var size: CGFloat {
        switch self {
        case .displayLarge: return DesignTokens.Typography.sizes.displayLarge
        case .displayMedium: return DesignTokens.Typography.sizes.displayMedium
        case .displaySmall: return DesignTokens.Typography.sizes.displaySmall
        case .headlineLarge: return DesignTokens.Typography.sizes.headlineLarge
        case .headlineMedium: return DesignTokens.Typography.sizes.headlineMedium
        case .headlineSmall: return DesignTokens.Typography.sizes.headlineSmall
        case .titleLarge: return DesignTokens.Typography.sizes.titleLarge
        case .titleMedium: return DesignTokens.Typography.sizes.titleMedium
        case .titleSmall: return DesignTokens.Typography.sizes.titleSmall
        case .bodyLarge: return DesignTokens.Typography.sizes.bodyLarge
        case .bodyMedium: return DesignTokens.Typography.sizes.bodyMedium
        case .bodySmall: return DesignTokens.Typography.sizes.bodySmall
        case .labelLarge: return DesignTokens.Typography.sizes.labelLarge
        case .labelMedium: return DesignTokens.Typography.sizes.labelMedium
        case .labelSmall: return DesignTokens.Typography.sizes.labelSmall
        }
    }

    var weight: Font.Weight {
        switch self {
        case .displayLarge, .displayMedium, .displaySmall, .headlineLarge:
            return .bold
        case .headlineMedium, .headlineSmall, .titleLarge:
            return .semibold
        case .titleMedium, .titleSmall:
            return .semibold
        case .bodyLarge, .bodyMedium:
            return .regular
        case .bodySmall:
            return .regular
        case .labelLarge, .labelMedium, .labelSmall:
            return .medium
        }
    }

    var textStyle: Font.TextStyle {
        switch self {
        case .displayLarge: return .largeTitle
        case .displayMedium: return .largeTitle
        case .displaySmall: return .title
        case .headlineLarge: return .title
        case .headlineMedium: return .title2
        case .headlineSmall: return .title3
        case .titleLarge: return .title
        case .titleMedium: return .title2
        case .titleSmall: return .title3
        case .bodyLarge: return .body
        case .bodyMedium: return .body
        case .bodySmall: return .callout
        case .labelLarge: return .headline
        case .labelMedium: return .subheadline
        case .labelSmall: return .caption
        }
    }
}

struct GulaFontModifier: ViewModifier {
    let style: GulaFontStyle
    @Environment(\.sizeCategory) var sizeCategory
    @Environment(\.locale) var locale

    func body(content: Content) -> some View {
        let isArabic = locale.identifier.hasPrefix("ar")
        let fontName = isArabic ? DesignTokens.Typography.Arabic.bodyFont : DesignTokens.Typography.Latin.bodyFont

        return content
            .font(.custom(fontName, size: style.size, relativeTo: style.textStyle))
            .fontWeight(style.weight)
    }
}

extension View {
    func gulaFont(_ style: GulaFontStyle) -> some View {
        modifier(GulaFontModifier(style: style))
    }

    func gulaDisplayLarge() -> some View { gulaFont(.displayLarge) }
    func gulaDisplayMedium() -> some View { gulaFont(.displayMedium) }
    func gulaDisplaySmall() -> some View { gulaFont(.displaySmall) }
    func gulaHeadlineLarge() -> some View { gulaFont(.headlineLarge) }
    func gulaHeadlineMedium() -> some View { gulaFont(.headlineMedium) }
    func gulaHeadlineSmall() -> some View { gulaFont(.headlineSmall) }
    func gulaTitleLarge() -> some View { gulaFont(.titleLarge) }
    func gulaTitleMedium() -> some View { gulaFont(.titleMedium) }
    func gulaTitleSmall() -> some View { gulaFont(.titleSmall) }
    func gulaBodyLarge() -> some View { gulaFont(.bodyLarge) }
    func gulaBodyMedium() -> some View { gulaFont(.bodyMedium) }
    func gulaBodySmall() -> some View { gulaFont(.bodySmall) }
    func gulaLabelLarge() -> some View { gulaFont(.labelLarge) }
    func gulaLabelMedium() -> some View { gulaFont(.labelMedium) }
    func gulaLabelSmall() -> some View { gulaFont(.labelSmall) }
}
