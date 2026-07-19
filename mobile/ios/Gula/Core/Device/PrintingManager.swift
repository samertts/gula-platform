import UIKit
import PDFKit

enum PrinterType {
    case airPrint
    case bluetooth
    case network
}

class PrintingManager: NSObject, ObservableObject {
    static let shared = PrintingManager()

    @Published var isPrinting = false
    @Published var printError: String?
    @Published var availablePrinters: [UIPrinter] = []

    override private init() {
        super.init()
    }

    func printPDF(data: Data, jobName: String = "GulaReport") {
        guard UIPrintInteractionController.isPrintingAvailable else {
            printError = "printing_not_available".localized
            return
        }

        isPrinting = true

        let printController = UIPrintInteractionController.shared
        let printInfo = UIPrintInfo(dictionary: nil)
        printInfo.jobName = jobName
        printInfo.outputType = .general
        printInfo.duplex = .longEdge
        printController.printInfo = printInfo
        printController.printingItem = data
        printController.showsNumberOfCopies = true
        printController.showsPaperSelectionForLoadedPapers = true

        printController.present(animated: true) { [weak self] _, completed, error in
            DispatchQueue.main.async {
                self?.isPrinting = false
                if let error = error {
                    self?.printError = error.localizedDescription
                }
            }
        }
    }

    func printBarcode(data: Data, jobName: String = "GulaBarcode") {
        guard UIPrintInteractionController.isPrintingAvailable else {
            printError = "printing_not_available".localized
            return
        }

        isPrinting = true

        let printController = UIPrintInteractionController.shared
        let printInfo = UIPrintInfo(dictionary: nil)
        printInfo.jobName = jobName
        printInfo.outputType = .general
        printController.printInfo = printInfo
        printController.printingItem = data

        printController.present(animated: true) { [weak self] _, completed, error in
            DispatchQueue.main.async {
                self?.isPrinting = false
                if let error = error {
                    self?.printError = error.localizedDescription
                }
            }
        }
    }

    func printLabel(text: String, patientName: String, barcode: String) -> Data? {
        let renderer = UIGraphicsImageRenderer(size: CGSize(width: 300, height: 150))
        let image = renderer.image { ctx in
            let rect = CGRect(x: 0, y: 0, width: 300, height: 150)
            UIColor.white.setFill()
            ctx.fill(rect)

            let paragraphStyle = NSMutableParagraphStyle()
            paragraphStyle.alignment = .center

            let attributes: [NSAttributedString.Key: Any] = [
                .font: UIFont.boldSystemFont(ofSize: 14),
                .paragraphStyle: paragraphStyle,
                .foregroundColor: UIColor.black
            ]

            let nameRect = CGRect(x: 10, y: 10, width: 280, height: 30)
            patientName.draw(in: nameRect, withAttributes: attributes)

            let textAttributes: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: 10),
                .paragraphStyle: paragraphStyle,
                .foregroundColor: UIColor.darkGray
            ]
            let textRect = CGRect(x: 10, y: 45, width: 280, height: 20)
            text.draw(in: textRect, withAttributes: textAttributes)

            let barcodeAttributes: [NSAttributedString.Key: Any] = [
                .font: UIFont(name: "C39HRS48DMT", size: 24) ?? UIFont.monospacedSystemFont(ofSize: 24, weight: .bold),
                .paragraphStyle: paragraphStyle,
                .foregroundColor: UIColor.black
            ]
            let barcodeRect = CGRect(x: 10, y: 75, width: 280, height: 40)
            barcode.draw(in: barcodeRect, withAttributes: barcodeAttributes)

            let smallAttrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: 8),
                .paragraphStyle: paragraphStyle,
                .foregroundColor: UIColor.gray
            ]
            let idRect = CGRect(x: 10, y: 120, width: 280, height: 20)
            barcode.draw(in: idRect, withAttributes: smallAttrs)
        }

        return image.pngData()
    }

    func generatePDFReport(html: String) -> Data? {
        let formatter = UIMarkupTextPrintFormatter(markupText: html)
        let renderer = UIPrintPageRenderer()
        renderer.addPrintFormatter(formatter, startingAtPageAt: 0)

        let pageSize = CGRect(x: 0, y: 0, width: 595.2, height: 841.8)
        renderer.setValue(pageSize, forKey: "paperRect")
        renderer.setValue(pageSize, forKey: "printableRect")

        let data = NSMutableData()
        UIGraphicsBeginPDFContextToData(data, pageSize, nil)

        for page in 0..<renderer.numberOfPages {
            UIGraphicsBeginPDFPage()
            renderer.drawPage(at: page, in: pageSize)
        }

        UIGraphicsEndPDFContext()
        return data as Data
    }
}
