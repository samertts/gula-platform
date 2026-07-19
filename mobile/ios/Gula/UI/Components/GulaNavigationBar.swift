import SwiftUI

struct GulaNavigationBar<Leading: View, Trailing: View>: View {
    let title: String
    let subtitle: String?
    let leading: Leading
    let trailing: Trailing

    @Environment(\.locale) var locale

    init(
        title: String,
        subtitle: String? = nil,
        @ViewBuilder leading: () -> Leading,
        @ViewBuilder trailing: () -> Trailing
    ) {
        self.title = title
        self.subtitle = subtitle
        self.leading = leading()
        self.trailing = trailing()
    }

    var body: some View {
        HStack {
            leading
                .frame(width: 44)

            Spacer()

            VStack(spacing: 2) {
                Text(title)
                    .gulaTitleMedium()
                    .foregroundColor(.gulaTextPrimary)
                    .lineLimit(1)

                if let subtitle = subtitle {
                    Text(subtitle)
                        .gulaLabelSmall()
                        .foregroundColor(.gulaTextSecondary)
                }
            }

            Spacer()

            trailing
                .frame(width: 44)
        }
        .padding(.horizontal, DesignTokens.Spacing.md)
        .padding(.vertical, DesignTokens.Spacing.sm)
        .background(Color.gulaSurfacePrimary)
    }
}

extension GulaNavigationBar where Leading == EmptyView, Trailing == EmptyView {
    init(title: String, subtitle: String? = nil) {
        self.init(title: title, subtitle: subtitle, leading: { EmptyView() }, trailing: { EmptyView() })
    }
}

extension GulaNavigationBar where Leading == EmptyView {
    init(title: String, subtitle: String? = nil, @ViewBuilder trailing: () -> Trailing) {
        self.init(title: title, subtitle: subtitle, leading: { EmptyView() }, trailing: trailing)
    }
}

extension GulaNavigationBar where Trailing == EmptyView {
    init(title: String, subtitle: String? = nil, @ViewBuilder leading: () -> Leading) {
        self.init(title: title, subtitle: subtitle, leading: leading, trailing: { EmptyView() })
    }
}

struct GulaBackButton: View {
    @Environment(\.dismiss) var dismiss
    @Environment(\.locale) var locale

    var body: some View {
        Button(action: { dismiss() }) {
            Image(systemName: locale.isArabic ? "chevron.right" : "chevron.left")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.gulaPrimary)
                .frame(width: 44, height: 44)
        }
    }
}
