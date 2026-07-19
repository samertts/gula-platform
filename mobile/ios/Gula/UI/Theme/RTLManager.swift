import SwiftUI

class RTLManager: ObservableObject {
    static let shared = RTLManager()

    @Published var isRTL: Bool = false

    private init() {
        isRTL = Locale.current.identifier.hasPrefix("ar")
        if let savedLang = UserDefaults.standard.string(forKey: "app_language") {
            isRTL = savedLang == "ar"
        }
    }

    var layoutDirection: LayoutDirection {
        isRTL ? .rightToLeft : .leftToRight
    }

    var locale: Locale {
        Locale(identifier: isRTL ? "ar_IQ" : "en_US")
    }

    func setArabic(_ enabled: Bool) {
        isRTL = enabled
        UserDefaults.standard.set(enabled ? "ar" : "en", forKey: "app_language")
        UIView.appearance().semanticContentAttribute = enabled ? .forceRightToLeft : .forceLeftToRight
    }

    func toggle() {
        setArabic(!isRTL)
    }

    var horizontalEdge: Edge.Set {
        isRTL ? .trailing : .leading
    }

    var oppositeEdge: Edge.Set {
        isRTL ? .leading : .trailing
    }

    func alignment(_ alignment: Alignment) -> Alignment {
        isRTL ? alignment.flippedRTL : alignment
    }
}

extension Alignment {
    var flippedRTL: Alignment {
        switch self {
        case .leading: return .trailing
        case .trailing: return .leading
        case .topLeading: return .topTrailing
        case .topTrailing: return .topLeading
        case .bottomLeading: return .bottomTrailing
        case .bottomTrailing: return .bottomLeading
        default: return self
        }
    }
}

struct RTLReader<Content: View>: View {
    @Environment(\.locale) var locale
    let content: (Bool) -> Content

    init(@ViewBuilder content: @escaping (Bool) -> Content) {
        self.content = content
    }

    var body: some View {
        content(locale.identifier.hasPrefix("ar"))
    }
}

struct RTLStack<Content: View>: View {
    let horizontalAlignment: HorizontalAlignment
    let spacing: CGFloat?
    let content: Content
    @Environment(\.locale) var locale

    init(
        horizontalAlignment: HorizontalAlignment = .center,
        spacing: CGFloat? = nil,
        @ViewBuilder content: () -> Content
    ) {
        self.horizontalAlignment = horizontalAlignment
        self.spacing = spacing
        self.content = content()
    }

    var body: some View {
        let isRTL = locale.identifier.hasPrefix("ar")
        let alignment: HorizontalAlignment = {
            switch horizontalAlignment {
            case .leading: return isRTL ? .trailing : .leading
            case .trailing: return isRTL ? .leading : .trailing
            default: return horizontalAlignment
            }
        }()

        VStack(alignment: alignment, spacing: spacing) {
            content
        }
    }
}
