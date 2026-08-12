import SwiftUI

struct PatientListView: View {
    @StateObject private var viewModel = PatientsViewModel()
    @State private var showAddPatient = false
    @Environment(\.locale) var locale

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                GulaSearchBar(text: $viewModel.searchText, placeholder: "search_patients".localized)

                if viewModel.isLoading && viewModel.patients.isEmpty {
                    GulaPageLoadingView()
                } else if viewModel.patients.isEmpty {
                    GulaEmptyState(
                        title: "no_patients".localized,
                        message: "no_patients_message".localized,
                        imageName: "person.slash",
                        actionTitle: "add_patient".localized
                    ) {
                        showAddPatient = true
                    }
                } else {
                    List {
                        ForEach(viewModel.patients, id: \.id) { patient in
                            NavigationLink(destination: PatientDetailView(patient: patient)) {
                                PatientRow(patient: patient)
                            }
                        }
                        .onDelete { indexSet in
                            if let index = indexSet.first {
                                let patient = viewModel.patients[index]
                                Task { await viewModel.deletePatient(id: Int(patient.id)) }
                            }
                        }
                    }
                    .gulaListStyle()
                }
            }
            .gulaPullToRefresh(isRefreshing: viewModel.isLoading) {
                Task { await viewModel.refresh() }
            }
            .navigationTitle("patients".localized)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: DesignTokens.Spacing.sm) {
                        Button(action: { viewModel.showSearch.toggle() }) {
                            Image(systemName: "magnifyingglass")
                        }
                        Button(action: { showAddPatient = true }) {
                            Image(systemName: "plus")
                        }
                    }
                }
            }
            .sheet(isPresented: $showAddPatient) {
                PatientFormView(isNew: true) { _ in
                    Task { await viewModel.refresh() }
                }
            }
            .sheet(isPresented: $viewModel.showSearch) {
                PatientSearchView()
            }
            .alert("error".localized, isPresented: .init(get: { viewModel.error != nil }, set: { _ in viewModel.error = nil })) {
                Button("ok".localized) { viewModel.error = nil }
            } message: {
                Text(viewModel.error ?? "")
            }
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }
}
