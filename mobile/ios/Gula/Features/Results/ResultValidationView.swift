import SwiftUI

struct ResultValidationView: View {
    let onComplete: () -> Void

    @State private var pendingResults: [ResultEntity] = []
    @State private var selectedResult: ResultEntity?
    @State private var validationNotes = ""
    @State private var signatureHash = ""
    @State private var isLoading = false
    @State private var error: String?
    @State private var showConfirmDialog = false
    @State private var currentAction: ValidationAction?

    @Environment(\.dismiss) var dismiss
    @Environment(\.locale) var locale

    enum ValidationAction {
        case validate, reject, flag
    }

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                if pendingResults.isEmpty {
                    GulaEmptyState(
                        title: "no_pending_validation".localized,
                        message: "no_pending_validation_message".localized,
                        imageName: "checkmark.seal"
                    )
                } else {
                    List {
                        ForEach(pendingResults, id: \.id) { result in
                            resultCard(result)
                                .onTapGesture { selectedResult = result }
                        }
                    }
                    .gulaListStyle()
                }
            }
            .gulaPullToRefresh(isRefreshing: isLoading) {
                Task { await loadPendingResults() }
            }
            .navigationTitle("validate_results".localized)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("done".localized) { dismiss() }
                }
            }
            .task { await loadPendingResults() }
            .sheet(item: $selectedResult) { result in
                validationSheet(result)
            }
            .alert("confirm_action".localized, isPresented: $showConfirmDialog) {
                Button("cancel".localized, role: .cancel) {}
                Button("confirm".localized, role: .destructive) {
                    if let action = currentAction {
                        performAction(action)
                    }
                }
            } message: {
                Text("confirm_validation_message".localized)
            }
        }
    }

    private func resultCard(_ result: ResultEntity) -> some View {
        GulaCard(style: .outlined) {
            VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
                HStack {
                    VStack(alignment: .leading) {
                        Text(locale.isArabic ? result.testNameAr : result.testNameEn)
                            .gulaBodyMedium()
                            .fontWeight(.semibold)
                        Text("\(result.resultValue, specifier: "%.2f") \(result.unit ?? "")")
                            .gulaBodyLarge()
                            .foregroundColor(result.isCritical ? .gulaCritical : .gulaTextPrimary)
                    }
                    Spacer()
                    GulaBadge(.status(result.status), size: .small)
                }

                HStack(spacing: DesignTokens.Spacing.sm) {
                    Button(action: {
                        currentAction = .validate
                        showConfirmDialog = true
                    }) {
                        Label("validate".localized, systemImage: "checkmark.seal")
                            .gulaLabelSmall()
                            .foregroundColor(.gulaSuccess)
                    }
                    .buttonStyle(PlainButtonStyle())

                    Button(action: {
                        currentAction = .reject
                        showConfirmDialog = true
                    }) {
                        Label("reject".localized, systemImage: "xmark.seal")
                            .gulaLabelSmall()
                            .foregroundColor(.gulaError)
                    }
                    .buttonStyle(PlainButtonStyle())

                    Button(action: {
                        currentAction = .flag
                        showConfirmDialog = true
                    }) {
                        Label("flag".localized, systemImage: "flag.fill")
                            .gulaLabelSmall()
                            .foregroundColor(.gulaWarning)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 4)
    }

    func validationSheet(_ result: ResultEntity) -> some View {
        NavigationView {
            Form {
                Section("result".localized) {
                    Text(locale.isArabic ? result.testNameAr : result.testNameEn)
                        .gulaBodyLarge()
                    Text("\(result.resultValue, specifier: "%.2f") \(result.unit ?? "")")
                        .gulaTitleLarge()
                }

                Section("validation_notes".localized) {
                    TextEditor(text: $validationNotes)
                        .frame(minHeight: 100)
                }

                Section("signature".localized) {
                    SecureField("signature_hash".localized, text: $signatureHash)
                }

                Section {
                    GulaButton(title: "validate".localized, style: .primary) {
                        currentAction = .validate
                        showConfirmDialog = true
                    }
                }
            }
            .navigationTitle("validation".localized)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("done".localized) { selectedResult = nil }
                }
            }
        }
    }

    private func loadPendingResults() async {
        await MainActor.run { isLoading = true; error = nil }
        do {
            let localResults = ResultRepository.shared.results
            await MainActor.run {
                pendingResults = localResults.filter { $0.status == "completed" || $0.status == "pending" }
                isLoading = false
            }
        }
    }

    private func performAction(_ action: ValidationAction) {
        guard let result = selectedResult else { return }

        Task {
            do {
                switch action {
                case .validate:
                    try await ResultRepository.shared.validateResult(
                        id: Int(result.id),
                        notes: validationNotes.isEmpty ? nil : validationNotes,
                        signatureHash: signatureHash.isEmpty ? nil : signatureHash
                    )
                case .reject:
                    try await ResultRepository.shared.validateResult(
                        id: Int(result.id),
                        notes: "Rejected: \(validationNotes)",
                        signatureHash: nil
                    )
                case .flag:
                    try await ResultRepository.shared.flagCritical(id: Int(result.id))
                }

                await MainActor.run {
                    selectedResult = nil
                    validationNotes = ""
                    signatureHash = ""
                    onComplete()
                }
                await loadPendingResults()
            } catch {
                await MainActor.run { self.error = error.localizedDescription }
            }
        }
    }
}

extension ResultEntity: Identifiable {}
