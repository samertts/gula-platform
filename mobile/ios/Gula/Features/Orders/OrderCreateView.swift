import SwiftUI

struct OrderCreateView: View {
    let onComplete: () -> Void

    @State private var patientId = ""
    @State private var doctorName = ""
    @State private var testName = ""
    @State private var results: [ResultItemData] = []
    @State private var isLoading = false
    @State private var error: String?
    @State private var patientSearchText = ""
    @State private var searchResults: [PatientResponse] = []
    @State private var showPatientSearch = false
    @State private var selectedPatientName = ""

    @Environment(\.dismiss) var dismiss
    @Environment(\.locale) var locale

    var body: some View {
        NavigationView {
            Form {
                Section("patient_info".localized) {
                    if !selectedPatientName.isEmpty {
                        HStack {
                            Image(systemName: "person.fill.checkmark")
                                .foregroundColor(.gulaSuccess)
                            Text(selectedPatientName)
                                .gulaBodyMedium()
                            Spacer()
                            Button("change".localized) { selectedPatientName = ""; patientId = "" }
                                .gulaLabelSmall()
                        }
                    } else {
                        TextField("patient_id".localized, text: $patientId)
                            .gulaBodyMedium()
                            .keyboardType(.numberPad)

                        Button("search_patient".localized) {
                            showPatientSearch = true
                        }
                        .gulaLabelMedium()
                        .foregroundColor(.gulaPrimary)
                    }

                    TextField("doctor_name".localized, text: $doctorName)
                        .gulaBodyMedium()
                }

                Section("tests".localized) {
                    ForEach(results.indices, id: \.self) { index in
                        VStack(alignment: .leading, spacing: 4) {
                            TextField("test_name".localized, text: Binding(
                                get: { results[index].testName },
                                set: { results[index] = ResultItemData(testName: $0, value: results[index].value, valueText: results[index].valueText, unit: results[index].unit, normalRangeLow: results[index].normalRangeLow, normalRangeHigh: results[index].normalRangeHigh) }
                            ))
                            TextField("value".localized, value: Binding(
                                get: { results[index].value ?? 0 },
                                set: { results[index] = ResultItemData(testName: results[index].testName, value: $0, valueText: results[index].valueText, unit: results[index].unit, normalRangeLow: results[index].normalRangeLow, normalRangeHigh: results[index].normalRangeHigh) }
                            ), format: .number)
                            .keyboardType(.decimalPad)
                        }
                    }
                    .onDelete { results.remove(atOffsets: $0) }

                    Button(action: {
                        results.append(ResultItemData(testName: "", value: nil, valueText: nil, unit: nil, normalRangeLow: nil, normalRangeHigh: nil))
                    }) {
                        HStack {
                            Image(systemName: "plus.circle.fill")
                            Text("add_test".localized)
                        }
                        .foregroundColor(.gulaPrimary)
                    }
                }

                if let error = error {
                    Section {
                        GulaAlert(type: .error, message: error, onDismiss: { self.error = nil })
                    }
                }
            }
            .gulaListStyle()
            .navigationTitle("create_order".localized)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("cancel".localized) { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("create".localized) { createOrder() }
                        .disabled(patientId.isEmpty || results.isEmpty || isLoading)
                }
            }
            .sheet(isPresented: $showPatientSearch) {
                PatientSearchView()
            }
        }
    }

    private func createOrder() {
        guard let patientIdInt = Int(patientId), !results.isEmpty else { return }
        isLoading = true
        error = nil

        Task {
            do {
                try await OrderRepository.shared.createOrder(
                    patientId: patientIdInt,
                    doctorName: doctorName.isEmpty ? nil : doctorName,
                    results: results
                )
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
