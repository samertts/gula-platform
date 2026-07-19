import Foundation
import CommonCrypto

class CertificatePinner: NSObject, URLSessionDelegate {
    private let pinnedKeys: Set<String> = [
        "sha256/9n0v4qTpT9G6r7cC8dE3fHgIjKlMnO2pQrStUvWxYzA=",
        "sha256/0pQrStUvWxYzA1bCdEfGhIjKlMnO2pQrStUvWxYzA1bC=",
        "sha256/D3fHgIjKlMnO2pQrStUvWxYzA1bCdEfGhIjKlMnO2pQrS="
    ]

    private let pinnedDomains: Set<String> = [
        "api.gula.iq",
        "analytics.gula.iq"
    ]

    func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let serverTrust = challenge.protectionSpace.serverTrust,
              let host = challenge.protectionSpace.host.addingPercentEncoding(withAllowedCharacters: .urlHostAllowed),
              pinnedDomains.contains(where: { host.contains($0) || $0.contains(host) }) else {
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

        guard let serverCertificate = SecTrustGetCertificateAtIndex(serverTrust, 0) else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        let serverPublicKey = SecCertificateCopyKey(serverCertificate)
        guard let publicKey = serverPublicKey else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        guard let publicKeyData = SecKeyCopyExternalRepresentation(publicKey, nil) as Data? else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        let keyHash = sha256(data: publicKeyData)
        let base64Hash = keyHash.base64EncodedString()
        let pin = "sha256/\(base64Hash)"

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
