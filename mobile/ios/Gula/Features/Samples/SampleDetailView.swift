import SwiftUI

struct SampleDetailView: View {
    let sample: SampleEntity
    @State private var showRejectDialog = false
    @State private var rejectReason = ""
    @State private var isLoading = false
    @State private var error: String?
    @Environment(\.locale) var locale

    var body: some View {
        ScrollView {
            VStack(spacing: DesignTokens.Spacing.md) {
                sampleHeader

                GulaCard(style: .outlined) {
                    VStack(spacing: DesignTokens.Spacing.md) {
                        detailRow(label: "barcode".localized, value: sample.barcode)
                        Divider()
                        detailRow(label: "sample_type".localized, value: sample.sampleType)
                        Divider()
                        detailRow(label: "status".localized, value: statusDisplayName(sample.status))
                        if let collectedBy = sample.collectedBy {
                            Divider()
                            detailRow(label: "collected_by".localized, value: collectedBy)
                        }
                        if let collectedAt = sample.collectedAt {
                            Divider()
                            detailRow(label: "collected_at".localized, value: collectedAt.formatted(date: .abbreviated, time: .shortened))
                        }
                        if let location = sample.storageLocation {
                            Divider()
                            detailRow(label: "storage_location".localized, value: location)
                        }
                        if let notes = sample.notes {
                            Divider()
                            detailRow(label: "notes".localized, value: notes)
                        }
                        if let reason = sample.rejectionReason {
                            Divider()
                            detailRow(label: "rejection_reason".localized, value: reason)
                                .foregroundColor(.gulaError)
                        }
                    }
                }

                actionButtons
            }
            .padding()
        }
        .gulaBackground()
        .navigationTitle("sample_detail".localized)
        .alert("reject_sample".localized, isPresented: $showRejectDialog) {
            TextField("rejection_reason".localized, text: $rejectReason)
            Button("cancel".localized, role: .cancel) {}
            Button("confirm_reject".localized, role: .destructive) {
                Task { await rejectSample() }
            }
        } message: {
            Text("reject_sample_message".localized)
        }
    }

    private var sampleHeader: some View {
        VStack(spacing: DesignTokens.Spacing.sm) {
            Image(systemName: sampleStatusIcon)
                .font(.system(size: 48))
                .foregroundColor(Color.statusColor(for: sample.status))

            Text(sample.sampleType)
                .gulaTitleLarge()
                .foregroundColor(.gulaTextPrimary)

            GulaBadge(.status(sample.status), size: .medium)

            Text(sample.barcode)
                .gulaBodyMedium()
                .font(.system(.body, design: .monospaced))
                .foregroundColor(.gulaTextSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
    }

    private var actionButtons: some View {
        VStack(spacing: DesignTokens.Spacing.md) {
            if sample.status == "collected" {
                GulaButton(title: "receive_sample".localized, style: .primary) {
                    Task { await receiveSample() }
                }
            }

            if sample.status != "rejected" {
                GulaButton(title: "reject_sample".localized, style: .danger) {
                    showRejectDialog = true
                }
            }

            if sample.status == "analyzed" {
                GulaButton(title: "print_label".localized, style: .outline) {
                    Task { await printLabel() }
                }
            }
        }
    }

    private func receiveSample() async {
        await MainActor.run { isLoading = true }
        do {
            try await SampleRepository.shared.receiveSample(id: Int(sample.id))
            await MainActor.run { isLoading = false }
        } catch {
            await MainActor.run { self.error = error.localizedDescription; isLoading = false }
        }
    }

    private func rejectSample() async {
        guard !rejectReason.isEmpty else { return }
        await MainActor.run { isLoading = true }
        do {
            try await SampleRepository.shared.rejectSample(id: Int(sample.id), reason: rejectReason)
            await MainActor.run { isLoading = false }
        } catch {
            await MainActor.run { self.error = error.localizedDescription; isLoading = false }
        }
    }

    private func printLabel() async {
        do {
            let response: SampleResponseStruct = try await APIClient.shared.request(.getSample(id: Int(sample.id)))
            if let labelData = PrintingManager.shared.printLabel(
                text: "\(sample.sampleType) - \(sample.barcode)",
                patientName: "Patient",
                barcode: sample.barcode
            ) {
                PrintingManager.shared.printBarcode(data: labelData)
            }
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
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
        }
    }

    private var sampleStatusIcon: String {
        switch sample.status.lowercased() {
        case "collected": return "testtube.2"
        case "received": return "shippingbox"
        case "processing": return "gearshape.2"
        case "analyzed": return "checkmark.circle"
        case "rejected": return "xmark.circle"
        default: return "circle"
        }
    }

    private func statusDisplayName(_ status: String) -> String {
        switch status.lowercased() {
        case "collected": return "status_collected".localized
        case "received": return "status_received".localized
        case "processing": return "status_processing".localized
        case "analyzed": return "status_analyzed".localized
        case "rejected": return "status_rejected".localized
        default: return status.capitalized
        }
    }
}
