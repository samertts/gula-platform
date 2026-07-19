import SwiftUI

struct SampleRow: View {
    let sample: SampleEntity
    @Environment(\.locale) var locale

    var body: some View {
        HStack(spacing: DesignTokens.Spacing.md) {
            Image(systemName: sampleStatusIcon)
                .font(.system(size: 24))
                .foregroundColor(Color.statusColor(for: sample.status))
                .frame(width: 40)

            VStack(alignment: locale.isArabic ? .trailing : .leading, spacing: 4) {
                HStack(spacing: DesignTokens.Spacing.xs) {
                    Text(sample.sampleType)
                        .gulaBodyMedium()
                        .fontWeight(.semibold)
                        .foregroundColor(.gulaTextPrimary)

                    Text("•")
                        .foregroundColor(.gulaTextTertiary)

                    Text(sample.barcode)
                        .gulaLabelSmall()
                        .foregroundColor(.gulaTextTertiary)
                        .font(.system(.caption, design: .monospaced))
                }

                if let collectedAt = sample.collectedAt {
                    Text(collectedAt.formatted(date: .abbreviated, time: .shortened))
                        .gulaLabelSmall()
                        .foregroundColor(.gulaTextSecondary)
                }

                if let location = sample.storageLocation {
                    HStack(spacing: DesignTokens.Spacing.xxs) {
                        Image(systemName: "location.fill")
                            .font(.system(size: 8))
                            .foregroundColor(.gulaTextTertiary)
                        Text(location)
                            .gulaLabelSmall()
                            .foregroundColor(.gulaTextTertiary)
                    }
                }
            }

            Spacer()

            GulaBadge(.status(sample.status), size: .small)
        }
        .padding(.vertical, DesignTokens.Spacing.xs)
        .padding(.horizontal, DesignTokens.Spacing.md)
        .contentShape(Rectangle())
    }

    private var sampleStatusIcon: String {
        switch sample.status.lowercased() {
        case "collected": return "testtube.2"
        case "received": return "shippingbox"
        case "processing": return "gearshape.2"
        case "analyzed": return "checkmark.circle"
        case "rejected": return "xmark.circle"
        default: return "circle"
        }
    }
}
