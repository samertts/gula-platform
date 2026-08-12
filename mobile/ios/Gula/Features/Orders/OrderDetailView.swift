import SwiftUI

struct OrderDetailView: View {
    let order: OrderEntity
    @State private var isLoading = false
    @State private var error: String?
    @State private var showCancelAlert = false
    @Environment(\.locale) var locale

    var body: some View {
        ScrollView {
            VStack(spacing: DesignTokens.Spacing.md) {
                orderHeader

                GulaCard(style: .outlined) {
                    VStack(spacing: DesignTokens.Spacing.md) {
                        detailRow(label: "status".localized, value: statusDisplayName(order.status))
                        Divider()
                        detailRow(label: "patient_id".localized, value: "#\(order.patientId)")
                        if let doctorName = order.doctorName {
                            Divider()
                            detailRow(label: "doctor".localized, value: doctorName)
                        }
                        if let createdAt = order.createdAt {
                            Divider()
                            detailRow(label: "created_at".localized, value: createdAt.formatted(date: .abbreviated, time: .shortened))
                        }
                        if let updatedAt = order.updatedAt {
                            Divider()
                            detailRow(label: "updated_at".localized, value: updatedAt.formatted(date: .abbreviated, time: .shortened))
                        }
                        if let priority = order.priority {
                            Divider()
                            detailRow(label: "priority".localized, value: priorityDisplayName(priority))
                        }
                    }
                }

                if let results = order.results, !results.isEmpty {
                    GulaCard(style: .outlined) {
                        VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
                            Text("results".localized)
                                .gulaTitleSmall()
                                .fontWeight(.bold)

                            ForEach(Array(results), id: \.id) { result in
                                ResultRow(result: result as! ResultEntity)
                                if result != results.last {
                                    Divider()
                                }
                            }
                        }
                    }
                }

                if order.status != "cancelled" && order.status != "completed" {
                    GulaButton(title: "cancel_order".localized, style: .danger) {
                        showCancelAlert = true
                    }
                }
            }
            .padding()
        }
        .gulaBackground()
        .navigationTitle("order_id_prefix".localized + " #\(order.id)")
        .alert("cancel_order_confirm".localized, isPresented: $showCancelAlert) {
            Button("cancel".localized, role: .cancel) {}
            Button("confirm_cancel".localized, role: .destructive) {
                Task {
                    do {
                        try await OrderRepository.shared.cancelOrder(id: Int(order.id))
                    } catch {
                        await MainActor.run { self.error = error.localizedDescription }
                    }
                }
            }
        } message: {
            Text("cancel_order_message".localized)
        }
    }

    private var orderHeader: some View {
        VStack(spacing: DesignTokens.Spacing.sm) {
            Image(systemName: "list.clipboard")
                .font(.system(size: 48))
                .foregroundColor(.gulaPrimary)

            Text("order_id_prefix".localized + " #\(order.id)")
                .gulaTitleLarge()
                .foregroundColor(.gulaTextPrimary)

            GulaBadge(.status(order.status), size: .medium)
        }
        .frame(maxWidth: .infinity)
        .padding()
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
        }
    }

    private func statusDisplayName(_ status: String) -> String {
        switch status.lowercased() {
        case "pending": return "status_pending".localized
        case "processing": return "status_processing".localized
        case "completed": return "status_completed".localized
        case "cancelled": return "status_cancelled".localized
        default: return status.capitalized
        }
    }

    private func priorityDisplayName(_ priority: String) -> String {
        switch priority.lowercased() {
        case "urgent": return "priority_urgent".localized
        case "stat": return "priority_stat".localized
        case "high": return "priority_high".localized
        default: return priority
        }
    }
}
