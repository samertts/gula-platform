import SwiftUI

struct ResultListView: View {
    @StateObject private var viewModel = ResultsViewModel()
    @State private var showEntryView = false
    @State private var showValidationView = false
    @Environment(\.locale) var locale

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                filterBar

                if !viewModel.criticalResults.isEmpty && !viewModel.showCriticalOnly {
                    criticalBanner
                }

                if viewModel.isLoading && viewModel.results.isEmpty {
                    GulaPageLoadingView()
                } else if viewModel.results.isEmpty {
                    GulaEmptyState(
                        title: "no_results".localized,
                        message: "no_results_message".localized,
                        imageName: "doc.text.magnifyingglass"
                    )
                } else {
                    List {
                        ForEach(viewModel.showCriticalOnly ? viewModel.criticalResults : viewModel.results, id: \.id) { result in
                            NavigationLink(destination: ResultDetailView(result: result)) {
                                ResultRow(result: result)
                            }
                        }
                    }
                    .gulaListStyle()
                }
            }
            .gulaPullToRefresh(isRefreshing: viewModel.isLoading) {
                Task { await viewModel.refresh() }
            }
            .navigationTitle("results".localized)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: DesignTokens.Spacing.sm) {
                        if viewModel.showCriticalOnly {
                            Button("show_all".localized) { viewModel.toggleCriticalFilter() }
                                .gulaLabelSmall()
                        } else {
                            Button(action: { viewModel.toggleCriticalFilter() }) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .foregroundColor(.gulaCritical)
                            }
                        }
                        Button(action: { showEntryView = true }) {
                            Image(systemName: "plus")
                        }
                        Button(action: { showValidationView = true }) {
                            Image(systemName: "checkmark.seal")
                        }
                    }
                }
            }
            .sheet(isPresented: $showEntryView) {
                ResultEntryView { Task { await viewModel.refresh() } }
            }
            .sheet(isPresented: $showValidationView) {
                ResultValidationView { Task { await viewModel.refresh() } }
            }
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }

    private var filterBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: DesignTokens.Spacing.sm) {
                ForEach(viewModel.resultStatuses, id: \.self) { status in
                    Button(action: { viewModel.filterByStatus(status == "all" ? nil : status) }) {
                        Text(statusDisplayName(status))
                            .gulaLabelMedium()
                            .padding(.horizontal, DesignTokens.Spacing.md)
                            .padding(.vertical, DesignTokens.Spacing.xs)
                            .background(
                                (viewModel.selectedStatus == status || (status == "all" && viewModel.selectedStatus == nil))
                                ? Color.gulaPrimary : Color.gulaSurfaceSecondary
                            )
                            .foregroundColor(
                                (viewModel.selectedStatus == status || (status == "all" && viewModel.selectedStatus == nil))
                                ? .white : .gulaTextPrimary
                            )
                            .cornerRadius(DesignTokens.Radius.full)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(.horizontal, DesignTokens.Spacing.md)
            .padding(.vertical, DesignTokens.Spacing.sm)
        }
        .background(Color.gulaSurfacePrimary)
    }

    private var criticalBanner: some View {
        Button(action: { viewModel.toggleCriticalFilter() }) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                Text(String(format: "critical_results_banner".localized, viewModel.criticalResults.count))
                    .gulaLabelMedium()
                Spacer()
                Image(systemName: "chevron.right")
            }
            .foregroundColor(.white)
            .padding(DesignTokens.Spacing.md)
            .background(Color.gulaCritical)
        }
        .buttonStyle(PlainButtonStyle())
    }

    private func statusDisplayName(_ status: String) -> String {
        switch status {
        case "all": return "all".localized
        case "pending": return "status_pending".localized
        case "completed": return "status_completed".localized
        case "verified": return "status_verified".localized
        case "rejected": return "status_rejected".localized
        default: return status.capitalized
        }
    }
}
