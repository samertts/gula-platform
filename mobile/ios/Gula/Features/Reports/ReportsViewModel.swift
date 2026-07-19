import Foundation
import Combine

struct ReportItem: Identifiable, Decodable {
    let id: Int
    let name: String
    let url: String
}

class ReportsViewModel: ObservableObject {
    @Published var reports: [ReportItem] = []
    @Published var isLoading = false
    @Published var error: String?
    @Published var selectedReport: ReportItem?
    @Published var reportData: Data?
    @Published var showReportViewer = false

    private var cancellables = Set<AnyCancellable>()

    func refresh() async {
        await MainActor.run { isLoading = true; error = nil }
        do {
            let response: ReportListResponse = try await APIClient.shared.request(
                .listReports(page: 1, limit: 50)
            )
            await MainActor.run {
                reports = response.items
                isLoading = false
            }
        } catch {
            await MainActor.run { self.error = error.localizedDescription; isLoading = false }
        }
    }

    func downloadReport(_ report: ReportItem) async {
        await MainActor.run { isLoading = true }
        do {
            let data = try await APIClient.shared.download(url: report.url)
            await MainActor.run {
                reportData = data
                selectedReport = report
                showReportViewer = true
                isLoading = false
            }
        } catch {
            await MainActor.run { self.error = error.localizedDescription; isLoading = false }
        }
    }

    func generateReport(orderId: Int) async -> String? {
        do {
            let response: ReportURLResponse = try await APIClient.shared.request(
                .generateReport(id: orderId)
            )
            return response.reportUrl
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
            return nil
        }
    }
}

struct ReportListResponse: Decodable {
    let items: [ReportItem]
    let pagination: PaginationMetaResponse
}
