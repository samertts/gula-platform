package io.gula.android.data.repository

import io.gula.android.data.local.dao.PatientDao
import io.gula.android.data.local.entity.PatientEntity
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.PatientCreateRequestDto
import io.gula.android.data.remote.dto.PatientResponseDto
import io.gula.android.data.remote.dto.PatientUpdateRequestDto
import io.gula.android.domain.model.Patient
import io.gula.android.domain.model.PatientCreateRequest
import io.gula.android.domain.model.PatientUpdateRequest
import io.gula.android.domain.repository.PatientRepository
import io.gula.android.util.Resource
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PatientRepositoryImpl @Inject constructor(
    private val patientDao: PatientDao,
    private val gulaApi: GulaApi,
) : PatientRepository {

    override fun getPatients(search: String?, page: Int, limit: Int): Flow<Resource<List<Patient>>> {
        return patientDao.getPatients(search, limit, (page - 1) * limit).map { entities ->
            if (entities.isNotEmpty()) {
                Resource.success(entities.map { it.toDomain() })
            } else {
                Resource.loading()
            }
        }
    }

    override fun getPatientById(id: Int): Flow<Resource<Patient>> {
        return patientDao.getPatientById(id).map { entity ->
            if (entity != null) {
                Resource.success(entity.toDomain())
            } else {
                Resource.loading()
            }
        }
    }

    override fun getPatientsByFamilyId(familyId: String): Flow<Resource<List<Patient>>> {
        return patientDao.getPatientsByFamilyId(familyId).map { entities ->
            Resource.success(entities.map { it.toDomain() })
        }
    }

    override suspend fun createPatient(request: PatientCreateRequest): Resource<Patient> {
        return try {
            val response = gulaApi.createPatient(
                PatientCreateRequestDto(
                    fullName = request.fullName,
                    phone = request.phone,
                    birthDate = request.birthDate,
                    gender = request.gender,
                    email = request.email,
                    nationalId = request.nationalId,
                    familyId = request.familyId,
                    forceCreate = request.forceCreate,
                    guardianId = request.guardianId,
                )
            )
            if (response.isSuccessful) {
                val dto = response.body()!!
                val patient = dto.toDomain()
                patientDao.insert(patient.toEntity())
                Resource.success(patient)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun updatePatient(id: Int, request: PatientUpdateRequest): Resource<Patient> {
        return try {
            val response = gulaApi.updatePatient(
                id,
                PatientUpdateRequestDto(
                    fullName = request.fullName,
                    phone = request.phone,
                    birthDate = request.birthDate,
                    gender = request.gender,
                    email = request.email,
                    familyId = request.familyId,
                )
            )
            if (response.isSuccessful) {
                val dto = response.body()!!
                val patient = dto.toDomain()
                patientDao.insert(patient.toEntity())
                Resource.success(patient)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun deletePatient(id: Int): Resource<Unit> {
        return try {
            val response = gulaApi.deletePatient(id)
            if (response.isSuccessful) {
                patientDao.deleteById(id)
                Resource.success(Unit)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            Resource.error(e.message ?: "Network error")
        }
    }

    override suspend fun searchPatients(query: String): Resource<List<Patient>> {
        return try {
            val local = patientDao.searchPatients(query)
            if (local.isNotEmpty()) {
                return Resource.success(local.map { it.toDomain() })
            }
            val response = gulaApi.getPatients(search = query, limit = 50)
            if (response.isSuccessful) {
                val patients = response.body()!!.items.map { it.toDomain() }
                patientDao.insertAll(patients.map { it.toEntity() })
                Resource.success(patients)
            } else {
                Resource.error(parseError(response.code(), response.errorBody()?.string()))
            }
        } catch (e: Exception) {
            val local = patientDao.searchPatients(query)
            if (local.isNotEmpty()) {
                Resource.success(local.map { it.toDomain() })
            } else {
                Resource.error(e.message ?: "Network error")
            }
        }
    }

    override suspend fun refreshPatients() {
        try {
            val response = gulaApi.getPatients(limit = 100)
            if (response.isSuccessful) {
                val patients = response.body()!!.items.map { it.toDomain() }
                patientDao.insertAll(patients.map { it.toEntity() })
            }
        } catch (_: Exception) { }
    }

    override fun getPatientCount(): Flow<Int> = patientDao.getCount()
}

private fun PatientResponseDto.toDomain() = Patient(
    id = id,
    fullName = fullName,
    phone = phone,
    birthDate = birthDate,
    gender = gender,
    email = email,
    labId = labId,
    nationalId = nationalId,
    healthId = healthId,
    familyId = familyId,
    guardianId = guardianId,
    status = status,
    createdAt = createdAt,
    updatedAt = updatedAt,
)

private fun Patient.toEntity() = PatientEntity(
    id = id,
    fullName = fullName,
    phone = phone,
    birthDate = birthDate,
    gender = gender,
    email = email,
    labId = labId,
    nationalId = nationalId,
    healthId = healthId,
    familyId = familyId,
    guardianId = guardianId,
    status = status,
    createdAt = createdAt,
    updatedAt = updatedAt,
)

private fun PatientEntity.toDomain() = Patient(
    id = id,
    fullName = fullName,
    phone = phone,
    birthDate = birthDate,
    gender = gender,
    email = email,
    labId = labId,
    nationalId = nationalId,
    healthId = healthId,
    familyId = familyId,
    guardianId = guardianId,
    status = status,
    createdAt = createdAt,
    updatedAt = updatedAt,
)
