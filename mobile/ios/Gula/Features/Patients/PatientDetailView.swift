import SwiftUI

struct PatientDetailView: View {
    let patient: PatientEntity
    @State private var patientHistory: PatientHistoryData?
    @State private var isLoading = true
    @State private var error: String?
    @State private var showEditForm = false
    @State private var showQR = false
    @Environment(\.locale) var locale

    var body: some View {
        ScrollView {
            VStack(spacing: DesignTokens.Spacing.md) {
                patientHeader

                if isLoading {
                    GulaLoadingView(message: "loading".localized)
                        .padding(.top, 40)
                } else if let error = error {
                    GulaErrorView(message: error, retryAction: { Task { await loadHistory() } })
                } else {
                    patientInfoCard

                    if let history = patientHistory {
                        if !history.orders.isEmpty {
                            ordersSection(history.orders)
                        }
                        if !history.samples.isEmpty {
                            samplesSection(history.samples)
                        }
                        if !history.results.isEmpty {
                            resultsSection(history.results)
                        }
                    }
                }
            }
            .padding()
        }
        .gulaBackground()
        .navigationTitle(patient.fullName)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                HStack(spacing: DesignTokens.Spacing.sm) {
                    Button(action: { showQR = true }) {
                        Image(systemName: "qrcode")
                    }
                    Button(action: { showEditForm = true }) {
                        Image(systemName: "pencil")
                    }
                }
            }
        }
        .task { await loadHistory() }
        .sheet(isPresented: $showEditForm) {
            PatientFormView(isNew: false, patient: patient) { _ in
                Task { await loadHistory() }
            }
        }
        .sheet(isPresented: $showQR) {
            PatientCardQRView(patientId: Int(patient.id), patientName: patient.fullName)
        }
    }

    private var patientHeader: some View {
        VStack(spacing: DesignTokens.Spacing.sm) {
            Circle()
                .fill(Color.gulaPrimary)
                .frame(width: 80, height: 80)
                .overlay(
                    Text(initials)
                        .gulaHeadlineLarge()
                        .foregroundColor(.white)
                )

            Text(patient.fullName)
                .gulaTitleLarge()
                .foregroundColor(.gulaTextPrimary)

            GulaBadge(.status(patient.status), size: .medium)
        }
        .frame(maxWidth: .infinity)
        .padding()
    }

    private var patientInfoCard: some View {
        GulaCard(style: .outlined) {
            VStack(spacing: DesignTokens.Spacing.md) {
                infoRow(icon: "phone.fill", label: "phone".localized, value: patient.phone)
                if let email = patient.email {
                    Divider()
                    infoRow(icon: "envelope.fill", label: "email".localized, value: email)
                }
                if let gender = patient.gender {
                    Divider()
                    infoRow(icon: "person.fill", label: "gender".localized, value: genderDisplayName(gender))
                }
                if let birthDate = patient.birthDate {
                    Divider()
                    infoRow(icon: "calendar", label: "birth_date".localized, value: birthDate)
                }
                Divider()
                infoRow(icon: "building.2", label: "lab_id".localized, value: "\(patient.labId)")
            }
        }
    }

    private func ordersSection(_ orders: [OrderResponse]) -> some View {
        GulaCard(style: .outlined) {
            VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
                Text("orders".localized)
                    .gulaTitleSmall()
                    .fontWeight(.bold)

                ForEach(orders.prefix(5), id: \.id) { order in
                    HStack {
                        Text("order_id_prefix".localized + " #\(order.id)")
                            .gulaBodyMedium()
                        Spacer()
                        GulaBadge(.status(order.status), size: .small)
                    }
                    Divider()
                }
            }
        }
    }

    private func samplesSection(_ samples: [SampleResponseStruct]) -> some View {
        GulaCard(style: .outlined) {
            VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
                Text("samples".localized)
                    .gulaTitleSmall()
                    .fontWeight(.bold)

                ForEach(samples.prefix(5), id: \.id) { sample in
                    HStack {
                        Text(sample.sampleType)
                            .gulaBodyMedium()
                        Spacer()
                        GulaBadge(.status(sample.status), size: .small)
                    }
                    Divider()
                }
            }
        }
    }

    private func resultsSection(_ results: [TestResultBriefData]) -> some View {
        GulaCard(style: .outlined) {
            VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
                Text("results".localized)
                    .gulaTitleSmall()
                    .fontWeight(.bold)

                ForEach(results.prefix(5), id: \.id) { result in
                    HStack {
                        VStack(alignment: .leading) {
                            Text(locale.isArabic ? result.testNameAr : result.testNameEn)
                                .gulaBodyMedium()
                            if let value = result.resultValue {
                                Text("\(value, specifier: "%.2f") \(result.unit ?? "")")
                                    .gulaLabelSmall()
                                    .foregroundColor(.gulaTextSecondary)
                            }
                        }
                        Spacer()
                        if result.isCritical {
                            GulaBadge(.custom(text: "critical".localized, color: .gulaCritical), size: .small)
                        } else if result.isAbnormal {
                            GulaBadge(.custom(text: "abnormal".localized, color: .gulaWarning), size: .small)
                        }
                    }
                    Divider()
                }
            }
        }
    }

    private func infoRow(icon: String, label: String, value: String) -> some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(.gulaPrimary)
                .frame(width: 24)
            VStack(alignment: .leading) {
                Text(label)
                    .gulaLabelSmall()
                    .foregroundColor(.gulaTextSecondary)
                Text(value)
                    .gulaBodyMedium()
                    .foregroundColor(.gulaTextPrimary)
            }
            Spacer()
        }
    }

    private var initials: String {
        let parts = patient.fullName.split(separator: " ")
        let first = parts.first?.prefix(1) ?? ""
        let last = parts.dropFirst().first?.prefix(1) ?? ""
        return "\(first)\(last)".uppercased()
    }

    private func genderDisplayName(_ gender: String) -> String {
        switch gender.lowercased() {
        case "male", "m": return "male".localized
        case "female", "f": return "female".localized
        default: return gender
        }
    }

    private func loadHistory() async {
        await MainActor.run { isLoading = true }
        do {
            let history = try await PatientRepository.shared.getPatientHistory(id: Int(patient.id))
            await MainActor.run {
                patientHistory = history
                isLoading = false
            }
        } catch {
            await MainActor.run { self.error = error.localizedDescription; isLoading = false }
        }
    }
}
