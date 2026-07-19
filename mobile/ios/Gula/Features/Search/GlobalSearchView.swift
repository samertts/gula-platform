import SwiftUI

enum SearchEntityType: String, CaseIterable {
    case all, patients, orders, samples, results

    var displayName: String {
        switch self {
        case .all: return "all".localized
        case .patients: return "patients".localized
        case .orders: return "orders".localized
        case .samples: return "samples".localized
        case .results: return "results".localized
        }
    }
}

struct GlobalSearchView: View {
    @State private var searchText = ""
    @State private var selectedType: SearchEntityType = .all
    @State private var patientResults: [PatientEntity] = []
    @State private var orderResults: [OrderEntity] = []
    @State private var sampleResults: [SampleEntity] = []
    @State private var resultResults: [ResultEntity] = []
    @State private var isLoading = false

    @Environment(\.dismiss) var dismiss
    @Environment(\.locale) var locale
    @FocusState private var isFocused: Bool

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                HStack(spacing: DesignTokens.Spacing.sm) {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(.gulaTextTertiary)

                    TextField("search_global_placeholder".localized, text: $searchText)
                        .gulaBodyLarge()
                        .focused($isFocused)
                        .onSubmit { performSearch() }
                        .onChange(of: searchText) { _ in
                            if !searchText.isEmpty {
                                performSearch()
                            } else {
                                clearResults()
                            }
                        }

                    if !searchText.isEmpty {
                        Button(action: { searchText = ""; clearResults() }) {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundColor(.gulaTextTertiary)
                        }
                    }
                }
                .padding(DesignTokens.Spacing.md)
                .background(Color.gulaSurfaceSecondary)
                .cornerRadius(DesignTokens.Radius.md)
                .padding()

                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: DesignTokens.Spacing.sm) {
                        ForEach(SearchEntityType.allCases, id: \.self) { type in
                            Button(action: { selectedType = type }) {
                                Text(type.displayName)
                                    .gulaLabelMedium()
                                    .padding(.horizontal, DesignTokens.Spacing.md)
                                    .padding(.vertical, DesignTokens.Spacing.xs)
                                    .background(selectedType == type ? Color.gulaPrimary : Color.gulaSurfaceSecondary)
                                    .foregroundColor(selectedType == type ? .white : .gulaTextPrimary)
                                    .cornerRadius(DesignTokens.Radius.full)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                    .padding(.horizontal, DesignTokens.Spacing.md)
                }
                .padding(.bottom, DesignTokens.Spacing.sm)

                if isLoading {
                    Spacer()
                    GulaLoadingView(message: "searching".localized)
                    Spacer()
                } else if searchText.isEmpty {
                    Spacer()
                    GulaEmptyState(title: "search".localized, message: "search_global_hint".localized, imageName: "magnifyingglass")
                    Spacer()
                } else if !hasResults {
                    Spacer()
                    GulaEmptyState(title: "no_results".localized, message: "no_search_results".localized, imageName: "magnifyingglass")
                    Spacer()
                } else {
                    resultsList
                }
            }
            .navigationTitle("search".localized)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("done".localized) { dismiss() }
                }
            }
            .onAppear { isFocused = true }
        }
    }

    private var resultsList: some View {
        List {
            if selectedType == .all || selectedType == .patients {
                if !patientResults.isEmpty {
                    Section("patients".localized) {
                        ForEach(patientResults, id: \.id) { patient in
                            PatientRow(patient: patient)
                        }
                    }
                }
            }

            if selectedType == .all || selectedType == .orders {
                if !orderResults.isEmpty {
                    Section("orders".localized) {
                        ForEach(orderResults, id: \.id) { order in
                            OrderRow(order: order)
                        }
                    }
                }
            }

            if selectedType == .all || selectedType == .samples {
                if !sampleResults.isEmpty {
                    Section("samples".localized) {
                        ForEach(sampleResults, id: \.id) { sample in
                            SampleRow(sample: sample)
                        }
                    }
                }
            }

            if selectedType == .all || selectedType == .results {
                if !resultResults.isEmpty {
                    Section("results".localized) {
                        ForEach(resultResults, id: \.id) { result in
                            ResultRow(result: result)
                        }
                    }
                }
            }
        }
        .gulaListStyle()
    }

    private var hasResults: Bool {
        !patientResults.isEmpty || !orderResults.isEmpty || !sampleResults.isEmpty || !resultResults.isEmpty
    }

    private func performSearch() {
        guard !searchText.isEmpty else { clearResults(); return }

        let context = CoreDataStack.shared.viewContext
        let query = searchText

        if selectedType == .all || selectedType == .patients {
            let request: NSFetchRequest<PatientEntity> = PatientEntity.fetchRequest()
            request.predicate = NSPredicate(format: "searchName CONTAINS[cd] %@ OR phone CONTAINS[cd] %@", query, query)
            request.fetchLimit = 10
            patientResults = (try? context.fetch(request)) ?? []
        } else {
            patientResults = []
        }

        if selectedType == .all || selectedType == .orders {
            let request: NSFetchRequest<OrderEntity> = OrderEntity.fetchRequest()
            request.predicate = NSPredicate(format: "id == %d", Int(query) ?? -1)
            request.fetchLimit = 10
            orderResults = (try? context.fetch(request)) ?? []
        } else {
            orderResults = []
        }

        if selectedType == .all || selectedType == .samples {
            let request: NSFetchRequest<SampleEntity> = SampleEntity.fetchRequest()
            request.predicate = NSPredicate(format: "barcode CONTAINS[cd] %@", query)
            request.fetchLimit = 10
            sampleResults = (try? context.fetch(request)) ?? []
        } else {
            sampleResults = []
        }

        if selectedType == .all || selectedType == .results {
            let request: NSFetchRequest<ResultEntity> = ResultEntity.fetchRequest()
            request.predicate = NSPredicate(format: "testNameEn CONTAINS[cd] %@ OR testNameAr CONTAINS[cd] %@", query, query)
            request.fetchLimit = 10
            resultResults = (try? context.fetch(request)) ?? []
        } else {
            resultResults = []
        }
    }

    private func clearResults() {
        patientResults = []
        orderResults = []
        sampleResults = []
        resultResults = []
    }
}
