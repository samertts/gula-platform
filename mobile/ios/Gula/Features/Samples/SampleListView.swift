import SwiftUI

struct SampleListView: View {
    @StateObject private var viewModel = SamplesViewModel()
    @State private var showScanner = false
    @State private var showCreate = false
    @State private var scannedCode: String?
    @Environment(\.locale) var locale

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                statusFilterBar

                if viewModel.isLoading && viewModel.samples.isEmpty {
                    GulaPageLoadingView()
                } else if viewModel.samples.isEmpty {
                    GulaEmptyState(
                        title: "no_samples".localized,
                        message: "no_samples_message".localized,
                        imageName: "testtube.2",
                        actionTitle: "scan_barcode".localized
                    ) {
                        showScanner = true
                    }
                } else {
                    List {
                        ForEach(viewModel.samples, id: \.id) { sample in
                            NavigationLink(destination: SampleDetailView(sample: sample)) {
                                SampleRow(sample: sample)
                            }
                        }
                    }
                    .gulaListStyle()
                }
            }
            .gulaPullToRefresh(isRefreshing: viewModel.isLoading) {
                Task { await viewModel.refresh() }
            }
            .navigationTitle("samples".localized)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: DesignTokens.Spacing.sm) {
                        Button(action: { showScanner = true }) {
                            Image(systemName: "qrcode.viewfinder")
                        }
                        Button(action: { showCreate = true }) {
                            Image(systemName: "plus")
                        }
                    }
                }
            }
            .sheet(isPresented: $showScanner) {
                BarcodeScannerView(onCapture: { barcode in
                    scannedCode = barcode
                    Task {
                        do {
                            let response = try await SampleRepository.shared.lookupRemoteByBarcode(barcode: barcode)
                            await MainActor.run { viewModel.scannedBarcode = barcode }
                        } catch {
                            await MainActor.run { viewModel.error = error.localizedDescription }
                        }
                    }
                    showScanner = false
                }, onDismiss: { showScanner = false })
            }
            .sheet(isPresented: $showCreate) {
                SampleCollectionView { Task { await viewModel.refresh() } }
            }
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }

    private var statusFilterBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: DesignTokens.Spacing.sm) {
                ForEach(viewModel.sampleStatuses, id: \.self) { status in
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

    private func statusDisplayName(_ status: String) -> String {
        switch status {
        case "all": return "all".localized
        case "collected": return "status_collected".localized
        case "received": return "status_received".localized
        case "processing": return "status_processing".localized
        case "analyzed": return "status_analyzed".localized
        case "rejected": return "status_rejected".localized
        default: return status.capitalized
        }
    }
}
