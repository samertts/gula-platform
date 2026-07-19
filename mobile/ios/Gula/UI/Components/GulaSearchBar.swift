import SwiftUI
import Combine

struct GulaSearchBar: View {
    @Binding var text: String
    let placeholder: String
    let debounceInterval: DispatchQueue.SchedulerTimeType.Stride
    let onSearch: ((String) -> Void)?

    @State private var debouncedText = ""
    @FocusState private var isFocused: Bool
    @Environment(\.locale) var locale

    init(
        text: Binding<String>,
        placeholder: String = "search".localized,
        debounceInterval: DispatchQueue.SchedulerTimeType.Stride = 0.3,
        onSearch: ((String) -> Void)? = nil
    ) {
        self._text = text
        self.placeholder = placeholder
        self.debounceInterval = debounceInterval
        self.onSearch = onSearch
    }

    var body: some View {
        HStack(spacing: DesignTokens.Spacing.xs) {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.gulaTextTertiary)
                .font(.system(size: 16))

            TextField(placeholder, text: $text)
                .gulaBodyMedium()
                .focused($isFocused)
                .submitLabel(.search)
                .onSubmit {
                    onSearch?(text)
                }

            if !text.isEmpty {
                Button(action: {
                    text = ""
                    isFocused = false
                }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.gulaTextTertiary)
                        .font(.system(size: 16))
                }
                .buttonStyle(PlainButtonStyle())
            }

            if !isFocused && text.isEmpty {
                Button(action: { isFocused = true }) {
                    Image(systemName: locale.isArabic ? "arrow.left" : "arrow.right")
                        .foregroundColor(.gulaTextTertiary)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(.horizontal, DesignTokens.Spacing.sm)
        .padding(.vertical, DesignTokens.Spacing.xs)
        .background(Color.gulaSurfaceSecondary)
        .cornerRadius(DesignTokens.Radius.md)
        .onReceive(Just(text).debounce(for: debounceInterval, scheduler: DispatchQueue.main)) { debounced in
            onSearch?(debounced)
        }
    }
}
