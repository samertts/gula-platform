import SwiftUI
import PDFKit

struct PDFViewer: UIViewRepresentable {
    let data: Data?
    let url: URL?
    let autoScale: Bool

    init(data: Data, autoScale: Bool = true) {
        self.data = data
        self.url = nil
        self.autoScale = autoScale
    }

    init(url: URL, autoScale: Bool = true) {
        self.data = nil
        self.url = url
        self.autoScale = autoScale
    }

    func makeUIView(context: Context) -> PDFView {
        let pdfView = PDFView()
        pdfView.autoScales = autoScale
        pdfView.displayMode = .singlePageContinuous
        pdfView.displayDirection = .vertical
        pdfView.pageBreakMargins = UIEdgeInsets(top: 8, left: 8, bottom: 8, right: 8)
        pdfView.backgroundColor = UIColor.systemGray6

        if let url = url {
            pdfView.document = PDFDocument(url: url)
        } else if let data = data {
            pdfView.document = PDFDocument(data: data)
        }

        return pdfView
    }

    func updateUIView(_ uiView: PDFView, context: Context) {
        if let url = url {
            uiView.document = PDFDocument(url: url)
        } else if let data = data {
            uiView.document = PDFDocument(data: data)
        }
    }
}

struct PDFToolbar: View {
    let title: String
    let onShare: (() -> Void)?
    let onPrint: (() -> Void)?
    let onDismiss: (() -> Void)?
    @Environment(\.locale) var locale

    var body: some View {
        HStack {
            if let onDismiss = onDismiss {
                Button(action: onDismiss) {
                    HStack(spacing: 4) {
                        Image(systemName: locale.isArabic ? "chevron.right" : "chevron.left")
                        Text("back".localized)
                            .gulaLabelMedium()
                    }
                }
            }

            Spacer()

            Text(title)
                .gulaTitleSmall()
                .foregroundColor(.gulaTextPrimary)

            Spacer()

            HStack(spacing: DesignTokens.Spacing.sm) {
                if let onShare = onShare {
                    Button(action: onShare) {
                        Image(systemName: "square.and.arrow.up")
                    }
                }
                if let onPrint = onPrint {
                    Button(action: onPrint) {
                        Image(systemName: "printer")
                    }
                }
            }
            .foregroundColor(.gulaPrimary)
        }
        .padding(.horizontal, DesignTokens.Spacing.md)
        .padding(.vertical, DesignTokens.Spacing.sm)
        .background(Color.gulaSurfacePrimary)
    }
}
