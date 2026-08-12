package io.gula.android.data.repository

import io.gula.android.data.local.dao.PatientDao
import io.gula.android.data.local.entity.PatientEntity
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.dto.PatientDto
import io.gula.android.data.remote.dto.PatientListResponseDto
import io.gula.android.domain.model.Patient
import io.gula.android.util.NetworkMonitor
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest
import org.junit.Before
import org.junit.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class PatientRepositoryImplTest {

    private lateinit var patientDao: PatientDao
    private lateinit var gulaApi: GulaApi
    private lateinit var networkMonitor: NetworkMonitor
    private lateinit var repository: PatientRepositoryImpl

    private val testDispatcher = StandardTestDispatcher()
    private val onlineFlow = MutableStateFlow(true)

    @Before
    fun setup() {
        patientDao = mockk()
        gulaApi = mockk()
        networkMonitor = mockk()

        every { networkMonitor.isOnline } returns onlineFlow

        repository = PatientRepositoryImpl(
            patientDao = patientDao,
            gulaApi = gulaApi,
            networkMonitor = networkMonitor,
            ioDispatcher = testDispatcher
        )
    }

    @Test
    fun `getPatients returns cached data when offline`() = runTest(testDispatcher) {
        val cachedPatients = listOf(
            PatientEntity(
                id = "p1",
                fullName = "Online Patient",
                phone = "07701234567",
                email = "online@test.com",
                birthDate = "1990-01-01",
                gender = "male",
                nationalId = null,
                createdAt = "2024-01-01T00:00:00Z",
                updatedAt = "2024-01-01T00:00:00Z"
            )
        )

        onlineFlow.value = false
        coEvery { patientDao.getAllPatients() } returns cachedPatients

        val result = repository.getPatients(page = 0, pageSize = 20, query = null).first()

        assertTrue(result.isSuccess)
        val patients = result.getOrThrow()
        assertEquals(1, patients.size)
        assertEquals("Online Patient", patients[0].fullName)

        coVerify(exactly = 0) { gulaApi.getPatients(any(), any(), any()) }
    }

    @Test
    fun `getPatients fetches from API and caches when online`() = runTest(testDispatcher) {
        val apiResponse = PatientListResponseDto(
            items = listOf(
                PatientDto(
                    id = "p1",
                    fullName = "API Patient",
                    phone = "07701234567",
                    email = null,
                    birthDate = "1990-06-15",
                    gender = "female",
                    nationalId = null,
                    sndhsHealthId = null,
                    familyId = null,
                    address = "Baghdad",
                    bloodType = "A+",
                    notes = null,
                    isActive = true,
                    labId = "lab-1",
                    createdAt = "2024-01-01T00:00:00Z",
                    updatedAt = "2024-01-01T00:00:00Z"
                )
            ),
            total = 1,
            page = 0,
            pageSize = 20,
            totalPages = 1
        )

        coEvery { gulaApi.getPatients(page = 0, pageSize = 20, query = null) } returns apiResponse
        coEvery { patientDao.insertAll(any<List<PatientEntity>>()) } returns Unit
        coEvery { patientDao.getAllPatients() } returns apiResponse.items.map { it.toEntity() }

        val result = repository.getPatients(page = 0, pageSize = 20, query = null).first()

        assertTrue(result.isSuccess)
        val patients = result.getOrThrow()
        assertEquals(1, patients.size)
        assertEquals("API Patient", patients[0].fullName)

        coVerify {
            gulaApi.getPatients(page = 0, pageSize = 20, query = null)
            patientDao.insertAll(any<List<PatientEntity>>())
        }
    }

    @Test
    fun `getPatientById returns patient from cache`() = runTest(testDispatcher) {
        val cachedEntity = PatientEntity(
            id = "p1",
            fullName = "Cached Patient",
            phone = "07701234567",
            email = null,
            birthDate = "1990-01-01",
            gender = "male",
            nationalId = null,
            createdAt = "2024-01-01T00:00:00Z",
            updatedAt = "2024-01-01T00:00:00Z"
        )

        coEvery { patientDao.getPatientById("p1") } returns cachedEntity

        val result = repository.getPatientById("p1")

        assertTrue(result.isSuccess)
        val patient = result.getOrThrow()
        assertNotNull(patient)
        assertEquals("Cached Patient", patient.fullName)
    }

    @Test
    fun `getPatientById returns null for unknown patient`() = runTest(testDispatcher) {
        coEvery { patientDao.getPatientById("unknown") } returns null

        val result = repository.getPatientById("unknown")

        assertTrue(result.isSuccess)
        assertEquals(null, result.getOrNull())
    }

    @Test
    fun `createPatient sends to API when online`() = runTest(testDispatcher) {
        val newPatient = Patient(
            id = null,
            fullName = "New Patient",
            phone = "07709876543",
            email = null,
            birthDate = "1995-03-20",
            gender = "female",
            nationalId = null,
            sndhsHealthId = null,
            familyId = null,
            address = "Basra",
            bloodType = "O+",
            notes = null
        )

        val createdDto = PatientDto(
            id = "p-new",
            fullName = "New Patient",
            phone = "07709876543",
            email = null,
            birthDate = "1995-03-20",
            gender = "female",
            nationalId = null,
            sndhsHealthId = null,
            familyId = null,
            address = "Basra",
            bloodType = "O+",
            notes = null,
            isActive = true,
            labId = "lab-1",
            createdAt = "2024-06-01T00:00:00Z",
            updatedAt = "2024-06-01T00:00:00Z"
        )

        coEvery { gulaApi.createPatient(any<PatientDto>()) } returns createdDto
        coEvery { patientDao.insertPatient(any<PatientEntity>()) } returns Unit

        val result = repository.createPatient(newPatient)

        assertTrue(result.isSuccess)
        val created = result.getOrThrow()
        assertEquals("p-new", created.id)

        coVerify {
            gulaApi.createPatient(any<PatientDto>())
            patientDao.insertPatient(any<PatientEntity>())
        }
    }

    @Test
    fun `updatePatient updates both API and cache`() = runTest(testDispatcher) {
        val updatedPatient = Patient(
            id = "p1",
            fullName = "Updated Name",
            phone = "07701111111",
            email = "updated@test.com",
            birthDate = "1990-01-01",
            gender = "male",
            nationalId = null,
            sndhsHealthId = null,
            familyId = null,
            address = "Updated Address",
            bloodType = null,
            notes = "Updated"
        )

        val updatedDto = PatientDto(
            id = "p1",
            fullName = "Updated Name",
            phone = "07701111111",
            email = "updated@test.com",
            birthDate = "1990-01-01",
            gender = "male",
            nationalId = null,
            sndhsHealthId = null,
            familyId = null,
            address = "Updated Address",
            bloodType = null,
            notes = "Updated",
            isActive = true,
            labId = "lab-1",
            createdAt = "2024-01-01T00:00:00Z",
            updatedAt = "2024-06-01T00:00:00Z"
        )

        coEvery { gulaApi.updatePatient(eq("p1"), any<PatientDto>()) } returns updatedDto
        coEvery { patientDao.updatePatient(any<PatientEntity>()) } returns Unit

        val result = repository.updatePatient(updatedPatient)

        assertTrue(result.isSuccess)

        coVerify {
            gulaApi.updatePatient(eq("p1"), any<PatientDto>())
            patientDao.updatePatient(any<PatientEntity>())
        }
    }

    @Test
    fun `searchPatients returns filtered results from cache`() = runTest(testDispatcher) {
        val searchResults = listOf(
            PatientEntity(
                id = "p1",
                fullName = "Ahmed Ali",
                phone = "07701111111",
                email = null,
                birthDate = "1985-05-10",
                gender = "male",
                nationalId = null,
                createdAt = "2024-01-01T00:00:00Z",
                updatedAt = "2024-01-01T00:00:00Z"
            )
        )

        coEvery { patientDao.searchPatients("Ahmed") } returns searchResults

        val result = repository.searchPatients("Ahmed")

        assertTrue(result.isSuccess)
        val patients = result.getOrThrow()
        assertEquals(1, patients.size)
        assertEquals("Ahmed Ali", patients[0].fullName)
    }

    @Test
    fun `getPatients handles API error gracefully by returning cached data`() = runTest(testDispatcher) {
        val cachedPatients = listOf(
            PatientEntity(
                id = "p1",
                fullName = "Fallback Patient",
                phone = "07701234567",
                email = null,
                birthDate = "1990-01-01",
                gender = "male",
                nationalId = null,
                createdAt = "2024-01-01T00:00:00Z",
                updatedAt = "2024-01-01T00:00:00Z"
            )
        )

        coEvery { gulaApi.getPatients(any(), any(), any()) } throws
            RuntimeException("Network error")
        coEvery { patientDao.getAllPatients() } returns cachedPatients

        val result = repository.getPatients(page = 0, pageSize = 20, query = null).first()

        assertTrue(result.isSuccess)
        val patients = result.getOrThrow()
        assertEquals(1, patients.size)
        assertEquals("Fallback Patient", patients[0].fullName)
    }
}
