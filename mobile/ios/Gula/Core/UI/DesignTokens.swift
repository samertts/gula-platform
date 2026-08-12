import Foundation
import SwiftUI

enum DesignTokens {
    // MARK: - Colors
    enum Colors {
        static let primary = Color(red: 0.149, green: 0.604, blue: 0.412)
        static let primaryLight = Color(red: 0.208, green: 0.733, blue: 0.510)
        static let primaryDark = Color(red: 0.098, green: 0.475, blue: 0.318)

        static let secondary = Color(red: 0.553, green: 0.729, blue: 0.941)
        static let secondaryLight = Color(red: 0.690, green: 0.831, blue: 0.973)
        static let secondaryDark = Color(red: 0.416, green: 0.627, blue: 0.910)

        static let accent = Color(red: 1.0, green: 0.584, blue: 0.0)
        static let accentLight = Color(red: 1.0, green: 0.702, blue: 0.200)
        static let accentDark = Color(red: 0.871, green: 0.467, blue: 0.0)

        static let success = Color(red: 0.200, green: 0.737, blue: 0.357)
        static let warning = Color(red: 1.0, green: 0.757, blue: 0.027)
        static let error = Color(red: 0.918, green: 0.235, blue: 0.188)
        static let info = Color(red: 0.239, green: 0.549, blue: 0.996)

        static let critical = Color(red: 0.918, green: 0.157, blue: 0.157)

        static let surfacePrimary = Color(.systemBackground)
        static let surfaceSecondary = Color(.secondarySystemBackground)
        static let surfaceTertiary = Color(.tertiarySystemBackground)

        static let textPrimary = Color(.label)
        static let textSecondary = Color(.secondaryLabel)
        static let textTertiary = Color(.tertiaryLabel)
        static let textInverse = Color(.systemBackground)

        static let border = Color(.separator)
        static let divider = Color(.opaqueSeparator)

        static let shadow = Color.black.opacity(0.1)
    }

    // MARK: - Typography
    enum Typography {
        enum Arabic {
            static let bodyFont = "NotoKufiArabic"
            static let titleFont = "NotoKufiArabic"
            static let displayFont = "NotoKufiArabic"
        }

        enum Latin {
            static let bodyFont = "Inter"
            static let titleFont = "Inter"
            static let displayFont = "Inter"
        }

        static let sizes = FontSizes()
    }

    struct FontSizes {
        let displayLarge: CGFloat = 34
        let displayMedium: CGFloat = 28
        let displaySmall: CGFloat = 22
        let headlineLarge: CGFloat = 20
        let headlineMedium: CGFloat = 18
        let headlineSmall: CGFloat = 16
        let titleLarge: CGFloat = 22
        let titleMedium: CGFloat = 16
        let titleSmall: CGFloat = 14
        let bodyLarge: CGFloat = 17
        let bodyMedium: CGFloat = 15
        let bodySmall: CGFloat = 13
        let labelLarge: CGFloat = 14
        let labelMedium: CGFloat = 12
        let labelSmall: CGFloat = 11
    }

    // MARK: - Spacing (4px scale)
    enum Spacing {
        static let xxxs: CGFloat = 2
        static let xxs: CGFloat = 4
        static let xs: CGFloat = 8
        static let sm: CGFloat = 12
        static let md: CGFloat = 16
        static let lg: CGFloat = 20
        static let xl: CGFloat = 24
        static let xxl: CGFloat = 32
        static let xxxl: CGFloat = 40
        static let huge: CGFloat = 48
        static let massive: CGFloat = 64
    }

    // MARK: - Corner Radius
    enum Radius {
        static let none: CGFloat = 0
        static let xs: CGFloat = 4
        static let sm: CGFloat = 8
        static let md: CGFloat = 12
        static let lg: CGFloat = 16
        static let xl: CGFloat = 20
        static let full: CGFloat = 9999
    }

    // MARK: - Shadows
    enum Shadows {
        static let sm = ShadowAttributes(color: Colors.shadow, radius: 2, x: 0, y: 1)
        static let md = ShadowAttributes(color: Colors.shadow, radius: 4, x: 0, y: 2)
        static let lg = ShadowAttributes(color: Colors.shadow, radius: 8, x: 0, y: 4)
        static let xl = ShadowAttributes(color: Colors.shadow, radius: 16, x: 0, y: 8)
    }

    struct ShadowAttributes {
        let color: Color
        let radius: CGFloat
        let x: CGFloat
        let y: CGFloat
    }

    // MARK: - Animation
    enum Animation {
        static let `default` = SwiftUI.Animation.easeInOut(duration: 0.3)
        static let fast = SwiftUI.Animation.easeInOut(duration: 0.15)
        static let slow = SwiftUI.Animation.easeInOut(duration: 0.5)
        static let spring = SwiftUI.Animation.spring(response: 0.4, dampingFraction: 0.7)
    }

    // MARK: - Layout
    enum Layout {
        static let maxContentWidth: CGFloat = 800
        static let minTouchTarget: CGFloat = 44
        static let sidebarWidth: CGFloat = 320
        static let cardMinHeight: CGFloat = 80
    }
}
