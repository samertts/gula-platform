import SwiftUI

struct GulaTextField: View {
    let title: String
    @Binding var text: String
    let placeholder: String
    let error: String?
    let isSecure: Bool
    let keyboardType: UIKeyboardType
    let textContentType: UITextContentType?
    let autocapitalization: TextInputAutocapitalization
    let submitLabel: SubmitLabel
    let onSubmit: (() -> Void)?

    @Environment(\.locale) var locale
    @FocusState private var isFocused: Bool

    init(
        title: String,
        text: Binding<String>,
        placeholder: String = "",
        error: String? = nil,
        isSecure: Bool = false,
        keyboardType: UIKeyboardType = .default,
        textContentType: UITextContentType? = nil,
        autocapitalization: TextInputAutocapitalization = .never,
        submitLabel: SubmitLabel = .done,
        onSubmit: (() -> Void)? = nil
    ) {
        self.title = title
        self._text = text
        self.placeholder = placeholder
        self.error = error
        self.isSecure = isSecure
        self.keyboardType = keyboardType
        self.textContentType = textContentType
        self.autocapitalization = autocapitalization
        self.submitLabel = submitLabel
        self.onSubmit = onSubmit
    }

    var body: some View {
        VStack(alignment: .leading, spacing: DesignTokens.Spacing.xxs) {
            Text(title)
                .gulaLabelMedium()
                .foregroundColor(.gulaTextSecondary)

            Group {
                if isSecure {
                    SecureField(placeholder, text: $text)
                        .textContentType(textContentType)
                } else {
                    TextField(placeholder, text: $text)
                        .textInputAutocapitalization(autocapitalization)
                        .keyboardType(keyboardType)
                        .textContentType(textContentType)
                }
            }
            .gulaBodyLarge()
            .padding(.horizontal, DesignTokens.Spacing.md)
            .padding(.vertical, DesignTokens.Spacing.sm)
            .background(
                RoundedRectangle(cornerRadius: DesignTokens.Radius.sm)
                    .stroke(error != nil ? Color.gulaError : (isFocused ? Color.gulaPrimary : Color.gulaBorder), lineWidth: error != nil ? 1.5 : 1)
            )
            .background(Color.gulaSurfacePrimary)
            .cornerRadius(DesignTokens.Radius.sm)
            .focused($isFocused)
            .submitLabel(submitLabel)
            .onSubmit { onSubmit?() }

            if let error = error {
                Text(error)
                    .gulaLabelSmall()
                    .foregroundColor(.gulaError)
                    .transition(.opacity)
            }
        }
    }
}

struct GulaSearchField: View {
    @Binding var text: String
    let placeholder: String

    var body: some View {
        HStack(spacing: DesignTokens.Spacing.xs) {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.gulaTextTertiary)
            TextField(placeholder, text: $text)
                .gulaBodyMedium()
            if !text.isEmpty {
                Button(action: { text = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.gulaTextTertiary)
                }
            }
        }
        .padding(DesignTokens.Spacing.sm)
        .background(Color.gulaSurfaceSecondary)
        .cornerRadius(DesignTokens.Radius.md)
    }
}
