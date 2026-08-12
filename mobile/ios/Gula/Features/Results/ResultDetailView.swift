import SwiftUI

struct ResultDetailView: View {
    let result: ResultEntity
    @State private var showAmendSheet = false
    @State private var isLoading = false
    @State private var error: String?
    @Environment(\.locale) var locale

    var body: some View {
        ScrollView {
            VStack(spacing: DesignTokens.Spacing.md) {
                resultHeader

                GulaCard(style: .outlined) {
                    VStack(spacing: DesignTokens.Spacing.md) {
                        detailRow(label: "test_name".localized,
                                  value: locale.isArabic ? result.testNameAr : result.testNameEn)
                        Divider()
                        detailRow(label: "test_code".localized, value: result.testCode)

                        if result.resultValue > 0 {
                            Divider()
                            HStack {
                                Text("value".localized)
                                    .gulaBodyMedium()
                                    .foregroundColor(.gulaTextSecondary)
                                Spacer()
                                Text("\(result.resultValue, specifier: "%.2f")")
                                    .gulaTitleLarge()
                                    .fontWeight(.bold)
                                    .foregroundColor(result.isCritical ? .gulaCritical : (result.isAbnormal ? .gulaWarning : .gulaTextPrimary))
                                if let unit = result.unit {
                                    Text(unit)
                                        .gulaBodyMedium()
                                        .foregroundColor(.gulaTextSecondary)
                                }
                            }
                        }

                        if let resultText = result.resultText {
                            Divider()
                            detailRow(label: "result_text".localized, value: resultText)
                        }

                        if result.referenceMin > 0 || result.referenceMax > 0 {
                            Divider()
                            detailRow(label: "reference_range".localized,
                                      value: "\(result.referenceMin, specifier: "%.1f") - \(result.referenceMax, specifier: "%.1f") \(result.unit ?? "")")
                        }

                        if let category = result.category {
                            Divider()
                            detailRow(label: "category".localized, value: category)
                        }

                        Divider()
                        detailRow(label: "status".localized, value: statusDisplayName(result.status))

                        if result.isCritical {
                            Divider()
                            HStack {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .foregroundColor(.gulaCritical)
                                Text("critical_value_warning".localized)
                                    .gulaBodyMedium()
                                    .foregroundColor(.gulaCritical)
                            }
                        }
                    }
                }

                if let sampleBarcode = result.sampleBarcode, !sampleBarcode.isEmpty {
                    GulaCard(style: .outlined) {
                        detailRow(label: "sample_barcode".localized, value: sampleBarcode)
                    }
                }

                actionButtons
            }
            .padding()
        }
        .gulaBackground()
        .navigationTitle("result_detail".localized)
    }

    private var resultHeader: some View {
        VStack(spacing: DesignTokens.Spacing.sm) {
            Image(systemName: result.isCritical ? "exclamationmark.triangle.fill" : "doc.text.fill")
                .font(.system(size: 48))
                .foregroundColor(result.isCritical ? .gulaCritical : .gulaPrimary)

            Text(locale.isArabic ? result.testNameAr : result.testNameEn)
                .gulaTitleLarge()
                .foregroundColor(.gulaTextPrimary)

            GulaBadge(.status(result.status), size: .medium)
        }
        .frame(maxWidth: .infinity)
        .padding()
    }

    private var actionButtons: some View {
        VStack(spacing: DesignTokens.Spacing.md) {
            if result.status == "completed" || result.status == "pending" {
                GulaButton(title: "verify_result".localized, style: .primary) {
                    Task { await verify() }
                }

                GulaButton(title: "flag_as_critical".localized, style: .outline) {
                    Task { await flagCritical() }
                }
            }

            GulaButton(title: "amend_result".localized, style: .ghost) {
                showAmendSheet = true
            }

            GulaButton(title: "print_result".localized, style: .outline) {
                Task { await printResult() }
            }
        }
    }

    private func detailRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .gulaBodyMedium()
                .foregroundColor(.gulaTextSecondary)
            Spacer()
            Text(value)
                .gulaBodyMedium()
                .fontWeight(.semibold)
                .foregroundColor(.gulaTextPrimary)
                .multilineTextAlignment(.trailing)
        }
    }

    private func verify() async {
        do {
            try await ResultRepository.shared.verifyResult(id: Int(result.id))
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }

    private func flagCritical() async {
        do {
            try await ResultRepository.shared.flagCritical(id: Int(result.id))
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }

    private func printResult() async {
        do {
            let response: ReportURLResponse = try await APIClient.shared.request(.generateReport(id: Int(result.id)))
            if let url = URL(string: response.reportUrl) {
                let data = try await APIClient.shared.download(url: response.reportUrl)
                PrintingManager.shared.printPDF(data: data, jobName: "result-\(result.id)")
            }
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }

    private func statusDisplayName(_ status: String) -> String {
        switch status.lowercased() {
        case "pending": return "status_pending".localized
        case "completed": return "status_completed".localized
        case "verified": return "status_verified".localized
        case "rejected": return "status_rejected".localized
        default: return status.capitalized
        }
    }
}

struct ReportURLResponse: Decodable {
    let reportUrl: String
}
