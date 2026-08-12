import SwiftUI

struct SampleCollectionView: View {
    let onComplete: () -> Void

    @State private var orderId = ""
    @State private var sampleType = "Blood"
    @State private var notes = ""
    @State private var isLoading = false
    @State private var error: String?
    @State private var showScanner = false

    @Environment(\.dismiss) var dismiss
    @Environment(\.locale) var locale

    private let sampleTypes = ["Blood", "Urine", "Stool", "Saliva", "Tissue", "Swab", "CSF", "Other"]

    var body: some View {
        NavigationView {
            Form {
                Section("sample_info".localized) {
                    HStack {
                        TextField("order_id".localized, text: $orderId)
                            .gulaBodyMedium()
                            .keyboardType(.numberPad)

                        Button(action: { showScanner = true }) {
                            Image(systemName: "qrcode.viewfinder")
                                .foregroundColor(.gulaPrimary)
                        }
                    }

                    Picker("sample_type".localized, selection: $sampleType) {
                        ForEach(sampleTypes, id: \.self) { type in
                            Text(type).tag(type)
                        }
                    }

                    TextField("notes".localized, text: $notes)
                        .gulaBodyMedium()
                }

                if let error = error {
                    Section {
                        GulaAlert(type: .error, message: error, onDismiss: { self.error = nil })
                    }
                }

                Section {
                    GulaButton(title: "register_sample".localized, isLoading: isLoading) {
                        registerSample()
                    }
                    .disabled(orderId.isEmpty || isLoading)
                }
            }
            .gulaListStyle()
            .navigationTitle("new_sample".localized)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("cancel".localized) { dismiss() }
                }
            }
            .sheet(isPresented: $showScanner) {
                BarcodeScannerView(onCapture: { barcode in
                    if let id = Int(barcode) {
                        orderId = "\(id)"
                    } else {
                        orderId = barcode
                    }
                    showScanner = false
                }, onDismiss: { showScanner = false })
            }
        }
    }

    private func registerSample() {
        guard let orderIdInt = Int(orderId) else {
            error = "invalid_order_id".localized
            return
        }

        isLoading = true
        error = nil

        Task {
            do {
                try await SampleRepository.shared.createSample(orderId: orderIdInt, sampleType: sampleType)
                await MainActor.run {
                    dismiss()
                    onComplete()
                }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
}
