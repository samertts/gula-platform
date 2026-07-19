import SwiftUI

struct DashboardView: View {
    @StateObject private var viewModel = DashboardViewModel()
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var networkMonitor: NetworkMonitor
    @Environment(\.locale) var locale

    private let columns = [
        GridItem(.flexible()),
        GridItem(.flexible())
    ]

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: DesignTokens.Spacing.md) {
                    headerSection

                    if !viewModel.criticalResults.isEmpty {
                        criticalAlertsSection
                    }

                    LazyVGrid(columns: columns, spacing: DesignTokens.Spacing.md) {
                        DashboardKPI(
                            title: "patients".localized,
                            value: "\(viewModel.patientCount)",
                            icon: "person.2",
                            color: .gulaPrimary
                        )
                        DashboardKPI(
                            title: "orders_today".localized,
                            value: "\(viewModel.ordersToday)",
                            icon: "list.clipboard",
                            color: .gulaInfo
                        )
                        DashboardKPI(
                            title: "pending_results".localized,
                            value: "\(viewModel.pendingResults)",
                            icon: "doc.text.magnifyingglass",
                            color: .gulaWarning
                        )
                        DashboardKPI(
                            title: "critical_alerts".localized,
                            value: "\(viewModel.criticalAlerts)",
                            icon: "exclamationmark.triangle.fill",
                            color: .gulaCritical
                        )
                        DashboardKPI(
                            title: "samples_today".localized,
                            value: "\(viewModel.samplesToday)",
                            icon: "testtube.2",
                            color: .gulaSecondary
                        )
                    }
                    .padding(.horizontal, DesignTokens.Spacing.md)

                    quickActionsSection

                    if !viewModel.recentOrders.isEmpty {
                        recentOrdersSection
                    }

                    if !viewModel.pendingSamples.isEmpty {
                        pendingSamplesSection
                    }
                }
                .padding(.vertical)
            }
            .gulaListStyle()
            .gulaPullToRefresh(isRefreshing: viewModel.isLoading) {
                Task { await viewModel.refresh() }
            }
            .navigationTitle("dashboard".localized)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: DesignTokens.Spacing.sm) {
                        if !networkMonitor.isConnected {
                            Image(systemName: "wifi.slash")
                                .foregroundColor(.gulaWarning)
                        }
                        NavigationLink(destination: GlobalSearchView()) {
                            Image(systemName: "magnifyingglass")
                        }
                    }
                }
            }
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }

    private var headerSection: some View {
        VStack(spacing: 4) {
            Text("welcome_back".localized + ", \(authManager.currentUser?.name ?? "")")
                .gulaHeadlineSmall()
                .foregroundColor(.gulaTextPrimary)

            Text(Date().formatted(date: .complete, time: .omitted))
                .gulaBodySmall()
                .foregroundColor(.gulaTextSecondary)
        }
        .padding(.vertical)
        .frame(maxWidth: .infinity)
    }

    private var criticalAlertsSection: some View {
        VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.gulaCritical)
                Text("critical_alerts".localized)
                    .gulaTitleSmall()
                    .fontWeight(.bold)
                Spacer()
                GulaBadge(.count(viewModel.criticalResults.count), size: .small)
            }
            .padding(.horizontal, DesignTokens.Spacing.md)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: DesignTokens.Spacing.sm) {
                    ForEach(viewModel.criticalResults.prefix(5), id: \.id) { result in
                        CriticalValueBanner(result: result)
                            .frame(width: 280)
                    }
                }
                .padding(.horizontal, DesignTokens.Spacing.md)
            }
        }
    }

    private var quickActionsSection: some View {
        VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
            Text("quick_actions".localized)
                .gulaTitleSmall()
                .fontWeight(.bold)
                .padding(.horizontal, DesignTokens.Spacing.md)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: DesignTokens.Spacing.md) {
                    DashboardQuickAction(title: "new_patient".localized, icon: "person.badge.plus", color: .gulaPrimary) {}
                    DashboardQuickAction(title: "new_order".localized, icon: "plus.doc", color: .gulaInfo) {}
                    DashboardQuickAction(title: "scan_barcode".localized, icon: "qrcode.viewfinder", color: .gulaAccent) {}
                    DashboardQuickAction(title: "new_sample".localized, icon: "testtube.2", color: .gulaSecondary) {}
                    DashboardQuickAction(title: "enter_result".localized, icon: "pencil.and.list.clipboard", color: .gulaWarning) {}
                }
                .padding(.horizontal, DesignTokens.Spacing.md)
            }
        }
    }

    private var recentOrdersSection: some View {
        VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
            Text("recent_orders".localized)
                .gulaTitleSmall()
                .fontWeight(.bold)
                .padding(.horizontal, DesignTokens.Spacing.md)

            ForEach(viewModel.recentOrders, id: \.id) { order in
                OrderRow(order: order)
                if order.id != viewModel.recentOrders.last?.id {
                    Divider().padding(.leading, DesignTokens.Spacing.md)
                }
            }
        }
        .padding(.vertical, DesignTokens.Spacing.sm)
        .background(Color.gulaSurfacePrimary)
        .cornerRadius(DesignTokens.Radius.lg)
        .padding(.horizontal, DesignTokens.Spacing.md)
    }

    private var pendingSamplesSection: some View {
        VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
            Text("pending_samples".localized)
                .gulaTitleSmall()
                .fontWeight(.bold)
                .padding(.horizontal, DesignTokens.Spacing.md)

            ForEach(viewModel.pendingSamples, id: \.id) { sample in
                SampleRow(sample: sample)
                if sample.id != viewModel.pendingSamples.last?.id {
                    Divider().padding(.leading, DesignTokens.Spacing.md)
                }
            }
        }
        .padding(.vertical, DesignTokens.Spacing.sm)
        .background(Color.gulaSurfacePrimary)
        .cornerRadius(DesignTokens.Radius.lg)
        .padding(.horizontal, DesignTokens.Spacing.md)
    }
}
