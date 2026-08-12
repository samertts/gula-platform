import Foundation
import CommonCrypto

final class CertificatePinner: NSObject, URLSessionDelegate {
    // SPKI pin observed for api.gula-platform.org on 2026-08-12.
    // Add a verified backup pin before rotating the production certificate.
    private let pinnedKeys: Set<String> = [
        "sha256/g9F05XEMwoJmxPy/otHWQ4jyLsg5jcPWyh4PYBrOEM0="
    ]

    private let pinnedDomains: Set<String> = [
        "api.gula-platform.org"
    ]

    func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let serverTrust = challenge.protectionSpace.serverTrust,
              let host = challenge.protectionSpace.host.lowercased().addingPercentEncoding(withAllowedCharacters: .urlHostAllowed),
              pinnedDomains.contains(host) else {
            completionHandler(.performDefaultHandling, nil)
            return
        }

        var secresult = SecTrustResultType.invalid
        guard SecTrustEvaluate(serverTrust, &secresult) == errSecSuccess else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        guard secresult == .unspecified || secresult == .proceed else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        guard let serverCertificate = SecTrustGetCertificateAtIndex(serverTrust, 0),
              let publicKey = SecCertificateCopyKey(serverCertificate),
              let publicKeyData = SecKeyCopyExternalRepresentation(publicKey, nil) as Data? else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        let keyHash = sha256(data: publicKeyData)
        let pin = "sha256/\(keyHash.base64EncodedString())"

        if pinnedKeys.contains(pin) {
            completionHandler(.useCredential, URLCredential(trust: serverTrust))
        } else {
            completionHandler(.cancelAuthenticationChallenge, nil)
        }
    }

    private func sha256(data: Data) -> Data {
        var hash = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        data.withUnsafeBytes { buffer in
            _ = CC_SHA256(buffer.baseAddress, CC_LONG(data.count), &hash)
        }
        return Data(hash)
    }
}
