import Foundation

extension String {
    var localized: String {
        NSLocalizedString(self, tableName: "Localizable", bundle: .main, value: self, comment: "")
    }

    func localized(with arguments: CVarArg...) -> String {
        String(format: self.localized, arguments: arguments)
    }

    func localized(forLanguage language: String) -> String {
        guard let path = Bundle.main.path(forResource: language, ofType: "lproj"),
              let bundle = Bundle(path: path) else {
            return self
        }
        return NSLocalizedString(self, tableName: "Localizable", bundle: bundle, value: self, comment: "")
    }
}

extension Locale {
    static var isArabic: Bool {
        current.identifier.hasPrefix("ar")
    }

    var isArabic: Bool {
        identifier.hasPrefix("ar")
    }
}
