import SwiftUI

extension Color {
    // MARK: - Brand Colors
    static let gulaPrimary = DesignTokens.Colors.primary
    static let gulaPrimaryLight = DesignTokens.Colors.primaryLight
    static let gulaPrimaryDark = DesignTokens.Colors.primaryDark

    static let gulaSecondary = DesignTokens.Colors.secondary
    static let gulaSecondaryLight = DesignTokens.Colors.secondaryLight
    static let gulaSecondaryDark = DesignTokens.Colors.secondaryDark

    static let gulaAccent = DesignTokens.Colors.accent
    static let gulaAccentLight = DesignTokens.Colors.accentLight
    static let gulaAccentDark = DesignTokens.Colors.accentDark

    // MARK: - Semantic Colors
    static let gulaSuccess = DesignTokens.Colors.success
    static let gulaWarning = DesignTokens.Colors.warning
    static let gulaError = DesignTokens.Colors.error
    static let gulaInfo = DesignTokens.Colors.info
    static let gulaCritical = DesignTokens.Colors.critical

    // MARK: - Surface Colors
    static let gulaSurfacePrimary = DesignTokens.Colors.surfacePrimary
    static let gulaSurfaceSecondary = DesignTokens.Colors.surfaceSecondary
    static let gulaSurfaceTertiary = DesignTokens.Colors.surfaceTertiary

    // MARK: - Text Colors
    static let gulaTextPrimary = DesignTokens.Colors.textPrimary
    static let gulaTextSecondary = DesignTokens.Colors.textSecondary
    static let gulaTextTertiary = DesignTokens.Colors.textTertiary
    static let gulaTextInverse = DesignTokens.Colors.textInverse

    // MARK: - Border & Divider
    static let gulaBorder = DesignTokens.Colors.border
    static let gulaDivider = DesignTokens.Colors.divider

    // MARK: - Status Badge Colors
    static func statusColor(for status: String) -> Color {
        switch status.lowercased() {
        case "active", "completed", "verified", "approved", "collected":
            return .gulaSuccess
        case "pending", "processing", "received":
            return .gulaInfo
        case "cancelled", "rejected", "failed":
            return .gulaError
        case "critical":
            return .gulaCritical
        case "warning", "abnormal":
            return .gulaWarning
        default:
            return .gulaTextSecondary
        }
    }

    // MARK: - Priority Colors
    static func priorityColor(for priority: String) -> Color {
        switch priority.lowercased() {
        case "stat", "high", "urgent":
            return .gulaCritical
        case "medium":
            return .gulaWarning
        default:
            return .gulaSuccess
        }
    }
}

extension UIColor {
    static let gulaPrimary = UIColor(red: 0.149, green: 0.604, blue: 0.412, alpha: 1)
    static let gulaSecondary = UIColor(red: 0.553, green: 0.729, blue: 0.941, alpha: 1)
    static let gulaAccent = UIColor(red: 1.0, green: 0.584, blue: 0.0, alpha: 1)
    static let gulaCritical = UIColor(red: 0.918, green: 0.157, blue: 0.157, alpha: 1)
    static let gulaSuccess = UIColor(red: 0.200, green: 0.737, blue: 0.357, alpha: 1)
    static let gulaWarning = UIColor(red: 1.0, green: 0.757, blue: 0.027, alpha: 1)
    static let gulaError = UIColor(red: 0.918, green: 0.235, blue: 0.188, alpha: 1)
}
