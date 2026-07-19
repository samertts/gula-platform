import SwiftUI

struct ReportListView: View {
    @StateObject private var viewModel = ReportsViewModel()
    @Environment(\.locale) var locale

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                if viewModel.isLoading && viewModel.reports.isEmpty {
                    GulaPageLoadingView()
                } else if viewModel.reports.isEmpty {
                    GulaEmptyState(
                        title: "no_reports".localized,
                        message: "no_reports_message".localized,
                        imageName: "doc.richtext"
                    )
                } else {
                    List {
                        ForEach(viewModel.reports) { report in
                            Button(action: {
                                Task { await viewModel.downloadReport(report) }
                            }) {
                                HStack(spacing: DesignTokens.Spacing.md) {
                                    Image(systemName: "doc.richtext")
                                        .font(.title2)
                                        .foregroundColor(.gulaPrimary)

                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(report.name)
                                            .gulaBodyMedium()
                                            .fontWeight(.semibold)
                                            .foregroundColor(.gulaTextPrimary)
                                    }

                                    Spacer()

                                    Image(systemName: "chevron.right")
                                        .foregroundColor(.gulaTextTertiary)
                                }
                                .padding(.vertical, 4)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                    .gulaListStyle()
                }
            }
            .gulaPullToRefresh(isRefreshing: viewModel.isLoading) {
                Task { await viewModel.refresh() }
            }
            .navigationTitle("reports".localized)
            .task { await viewModel.refresh() }
            .fullScreenCover(isPresented: $viewModel.showReportViewer) {
                if let data = viewModel.reportData, let report = viewModel.selectedReport {
                    NavigationView {
                        PDFViewer(data: data)
                            .navigationTitle(report.name)
                            .toolbar {
                                ToolbarItem(placement: .confirmationAction) {
                                    Button("done".localized) { viewModel.showReportViewer = false }
                                }
                                ToolbarItem(placement: .navigationBarTrailing) {
                                    HStack {
                                        Button(action: {
                                            PrintingManager.shared.printPDF(data: data)
                                        }) {
                                            Image(systemName: "printer")
                                        }
                                        Button(action: {
                                            let activityVC = UIActivityViewController(activityItems: [data], applicationActivities: nil)
                                            if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                                               let root = windowScene.windows.first?.rootViewController {
                                                root.present(activityVC, animated: true)
                                            }
                                        }) {
                                            Image(systemName: "square.and.arrow.up")
                                        }
                                    }
                                }
                            }
                    }
                }
            }
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }
}
