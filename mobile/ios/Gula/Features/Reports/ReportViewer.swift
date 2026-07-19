import SwiftUI
import PDFKit

struct ReportViewer: View {
    let data: Data
    let title: String
    @Environment(\.dismiss) var dismiss
    @Environment(\.locale) var locale

    var body: some View {
        VStack(spacing: 0) {
            PDFToolbar(
                title: title,
                onShare: { sharePDF() },
                onPrint: { printPDF() },
                onDismiss: { dismiss() }
            )

            PDFViewer(data: data)
        }
        .edgesIgnoringSafeArea(.bottom)
    }

    private func sharePDF() {
        let activityVC = UIActivityViewController(activityItems: [data], applicationActivities: nil)
        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
           let root = windowScene.windows.first?.rootViewController {
            root.present(activityVC, animated: true)
        }
    }

    private func printPDF() {
        PrintingManager.shared.printPDF(data: data, jobName: title)
    }
}
