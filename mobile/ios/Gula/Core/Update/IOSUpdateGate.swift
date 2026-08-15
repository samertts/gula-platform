import SwiftUI

struct IOSUpdatePolicy: Codable, Equatable {
    let platform: String
    let currentVersion: String
    let latestVersion: String
    let minimumSupportedVersion: String
    let updateAvailable: Bool
    let forceUpdate: Bool
    let storeURL: String
    let releaseNotesURL: String
    let message: String
    let messageAr: String

    enum CodingKeys: String, CodingKey {
        case platform
        case currentVersion = "current_version"
        case latestVersion = "latest_version"
        case minimumSupportedVersion = "minimum_supported_version"
        case updateAvailable = "update_available"
        case forceUpdate = "force_update"
        case storeURL = "store_url"
        case releaseNotesURL = "release_notes_url"
        case message
        case messageAr = "message_ar"
    }
}

private struct IOSUpdateManifest: Codable {
    let policies: [String: IOSUpdatePolicy]
}

enum IOSVersionComparator {
    static func isLess(_ current: String, than target: String) -> Bool {
        let currentParts = coreParts(current)
        let targetParts = coreParts(target)
        return currentParts.lexicographicallyPrecedes(targetParts)
    }

    private static func coreParts(_ value: String) -> [Int] {
        let core = value.split(separator: "-", maxSplits: 1).first.map(String.init) ?? value
        var parts = core.split(separator: ".", omittingEmptySubsequences: false).prefix(3).map { Int($0) ?? 0 }
        while parts.count < 3 { parts.append(0) }
        return Array(parts)
    }
}

@MainActor
final class IOSUpdateChecker: ObservableObject {
    @Published private(set) var policy: IOSUpdatePolicy?

    private let session: URLSession
    private let endpoint: URL

    init(
        session: URLSession = .shared,
        endpoint: URL = URL(string: "https://api.gula-platform.org/app-updates")!
    ) {
        self.session = session
        self.endpoint = endpoint
    }

    func check(currentVersion: String) async {
        var components = URLComponents(url: endpoint, resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "platform", value: "ios"),
            URLQueryItem(name: "version", value: currentVersion),
        ]
        guard let url = components?.url else { return }

        do {
            var request = URLRequest(url: url)
            request.httpMethod = "GET"
            request.cachePolicy = .reloadIgnoringLocalCacheData
            request.timeoutInterval = 8
            request.setValue("GULA-iOS-UpdateGate/1.0", forHTTPHeaderField: "User-Agent")

            let (data, response) = try await session.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse,
                  (200..<300).contains(httpResponse.statusCode) else {
                return
            }
            let manifest = try JSONDecoder().decode(IOSUpdateManifest.self, from: data)
            policy = manifest.policies["ios"]
        } catch {
            // Metadata must never turn a transient network problem into a clinical outage.
            policy = nil
        }
    }

    func requiresUpdate(currentVersion: String) -> Bool {
        guard let policy else { return false }
        return policy.forceUpdate || IOSVersionComparator.isLess(currentVersion, than: policy.minimumSupportedVersion)
    }
}

struct IOSUpdateGate<Content: View>: View {
    @StateObject private var checker = IOSUpdateChecker()
    @Environment(\.openURL) private var openURL
    @State private var optionalUpdateDismissed = false

    private let content: Content
    private let currentVersion: String

    init(
        currentVersion: String = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0.0.0",
        @ViewBuilder content: () -> Content
    ) {
        self.currentVersion = currentVersion
        self.content = content()
    }

    var body: some View {
        ZStack {
            content
                .disabled(checker.requiresUpdate(currentVersion: currentVersion))

            if checker.requiresUpdate(currentVersion: currentVersion), let policy = checker.policy {
                IOSForcedUpdateView(policy: policy, openURL: openURL)
            } else if !optionalUpdateDismissed,
                      let policy = checker.policy,
                      policy.updateAvailable {
                VStack {
                    IOSOptionalUpdateBanner(
                        policy: policy,
                        openURL: openURL,
                        dismiss: { optionalUpdateDismissed = true }
                    )
                    Spacer()
                }
                .padding(.top, 8)
            }
        }
        .task {
            await checker.check(currentVersion: currentVersion)
        }
    }
}

private struct IOSForcedUpdateView: View {
    let policy: IOSUpdatePolicy
    let openURL: OpenURLAction

    var body: some View {
        ZStack {
            Color(.systemBackground).ignoresSafeArea()
            VStack(spacing: 20) {
                Image(systemName: "arrow.down.app.fill")
                    .font(.system(size: 54))
                    .foregroundStyle(Color.gulaPrimary)
                Text("تحديث مطلوب")
                    .font(.title2.weight(.bold))
                Text(policy.messageAr)
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.secondary)
                Text("الإصدار الحالي: \(policy.currentVersion)\nالإصدار المطلوب: \(policy.minimumSupportedVersion)")
                    .multilineTextAlignment(.center)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Button("فتح صفحة التحديث") {
                    guard let url = URL(string: policy.storeURL) else { return }
                    openURL(url)
                }
                .buttonStyle(.borderedProminent)
            }
            .padding(32)
            .accessibilityIdentifier("ios-forced-update")
        }
    }
}

private struct IOSOptionalUpdateBanner: View {
    let policy: IOSUpdatePolicy
    let openURL: OpenURLAction
    let dismiss: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 3) {
                Text("يتوفر تحديث جديد: \(policy.latestVersion)")
                    .font(.subheadline.weight(.semibold))
                Text(policy.messageAr)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer(minLength: 8)
            Button("تحديث") {
                guard let url = URL(string: policy.storeURL) else { return }
                openURL(url)
            }
            .buttonStyle(.borderedProminent)
            Button("لاحقًا", action: dismiss)
                .buttonStyle(.borderless)
        }
        .padding(14)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
        .padding(.horizontal, 12)
        .accessibilityIdentifier("ios-optional-update")
    }
}
