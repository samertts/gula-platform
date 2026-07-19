import SwiftUI

struct PatientSearchView: View {
    @State private var searchText = ""
    @State private var searchResults: [PatientResponse] = []
    @State private var isLoading = false
    @State private var error: String?
    @Environment(\.dismiss) var dismiss
    @Environment(\.locale) var locale

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                GulaSearchBar(text: $searchText, placeholder: "search_patients".localized, debounceInterval: 0.5) { query in
                    Task { await performSearch(query) }
                }
                .padding()

                if isLoading {
                    Spacer()
                    GulaLoadingView(message: "searching".localized)
                    Spacer()
                } else if searchResults.isEmpty && !searchText.isEmpty {
                    Spacer()
                    GulaEmptyState(
                        title: "no_results".localized,
                        message: "no_search_results".localized,
                        imageName: "magnifyingglass"
                    )
                    Spacer()
                } else {
                    List(searchResults, id: \.id) { patient in
                        HStack(spacing: DesignTokens.Spacing.md) {
                            Circle()
                                .fill(Color.gulaInfo)
                                .frame(width: 40, height: 40)
                                .overlay(Text(patient.fullName.prefix(1).uppercased()).foregroundColor(.white))

                            VStack(alignment: .leading, spacing: 4) {
                                Text(patient.fullName)
                                    .gulaBodyMedium()
                                    .fontWeight(.semibold)
                                Text(patient.phone)
                                    .gulaLabelSmall()
                                    .foregroundColor(.gulaTextSecondary)
                            }

                            Spacer()

                            Image(systemName: "chevron.right")
                                .foregroundColor(.gulaTextTertiary)
                        }
                        .padding(.vertical, 4)
                        .contentShape(Rectangle())
                        .onTapGesture {
                            let patientEntity = PatientRepository.shared.getPatient(id: patient.id)
                            if patientEntity != nil {
                                dismiss()
                            }
                        }
                    }
                    .gulaListStyle()
                }
            }
            .navigationTitle("search_patients".localized)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("done".localized) { dismiss() }
                }
            }
        }
    }

    private func performSearch(_ query: String) async {
        guard !query.isEmpty else { return }
        await MainActor.run { isLoading = true; error = nil }

        do {
            let results = try await PatientRepository.shared.searchRemote(query: query)
            await MainActor.run {
                searchResults = results
                isLoading = false
            }
        } catch {
            await MainActor.run {
                self.error = error.localizedDescription
                isLoading = false
            }
        }
    }
}
