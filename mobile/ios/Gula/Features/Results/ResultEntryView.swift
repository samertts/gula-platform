import SwiftUI

struct ResultEntryView: View {
    let onComplete: () -> Void

    @State private var patientId = ""
    @State private var testCode = ""
    @State private var testNameEn = ""
    @State private var testNameAr = ""
    @State private var resultValue = ""
    @State private var unit = ""
    @State private var referenceMin = ""
    @State private var referenceMax = ""
    @State private var sampleBarcode = ""
    @State private var orderingPhysician = ""
    @State private var clinicalNotes = ""
    @State private var isCritical = false
    @State private var isAbnormal = false
    @State private var isLoading = false
    @State private var error: String?

    @Environment(\.dismiss) var dismiss
    @Environment(\.locale) var locale

    var body: some View {
        NavigationView {
            Form {
                Section("patient".localized) {
                    TextField("patient_id".localized, text: $patientId)
                        .keyboardType(.numberPad)
                }

                Section("test_info".localized) {
                    TextField("test_code".localized, text: $testCode)
                    TextField(locale.isArabic ? "" : "test_name_en".localized, text: $testNameEn)
                    if locale.isArabic {
                        TextField("test_name_ar".localized, text: $testNameAr)
                    }
                }

                Section("result".localized) {
                    TextField("value".localized, text: $resultValue)
                        .keyboardType(.decimalPad)
                    TextField("unit".localized, text: $unit)
                    TextField("reference_min".localized, text: $referenceMin)
                        .keyboardType(.decimalPad)
                    TextField("reference_max".localized, text: $referenceMax)
                        .keyboardType(.decimalPad)
                }

                Section("sample".localized) {
                    TextField("sample_barcode".localized, text: $sampleBarcode)
                    TextField("ordering_physician".localized, text: $orderingPhysician)
                }

                Section("notes".localized) {
                    TextEditor(text: $clinicalNotes)
                        .frame(minHeight: 60)
                }

                Section {
                    Toggle("mark_as_critical".localized, isOn: $isCritical)
                        .tint(.gulaCritical)
                    Toggle("mark_as_abnormal".localized, isOn: $isAbnormal)
                        .tint(.gulaWarning)
                }

                if let error = error {
                    Section {
                        GulaAlert(type: .error, message: error, onDismiss: { self.error = nil })
                    }
                }

                Section {
                    GulaButton(title: "save_result".localized, isLoading: isLoading) {
                        saveResult()
                    }
                    .disabled(patientId.isEmpty || testCode.isEmpty || isLoading)
                }
            }
            .gulaListStyle()
            .navigationTitle("enter_result".localized)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("cancel".localized) { dismiss() }
                }
            }
        }
    }

    private func saveResult() {
        guard let citizenId = Int(patientId),
              let value = Double(resultValue) else {
            error = "validation_error".localized
            return
        }

        isLoading = true
        error = nil

        let input = TestResultCreateInput(
            citizenId: citizenId,
            labId: UserDefaults.standard.integer(forKey: "current_user_lab_id"),
            testCode: testCode,
            testNameEn: testNameEn,
            testNameAr: testNameAr.isEmpty ? testNameEn : testNameAr,
            resultValue: value,
            resultText: nil,
            unit: unit.isEmpty ? nil : unit,
            referenceMin: Double(referenceMin),
            referenceMax: Double(referenceMax),
            status: "completed",
            isCritical: isCritical,
            isAbnormal: isAbnormal,
            sampleBarcode: sampleBarcode,
            orderingPhysician: orderingPhysician.isEmpty ? nil : orderingPhysician,
            clinicalNotes: clinicalNotes.isEmpty ? nil : clinicalNotes
        )

        Task {
            do {
                try await ResultRepository.shared.createResult(data: input)
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
