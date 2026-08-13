package io.gula.android.data.repository

import io.gula.android.data.local.dao.PatientDao
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.PatientResponseDto
import io.gula.android.domain.model.PatientCreateRequest
import io.gula.android.util.Resource
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import retrofit2.Response

class PatientRepositoryImplTest {

    private lateinit var patientDao: PatientDao
    private lateinit var gulaApi: GulaApi
    private lateinit var repository: PatientRepositoryImpl

    @Before
    fun setup() {
        patientDao = mockk()
        gulaApi = mockk()
        repository = PatientRepositoryImpl(patientDao, gulaApi)
    }

    @Test
    fun `create patient persists the API response locally`() = runTest {
        val response = PatientResponseDto(
            id = 41,
            fullName = "Queued Patient",
            phone = "07701234567",
            birthDate = "1990-01-01",
            gender = "F",
            labId = 2,
        )
        coEvery { gulaApi.createPatient(any()) } returns Response.success(response)
        coEvery { patientDao.insert(any()) } returns Unit

        val result = repository.createPatient(
            PatientCreateRequest(
                fullName = "Queued Patient",
                phone = "07701234567",
                birthDate = "1990-01-01",
                gender = "F",
            ),
        )

        assertTrue(result is Resource.Success)
        val patient = (result as Resource.Success).data
        assertEquals(41, patient.id)
        assertEquals("Queued Patient", patient.fullName)
        coVerify(exactly = 1) { patientDao.insert(match { it.id == 41 && it.phone == "07701234567" }) }
    }

    @Test
    fun `create patient returns a readable conflict error without caching`() = runTest {
        coEvery { gulaApi.createPatient(any()) } returns Response.error(
            409,
            "Duplicate patient".toResponseBody("text/plain".toMediaType()),
        )

        val result = repository.createPatient(
            PatientCreateRequest(fullName = "Existing Patient", phone = "07709999999"),
        )

        assertTrue(result is Resource.Error)
        assertEquals("Resource already exists", (result as Resource.Error<*>).message)
        coVerify(exactly = 0) { patientDao.insert(any()) }
    }
}
