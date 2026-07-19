import Foundation
import Combine

class PatientsViewModel: ObservableObject {
    @Published var patients: [PatientEntity] = []
    @Published var searchText = ""
    @Published var isLoading = false
    @Published var error: String?
    @Published var selectedGender: String?
    @Published var showSearch = false

    private let repository = PatientRepository.shared
    private var cancellables = Set<AnyCancellable>()

    init() {
        repository.$patients
            .receive(on: DispatchQueue.main)
            .assign(to: &$patients)

        $searchText
            .debounce(for: .milliseconds(300), scheduler: DispatchQueue.main)
            .removeDuplicates()
            .sink { [weak self] query in
                self?.performSearch(query)
            }
            .store(in: &cancellables)
    }

    func refresh() async {
        await MainActor.run { isLoading = true; error = nil }
        do {
            try await repository.refreshFromRemote()
            await MainActor.run { isLoading = false }
        } catch {
            await MainActor.run { self.error = error.localizedDescription; isLoading = false }
        }
    }

    func deletePatient(id: Int) async {
        do {
            try await repository.deletePatient(id: id)
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }

    private func performSearch(_ query: String) {
        repository.fetchLocalPatients(search: query.isEmpty ? nil : query)
    }
}
