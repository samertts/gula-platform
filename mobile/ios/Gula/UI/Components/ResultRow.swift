import SwiftUI

struct ResultRow: View {
    let result: ResultEntity
    @Environment(\.locale) var locale

    var body: some View {
        VStack(spacing: DesignTokens.Spacing.sm) {
            HStack(spacing: DesignTokens.Spacing.md) {
                VStack(alignment: locale.isArabic ? .trailing : .leading, spacing: 4) {
                    Text(locale.isArabic ? result.testNameAr : result.testNameEn)
                        .gulaBodyMedium()
                        .fontWeight(.semibold)
                        .foregroundColor(.gulaTextPrimary)

                    if let unit = result.unit {
                        HStack(spacing: DesignTokens.Spacing.xxs) {
                            if result.resultValue > 0 {
                                Text("\(result.resultValue, specifier: "%.2f")")
                                    .gulaBodyLarge()
                                    .fontWeight(.bold)
                                    .foregroundColor(result.isCritical ? .gulaCritical : (result.isAbnormal ? .gulaWarning : .gulaTextPrimary))
                            }
                            Text(unit)
                                .gulaLabelSmall()
                                .foregroundColor(.gulaTextSecondary)
                        }
                    }
                }

                Spacer()

                VStack(alignment: .trailing, spacing: 4) {
                    GulaBadge(.status(result.status), size: .small)

                    if result.isCritical {
                        HStack(spacing: 2) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .font(.system(size: 10))
                            Text("critical".localized)
                                .gulaLabelSmall()
                        }
                        .foregroundColor(.gulaCritical)
                    }

                    if result.isAbnormal && !result.isCritical {
                        HStack(spacing: 2) {
                            Image(systemName: "exclamationmark.circle.fill")
                                .font(.system(size: 10))
                            Text("abnormal".localized)
                                .gulaLabelSmall()
                        }
                        .foregroundColor(.gulaWarning)
                    }
                }
            }

            if result.referenceMin > 0 || result.referenceMax > 0 {
                HStack(spacing: DesignTokens.Spacing.xxs) {
                    Image(systemName: "arrow.up.and.down")
                        .font(.system(size: 10))
                        .foregroundColor(.gulaTextTertiary)

                    Text(String(format: "reference_range".localized,
                               result.referenceMin, result.referenceMax))
                        .gulaLabelSmall()
                        .foregroundColor(.gulaTextTertiary)

                    Spacer()
                }
            }
        }
        .padding(.vertical, DesignTokens.Spacing.xs)
        .padding(.horizontal, DesignTokens.Spacing.md)
        .background(result.isCritical ? Color.gulaCritical.opacity(0.05) : Color.clear)
        .cornerRadius(DesignTokens.Radius.sm)
        .contentShape(Rectangle())
    }
}

struct CriticalValueBanner: View {
    let result: ResultEntity
    @Environment(\.locale) var locale

    var body: some View {
        HStack(spacing: DesignTokens.Spacing.sm) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.title2)
                .foregroundColor(.white)

            VStack(alignment: locale.isArabic ? .trailing : .leading, spacing: 2) {
                Text("critical_value".localized)
                    .gulaLabelLarge()
                    .foregroundColor(.white)
                    .fontWeight(.bold)

                Text("\(locale.isArabic ? result.testNameAr : result.testNameEn): \(result.resultValue, specifier: "%.2f") \(result.unit ?? "")")
                    .gulaBodySmall()
                    .foregroundColor(.white.opacity(0.9))
            }

            Spacer()
        }
        .padding(DesignTokens.Spacing.md)
        .background(Color.gulaCritical)
        .cornerRadius(DesignTokens.Radius.md)
    }
}
