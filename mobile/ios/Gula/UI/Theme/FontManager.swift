import SwiftUI
import UIKit

class FontManager {
    static let shared = FontManager()

    private let arabicFonts = [
        "NotoKufiArabic-Regular",
        "NotoKufiArabic-Bold",
        "NotoKufiArabic-Medium",
        "NotoKufiArabic-SemiBold",
        "NotoKufiArabic-Light"
    ]

    private let latinFonts = [
        "Inter-Regular",
        "Inter-Bold",
        "Inter-Medium",
        "Inter-SemiBold",
        "Inter-Light"
    ]

    private init() {
        registerFonts()
    }

    private func registerFonts() {
        let allFonts = arabicFonts + latinFonts
        for fontName in allFonts {
            registerFont(named: fontName)
        }
    }

    private func registerFont(named name: String) {
        guard let fontURL = Bundle.main.url(forResource: name, withExtension: "ttf") ?? Bundle.main.url(forResource: name, withExtension: "otf") else {
            return
        }
        guard let fontDataProvider = CGDataProvider(url: fontURL as CFURL),
              let font = CGFont(fontDataProvider) else {
            return
        }

        var error: Unmanaged<CFError>?
        CTFontManagerRegisterGraphicsFont(font, &error)
    }

    func fontName(for style: GulaFontStyle, isArabic: Bool) -> String {
        let weight = style.weight
        if isArabic {
            switch weight {
            case .bold, .heavy, .black: return "NotoKufiArabic-Bold"
            case .semibold: return "NotoKufiArabic-SemiBold"
            case .medium: return "NotoKufiArabic-Medium"
            case .light, .ultraLight, .thin: return "NotoKufiArabic-Light"
            default: return "NotoKufiArabic-Regular"
            }
        } else {
            switch weight {
            case .bold, .heavy, .black: return "Inter-Bold"
            case .semibold: return "Inter-SemiBold"
            case .medium: return "Inter-Medium"
            case .light, .ultraLight, .thin: return "Inter-Light"
            default: return "Inter-Regular"
            }
        }
    }

    func scaledFontSize(for style: GulaFontStyle, sizeCategory: ContentSizeCategory) -> CGFloat {
        let baseSize = style.size
        let multiplier: CGFloat
        switch sizeCategory {
        case .extraSmall: multiplier = 0.8
        case .small: multiplier = 0.9
        case .medium: multiplier = 1.0
        case .large: multiplier = 1.1
        case .extraLarge: multiplier = 1.2
        case .extraExtraLarge: multiplier = 1.3
        case .extraExtraExtraLarge: multiplier = 1.4
        case .accessibilityMedium: multiplier = 1.5
        case .accessibilityLarge: multiplier = 1.7
        case .accessibilityExtraLarge: multiplier = 1.9
        case .accessibilityExtraExtraLarge: multiplier = 2.1
        case .accessibilityExtraExtraExtraLarge: multiplier = 2.3
        default: multiplier = 1.0
        }
        return baseSize * multiplier
    }

    static func registerCustomFonts() {
        _ = FontManager.shared
    }
}

struct ScaledFont: ViewModifier {
    @Environment(\.sizeCategory) var sizeCategory
    let style: GulaFontStyle
    let isArabic: Bool

    func body(content: Content) -> some View {
        let fontManager = FontManager.shared
        let fontName = fontManager.fontName(for: style, isArabic: isArabic)
        let size = fontManager.scaledFontSize(for: style, sizeCategory: sizeCategory)

        return content
            .font(.custom(fontName, size: size))
    }
}

extension View {
    func scaledFont(style: GulaFontStyle, isArabic: Bool = false) -> some View {
        modifier(ScaledFont(style: style, isArabic: isArabic))
    }
}
