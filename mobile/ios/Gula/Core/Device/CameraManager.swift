import AVFoundation
import UIKit

enum CameraError: LocalizedError {
    case notAuthorized
    case notAvailable
    case configurationFailed
    case captureFailed

    var errorDescription: String? {
        switch self {
        case .notAuthorized: return "camera_not_authorized".localized
        case .notAvailable: return "camera_not_available".localized
        case .configurationFailed: return "camera_config_failed".localized
        case .captureFailed: return "camera_capture_failed".localized
        }
    }
}

class CameraManager: NSObject, ObservableObject {
    let captureSession = AVCaptureSession()
    @Published var isAuthorized = false
    @Published var isRunning = false
    @Published var error: CameraError?

    private let sessionQueue = DispatchQueue(label: "com.gula.camera.session", qos: .userInitiated)

    override init() {
        super.init()
        checkAuthorization()
    }

    func checkAuthorization() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            isAuthorized = true
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async {
                    self?.isAuthorized = granted
                    if granted {
                        self?.setupCamera()
                    }
                }
            }
        default:
            isAuthorized = false
            error = .notAuthorized
        }
    }

    func setupCamera() {
        sessionQueue.async { [weak self] in
            guard let self = self else { return }
            self.captureSession.beginConfiguration()

            guard let videoDevice = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) ?? AVCaptureDevice.default(for: .video) else {
                DispatchQueue.main.async { self.error = .notAvailable }
                self.captureSession.commitConfiguration()
                return
            }

            guard let videoInput = try? AVCaptureDeviceInput(device: videoDevice) else {
                DispatchQueue.main.async { self.error = .configurationFailed }
                self.captureSession.commitConfiguration()
                return
            }

            if self.captureSession.canAddInput(videoInput) {
                self.captureSession.addInput(videoInput)
            } else {
                DispatchQueue.main.async { self.error = .configurationFailed }
                self.captureSession.commitConfiguration()
                return
            }

            let metadataOutput = AVCaptureMetadataOutput()
            if self.captureSession.canAddOutput(metadataOutput) {
                self.captureSession.addOutput(metadataOutput)
                metadataOutput.setMetadataObjectsDelegate(self, queue: DispatchQueue.main)
                metadataOutput.metadataObjectTypes = [.qr, .code128, .code39, .code93, .ean13, .ean8, .pdf417, .aztec]
            }

            self.captureSession.commitConfiguration()
        }
    }

    func startSession() {
        guard isAuthorized else { return }
        sessionQueue.async { [weak self] in
            self?.captureSession.startRunning()
            DispatchQueue.main.async { self?.isRunning = true }
        }
    }

    func stopSession() {
        sessionQueue.async { [weak self] in
            self?.captureSession.stopRunning()
            DispatchQueue.main.async { self?.isRunning = false }
        }
    }

    func capturePhoto(completion: @escaping (UIImage?) -> Void) {
        guard isRunning else {
            completion(nil)
            return
        }
    }
}

extension CameraManager: AVCaptureMetadataOutputObjectsDelegate {
    func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput metadataObjects: [AVMetadataObject], from connection: AVCaptureConnection) {
        for metadata in metadataObjects {
            if let readableObject = metadata as? AVMetadataMachineReadableCodeObject,
               let stringValue = readableObject.stringValue {
                NotificationCenter.default.post(
                    name: .barcodeScanned,
                    object: nil,
                    userInfo: ["barcode": stringValue, "type": readableObject.type.rawValue]
                )
                stopSession()
                break
            }
        }
    }
}

extension Notification.Name {
    static let barcodeScanned = Notification.Name("barcodeScanned")
}
