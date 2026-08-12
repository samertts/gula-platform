import SwiftUI
import CoreImage.CIFilterBuiltins

struct QRCodeView: View {
    let string: String
    let size: CGFloat

    @State private var qrImage: UIImage?

    init(string: String, size: CGFloat = 200) {
        self.string = string
        self.size = size
    }

    var body: some View {
        Group {
            if let image = qrImage {
                Image(uiImage: image)
                    .resizable()
                    .interpolation(.none)
                    .scaledToFit()
                    .frame(width: size, height: size)
            } else {
                Rectangle()
                    .fill(Color.gulaSurfaceSecondary)
                    .frame(width: size, height: size)
                    .overlay(
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle())
                    )
                    .onAppear {
                        generateQRCode()
                    }
            }
        }
    }

    private func generateQRCode() {
        guard let data = string.data(using: .utf8) else { return }

        let context = CIContext()
        let filter = CIFilter.qrCodeGenerator()
        filter.setValue(data, forKey: "inputMessage")
        filter.setValue("H", forKey: "inputCorrectionLevel")

        guard let outputImage = filter.outputImage else { return }

        let scale = size / outputImage.extent.size.width
        let scaledImage = outputImage.transformed(by: CGAffineTransform(scaleX: scale, y: scale))

        guard let cgImage = context.createCGImage(scaledImage, from: scaledImage.extent) else { return }

        DispatchQueue.main.async {
            qrImage = UIImage(cgImage: cgImage)
        }
    }
}

struct PatientCardQRView: View {
    let patientId: Int
    let patientName: String
    @Environment(\.locale) var locale

    var body: some View {
        VStack(spacing: DesignTokens.Spacing.md) {
            QRCodeView(string: "gula://patient/\(patientId)", size: 180)

            Text(patientName)
                .gulaBodyLarge()
                .fontWeight(.semibold)
                .foregroundColor(.gulaTextPrimary)

            Text("scan_qr_info".localized)
                .gulaBodySmall()
                .foregroundColor(.gulaTextSecondary)
                .multilineTextAlignment(.center)
        }
        .padding(DesignTokens.Spacing.lg)
        .background(Color.gulaSurfacePrimary)
        .cornerRadius(DesignTokens.Radius.lg)
        .shadow(color: Color.black.opacity(0.1), radius: 8, x: 0, y: 4)
    }
}
