package io.gula.android.domain.repository

import io.gula.android.domain.model.Patient
import io.gula.android.domain.model.PatientCreateRequest
import io.gula.android.domain.model.PatientUpdateRequest
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow

interface PatientRepository {
    fun getPatients(search: String? = null, page: Int = 1, limit: Int = 20): Flow<Resource<List<Patient>>>
    fun getPatientById(id: Int): Flow<Resource<Patient>>
    fun getPatientsByFamilyId(familyId: String): Flow<Resource<List<Patient>>>
    suspend fun createPatient(request: PatientCreateRequest): Resource<Patient>
    suspend fun updatePatient(id: Int, request: PatientUpdateRequest): Resource<Patient>
    suspend fun deletePatient(id: Int): Resource<Unit>
    suspend fun searchPatients(query: String): Resource<List<Patient>>
    suspend fun refreshPatients()
    fun getPatientCount(): Flow<Int>
}
