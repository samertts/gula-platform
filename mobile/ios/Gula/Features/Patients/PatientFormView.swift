import SwiftUI

struct PatientFormView: View {
    let isNew: Bool
    let patient: PatientEntity?
    let onSave: (PatientEntity?) -> Void

    @State private var fullName = ""
    @State private var phone = ""
    @State private var email = ""
    @State private var birthDate = ""
    @State private var gender = "male"
    @State private var nationalId = ""
    @State private var isLoading = false
    @State private var error: String?

    @Environment(\.dismiss) var dismiss
    @Environment(\.locale) var locale

    private let genders = ["male", "female"]

    init(isNew: Bool, patient: PatientEntity? = nil, onSave: @escaping (PatientEntity?) -> Void) {
        self.isNew = isNew
        self.patient = patient
        self.onSave = onSave
    }

    var body: some View {
        NavigationView {
            Form {
                Section("personal_info".localized) {
                    TextField("full_name".localized, text: $fullName)
                        .gulaBodyMedium()

                    TextField("phone".localized, text: $phone)
                        .gulaBodyMedium()
                        .keyboardType(.phonePad)

                    TextField("email".localized, text: $email)
                        .gulaBodyMedium()
                        .keyboardType(.emailAddress)
                        .textContentType(.emailAddress)

                    TextField("birth_date".localized, text: $birthDate)
                        .gulaBodyMedium()
                        .placeholder("YYYY-MM-DD", text: $birthDate)

                    Picker("gender".localized, selection: $gender) {
                        ForEach(genders, id: \.self) { g in
                            Text(locale.isArabic ? (g == "male" ? "ذكر" : "أنثى") : g.capitalized)
                                .tag(g)
                        }
                    }
                }

                Section("additional_info".localized) {
                    TextField("national_id".localized, text: $nationalId)
                        .gulaBodyMedium()
                }

                if let error = error {
                    Section {
                        GulaAlert(type: .error, message: error, onDismiss: { self.error = nil })
                    }
                }
            }
            .gulaListStyle()
            .navigationTitle(isNew ? "add_patient".localized : "edit_patient".localized)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("cancel".localized) { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(isNew ? "add".localized : "save".localized) {
                        savePatient()
                    }
                    .disabled(fullName.isEmpty || phone.isEmpty || isLoading)
                }
            }
            .onAppear {
                if let patient = patient {
                    fullName = patient.fullName
                    phone = patient.phone
                    email = patient.email ?? ""
                    birthDate = patient.birthDate ?? ""
                    gender = patient.gender ?? "male"
                    nationalId = patient.nationalId ?? ""
                }
            }
        }
    }

    private func savePatient() {
        isLoading = true
        error = nil

        Task {
            do {
                let body: [String: Any] = [
                    "full_name": fullName,
                    "phone": phone,
                    "email": email,
                    "birth_date": birthDate,
                    "gender": gender,
                    "national_id": nationalId
                ]

                if isNew {
                    let _: PatientResponse = try await APIClient.shared.request(.createPatient, body: body)
                } else if let patient = patient {
                    let _: PatientResponse = try await APIClient.shared.request(
                        .updatePatient(id: Int(patient.id)), body: body
                    )
                }

                await MainActor.run {
                    dismiss()
                    onSave(nil)
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

extension View {
    func placeholder(_ placeholder: String, text: Binding<String>) -> some View {
        self.modifier(PlaceholderModifier(placeholder: placeholder, text: text))
    }
}

struct PlaceholderModifier: ViewModifier {
    let placeholder: String
    @Binding var text: String

    func body(content: Content) -> some View {
        ZStack(alignment: .leading) {
            if text.isEmpty {
                Text(placeholder)
                    .foregroundColor(.gulaTextTertiary)
            }
            content
        }
    }
}
