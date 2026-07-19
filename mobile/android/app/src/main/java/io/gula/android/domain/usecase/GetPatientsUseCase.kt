package io.gula.android.domain.usecase

import io.gula.android.domain.model.Patient
import io.gula.android.domain.repository.PatientRepository
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class GetPatientsUseCase @Inject constructor(
    private val patientRepository: PatientRepository
) {
    operator fun invoke(
        search: String? = null,
        page: Int = 1,
        limit: Int = 20,
    ): Flow<Resource<List<Patient>>> {
        return patientRepository.getPatients(search, page, limit)
    }
}
