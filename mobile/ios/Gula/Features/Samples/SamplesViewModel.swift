import Foundation
import Combine

class SamplesViewModel: ObservableObject {
    @Published var samples: [SampleEntity] = []
    @Published var isLoading = false
    @Published var error: String?
    @Published var selectedStatus: String?
    @Published var scannedBarcode: String?

    private let repository = SampleRepository.shared
    private var cancellables = Set<AnyCancellable>()

    init() {
        repository.$samples
            .receive(on: DispatchQueue.main)
            .assign(to: &$samples)
    }

    var sampleStatuses: [String] {
        ["all", "collected", "received", "processing", "analyzed", "rejected"]
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

    func filterByStatus(_ status: String?) {
        selectedStatus = status
        repository.fetchLocalSamples(status: status)
    }

    func receiveSample(id: Int) async {
        do {
            try await repository.receiveSample(id: id)
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }

    func rejectSample(id: Int, reason: String) async {
        do {
            try await repository.rejectSample(id: id, reason: reason)
        } catch {
            await MainActor.run { self.error = error.localizedDescription }
        }
    }

    func lookupBarcode(_ barcode: String) {
        scannedBarcode = barcode
    }
}
