import SwiftUI
import AVFoundation

struct BarcodeScanner: UIViewControllerRepresentable {
    var onCapture: (String) -> Void

    func makeUIViewController(context: Context) -> BarcodeScannerController {
        let controller = BarcodeScannerController()
        controller.onCapture = onCapture
        return controller
    }

    func updateUIViewController(_ uiViewController: BarcodeScannerController, context: Context) {}
}

class BarcodeScannerController: UIViewController {
    var captureSession: AVCaptureSession?
    var previewLayer: AVCaptureVideoPreviewLayer?
    var onCapture: ((String) -> Void)?
    private let supportedCodes: [AVMetadataObject.ObjectType] = [
        .qr, .code128, .code39, .code93, .ean13, .ean8, .pdf417, .aztec, .interleaved2of5, .itf14, .upce
    ]

    override func viewDidLoad() {
        super.viewDidLoad()
        setupCamera()
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        previewLayer?.frame = view.layer.bounds
    }

    private func setupCamera() {
        let session = AVCaptureSession()
        guard let videoDevice = AVCaptureDevice.default(for: .video),
              let videoInput = try? AVCaptureDeviceInput(device: videoDevice) else {
            showError("camera_not_available".localized)
            return
        }

        guard session.canAddInput(videoInput) else {
            showError("camera_config_failed".localized)
            return
        }
        session.addInput(videoInput)

        let metadataOutput = AVCaptureMetadataOutput()
        guard session.canAddOutput(metadataOutput) else {
            showError("camera_config_failed".localized)
            return
        }
        session.addOutput(metadataOutput)

        metadataOutput.setMetadataObjectsDelegate(self, queue: .main)
        metadataOutput.metadataObjectTypes = supportedCodes

        let preview = AVCaptureVideoPreviewLayer(session: session)
        preview.frame = view.layer.bounds
        preview.videoGravity = .resizeAspectFill
        view.layer.addSublayer(preview)

        captureSession = session
        previewLayer = preview

        let overlay = createOverlay()
        view.addSubview(overlay)

        let torchButton = UIButton(type: .system)
        torchButton.setImage(UIImage(systemName: "flashlight.off.fill"), for: .normal)
        torchButton.tintColor = .white
        torchButton.backgroundColor = UIColor.black.withAlphaComponent(0.3)
        torchButton.layer.cornerRadius = 22
        torchButton.frame = CGRect(x: view.bounds.midX - 22, y: view.bounds.maxY - 100, width: 44, height: 44)
        torchButton.addTarget(self, action: #selector(toggleTorch), for: .touchUpInside)
        view.addSubview(torchButton)

        DispatchQueue.global(qos: .userInitiated).async {
            session.startRunning()
        }
    }

    private func createOverlay() -> UIView {
        let overlay = UIView(frame: view.bounds)
        overlay.backgroundColor = UIColor.black.withAlphaComponent(0.5)
        overlay.isUserInteractionEnabled = false

        let scanRect = CGRect(
            x: view.bounds.midX - 120,
            y: view.bounds.midY - 120,
            width: 240,
            height: 240
        )

        let path = UIBezierPath(rect: overlay.bounds)
        let cutout = UIBezierPath(roundedRect: scanRect, cornerRadius: 12)
        path.append(cutout)
        path.usesEvenOddFillRule = true

        let maskLayer = CAShapeLayer()
        maskLayer.path = path.cgPath
        maskLayer.fillRule = .evenOdd
        maskLayer.fillColor = UIColor.black.cgColor
        overlay.layer.mask = maskLayer

        let borderLayer = CAShapeLayer()
        borderLayer.path = UIBezierPath(roundedRect: scanRect, cornerRadius: 12).cgPath
        borderLayer.strokeColor = UIColor.gulaPrimary.cgColor
        borderLayer.lineWidth = 3
        borderLayer.fillColor = UIColor.clear.cgColor
        overlay.layer.addSublayer(borderLayer)

        return overlay
    }

    @objc private func toggleTorch() {
        guard let device = AVCaptureDevice.default(for: .video), device.hasTorch else { return }
        try? device.lockForConfiguration()
        device.torchMode = device.torchMode == .on ? .off : .on
        device.unlockForConfiguration()
    }

    private func showError(_ message: String) {
        let label = UILabel()
        label.text = message
        label.textColor = .white
        label.textAlignment = .center
        label.numberOfLines = 0
        label.frame = view.bounds
        view.addSubview(label)
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        captureSession?.stopRunning()
    }
}

extension BarcodeScannerController: AVCaptureMetadataOutputObjectsDelegate {
    func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput metadataObjects: [AVMetadataObject], from connection: AVCaptureConnection) {
        guard let object = metadataObjects.first as? AVMetadataMachineReadableCodeObject,
              let stringValue = object.stringValue else { return }

        AudioServicesPlaySystemSound(SystemSoundID(kSystemSoundID_Vibrate))
        onCapture?(stringValue)
    }
}
