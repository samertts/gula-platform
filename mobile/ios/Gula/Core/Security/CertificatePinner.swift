import Foundation
import Security
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
              pinnedDomains.contains(challenge.protectionSpace.host.lowercased()) else {
            completionHandler(.performDefaultHandling, nil)
            return
        }

        var trustResult = SecTrustResultType.invalid
        guard SecTrustEvaluate(serverTrust, &trustResult) == errSecSuccess,
              trustResult == .unspecified || trustResult == .proceed else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        let certificateCount = SecTrustGetCertificateCount(serverTrust)
        for index in 0..<certificateCount {
            guard let certificate = SecTrustGetCertificateAtIndex(serverTrust, index),
                  let spki = subjectPublicKeyInfo(from: SecCertificateCopyData(certificate) as Data) else {
                continue
            }

            let pin = "sha256/\(sha256(data: spki).base64EncodedString())"
            if pinnedKeys.contains(pin) {
                completionHandler(.useCredential, URLCredential(trust: serverTrust))
                return
            }
        }

        completionHandler(.cancelAuthenticationChallenge, nil)
    }

    private func subjectPublicKeyInfo(from certificate: Data) -> Data? {
        var certificateReader = DERReader(certificate)
        guard let certificateSequence = certificateReader.read(tag: 0x30) else { return nil }
        var certificateBody = DERReader(certificateSequence.content)
        guard let tbsCertificate = certificateBody.read(tag: 0x30) else { return nil }
        var tbsBody = DERReader(tbsCertificate.content)

        if tbsBody.peekTag == 0xA0 { _ = tbsBody.read() } // optional version
        guard tbsBody.read(tag: 0x02) != nil, // serialNumber
              tbsBody.read(tag: 0x30) != nil, // signature
              tbsBody.read(tag: 0x30) != nil, // issuer
              tbsBody.read(tag: 0x30) != nil, // validity
              tbsBody.read(tag: 0x30) != nil, // subject
              let subjectPublicKeyInfo = tbsBody.read(tag: 0x30) else {
            return nil
        }
        return subjectPublicKeyInfo.encoded
    }

    private func sha256(data: Data) -> Data {
        var hash = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        data.withUnsafeBytes { buffer in
            _ = CC_SHA256(buffer.baseAddress, CC_LONG(data.count), &hash)
        }
        return Data(hash)
    }

    private struct DERReader {
        struct Element {
            let encoded: Data
            let content: Data
        }

        private let bytes: [UInt8]
        private var offset = 0

        init(_ data: Data) {
            bytes = Array(data)
        }

        var peekTag: UInt8? {
            offset < bytes.count ? bytes[offset] : nil
        }

        mutating func read(tag expectedTag: UInt8? = nil) -> Element? {
            let start = offset
            guard offset < bytes.count else { return nil }
            let tag = bytes[offset]
            if let expectedTag, tag != expectedTag { return nil }
            offset += 1
            guard offset < bytes.count else { return nil }

            let firstLengthByte = bytes[offset]
            offset += 1
            var length = Int(firstLengthByte & 0x7F)
            if firstLengthByte & 0x80 != 0 {
                let lengthByteCount = Int(firstLengthByte & 0x7F)
                guard lengthByteCount > 0, lengthByteCount <= 4,
                      offset + lengthByteCount <= bytes.count else { return nil }
                length = 0
                for _ in 0..<lengthByteCount {
                    length = (length << 8) | Int(bytes[offset])
                    offset += 1
                }
            }

            guard length >= 0, offset + length <= bytes.count else { return nil }
            let contentStart = offset
            offset += length
            return Element(
                encoded: Data(bytes[start..<offset]),
                content: Data(bytes[contentStart..<offset])
            )
        }
    }
}
