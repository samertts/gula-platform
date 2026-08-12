import SwiftUI
import AVFoundation

struct BarcodeScannerView: View {
    let onCapture: (String) -> Void
    let onDismiss: (() -> Void)?

    @State private var isScanning = false
    @State private var showError = false
    @State private var errorMessage = ""
    @Environment(\.locale) var locale

    init(onCapture: @escaping (String) -> Void, onDismiss: (() -> Void)? = nil) {
        self.onCapture = onCapture
        self.onDismiss = onDismiss
    }

    var body: some View {
        ZStack {
            BarcodeScanner(onCapture: { barcode in
                AudioServicesPlaySystemSound(kSystemSoundID_Vibrate)
                onCapture(barcode)
            })
            .ignoresSafeArea()

            VStack {
                HStack {
                    if let onDismiss = onDismiss {
                        Button(action: onDismiss) {
                            Image(systemName: "xmark")
                                .font(.title2)
                                .foregroundColor(.white)
                                .padding()
                                .background(Color.black.opacity(0.5))
                                .clipShape(Circle())
                        }
                    }

                    Spacer()
                }
                .padding()

                Spacer()

                Text("scan_barcode_instructions".localized)
                    .gulaBodyMedium()
                    .foregroundColor(.white)
                    .padding()
                    .background(Color.black.opacity(0.6))
                    .cornerRadius(DesignTokens.Radius.md)
                    .padding(.bottom, 50)
            }
        }
        .alert("error".localized, isPresented: $showError) {
            Button("ok".localized) { showError = false }
        } message: {
            Text(errorMessage)
        }
        .onAppear {
            checkCameraPermission()
        }
    }

    private func checkCameraPermission() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            isScanning = true
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { granted in
                if !granted {
                    errorMessage = "camera_not_authorized".localized
                    showError = true
                }
            }
        case .denied, .restricted:
            errorMessage = "camera_not_authorized".localized
            showError = true
        @unknown default:
            errorMessage = "camera_not_available".localized
            showError = true
        }
    }
}
