import SwiftUI

struct OrderListView: View {
    @StateObject private var viewModel = OrdersViewModel()
    @State private var showCreateOrder = false
    @Environment(\.locale) var locale

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                statusFilterBar

                if viewModel.isLoading && viewModel.orders.isEmpty {
                    GulaPageLoadingView()
                } else if viewModel.orders.isEmpty {
                    GulaEmptyState(
                        title: "no_orders".localized,
                        message: "no_orders_message".localized,
                        imageName: "list.clipboard",
                        actionTitle: "create_order".localized
                    ) {
                        showCreateOrder = true
                    }
                } else {
                    List {
                        ForEach(viewModel.orders, id: \.id) { order in
                            NavigationLink(destination: OrderDetailView(order: order)) {
                                OrderRow(order: order)
                            }
                        }
                        .onDelete { indexSet in
                            if let index = indexSet.first {
                                let order = viewModel.orders[index]
                                Task { await viewModel.cancelOrder(id: Int(order.id)) }
                            }
                        }
                    }
                    .gulaListStyle()
                }
            }
            .gulaPullToRefresh(isRefreshing: viewModel.isLoading) {
                Task { await viewModel.refresh() }
            }
            .navigationTitle("orders".localized)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showCreateOrder = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showCreateOrder) {
                OrderCreateView { Task { await viewModel.refresh() } }
            }
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }

    private var statusFilterBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: DesignTokens.Spacing.sm) {
                ForEach(viewModel.orderStatuses, id: \.self) { status in
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
        case "pending": return "status_pending".localized
        case "processing": return "status_processing".localized
        case "completed": return "status_completed".localized
        case "cancelled": return "status_cancelled".localized
        default: return status.capitalized
        }
    }
}
