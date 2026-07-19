package io.gula.android.data.local

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import io.gula.android.data.local.dao.PatientDao
import io.gula.android.data.local.entity.PatientEntity
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull

@RunWith(AndroidJUnit4::class)
class PatientDaoTest {

    private lateinit var database: GulaDatabase
    private lateinit var patientDao: PatientDao

    @Before
    fun setup() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(
            context,
            GulaDatabase::class.java
        ).allowMainThreadQueries().build()
        patientDao = database.patientDao()
    }

    @After
    fun teardown() {
        database.close()
    }

    @Test
    fun insertAndRetrievePatient() = runBlocking {
        val patient = PatientEntity(
            id = "test-1",
            fullName = "Test Patient",
            phone = "07701234567",
            email = "test@test.com",
            birthDate = "1990-01-15",
            gender = "male",
            nationalId = null,
            createdAt = "2024-01-01T00:00:00Z",
            updatedAt = "2024-01-01T00:00:00Z"
        )

        patientDao.insertPatient(patient)
        val retrieved = patientDao.getPatientById("test-1")

        assertNotNull(retrieved)
        assertEquals("Test Patient", retrieved.fullName)
        assertEquals("07701234567", retrieved.phone)
        assertEquals("test@test.com", retrieved.email)
        assertEquals("1990-01-15", retrieved.birthDate)
        assertEquals("male", retrieved.gender)
    }

    @Test
    fun insertAllAndGetAllPatients() = runBlocking {
        val patients = listOf(
            PatientEntity(
                id = "p1", fullName = "Ali Ahmed", phone = "07701111111",
                birthDate = "1985-03-10", gender = "male",
                createdAt = "2024-01-01T00:00:00Z", updatedAt = "2024-01-01T00:00:00Z"
            ),
            PatientEntity(
                id = "p2", fullName = "Sara Ali", phone = "07702222222",
                birthDate = "1992-07-22", gender = "female",
                createdAt = "2024-01-02T00:00:00Z", updatedAt = "2024-01-02T00:00:00Z"
            ),
            PatientEntity(
                id = "p3", fullName = "Omar Hassan", phone = "07703333333",
                birthDate = "1978-11-05", gender = "male",
                createdAt = "2024-01-03T00:00:00Z", updatedAt = "2024-01-03T00:00:00Z"
            )
        )

        patientDao.insertAll(patients)
        val allPatients = patientDao.getAllPatients()

        assertEquals(3, allPatients.size)
        assertEquals("Ali Ahmed", allPatients[0].fullName)
    }

    @Test
    fun searchPatientsByName() = runBlocking {
        val patients = listOf(
            PatientEntity(
                id = "p1", fullName = "Ahmed Mohammed", phone = "07701111111",
                birthDate = "1990-01-01", gender = "male",
                createdAt = "2024-01-01T00:00:00Z", updatedAt = "2024-01-01T00:00:00Z"
            ),
            PatientEntity(
                id = "p2", fullName = "Ahmed Ali", phone = "07702222222",
                birthDate = "1992-07-22", gender = "male",
                createdAt = "2024-01-02T00:00:00Z", updatedAt = "2024-01-02T00:00:00Z"
            ),
            PatientEntity(
                id = "p3", fullName = "Sara Khalid", phone = "07703333333",
                birthDate = "1988-05-15", gender = "female",
                createdAt = "2024-01-03T00:00:00Z", updatedAt = "2024-01-03T00:00:00Z"
            )
        )

        patientDao.insertAll(patients)
        val results = patientDao.searchPatients("Ahmed")

        assertEquals(2, results.size)
        assert(results.all { it.fullName.contains("Ahmed") })
    }

    @Test
    fun searchPatientsByPhone() = runBlocking {
        val patients = listOf(
            PatientEntity(
                id = "p1", fullName = "Test One", phone = "07701111111",
                birthDate = "1990-01-01", gender = "male",
                createdAt = "2024-01-01T00:00:00Z", updatedAt = "2024-01-01T00:00:00Z"
            )
        )

        patientDao.insertAll(patients)
        val results = patientDao.searchPatients("07701111111")

        assertEquals(1, results.size)
        assertEquals("Test One", results[0].fullName)
    }

    @Test
    fun updatePatient() = runBlocking {
        val patient = PatientEntity(
            id = "p1", fullName = "Original Name", phone = "07701111111",
            birthDate = "1990-01-01", gender = "male",
            createdAt = "2024-01-01T00:00:00Z", updatedAt = "2024-01-01T00:00:00Z"
        )

        patientDao.insertPatient(patient)

        val updatedPatient = patient.copy(
            fullName = "Updated Name",
            phone = "07709999999",
            updatedAt = "2024-06-01T00:00:00Z"
        )
        patientDao.updatePatient(updatedPatient)

        val retrieved = patientDao.getPatientById("p1")
        assertNotNull(retrieved)
        assertEquals("Updated Name", retrieved.fullName)
        assertEquals("07709999999", retrieved.phone)
    }

    @Test
    fun deletePatient() = runBlocking {
        val patient = PatientEntity(
            id = "p1", fullName = "To Delete", phone = "07701111111",
            birthDate = "1990-01-01", gender = "male",
            createdAt = "2024-01-01T00:00:00Z", updatedAt = "2024-01-01T00:00:00Z"
        )

        patientDao.insertPatient(patient)
        patientDao.deletePatient(patient)

        val retrieved = patientDao.getPatientById("p1")
        assertNull(retrieved)
    }

    @Test
    fun getAllPatientsFlow() = runBlocking {
        val patient = PatientEntity(
            id = "p1", fullName = "Flow Patient", phone = "07701111111",
            birthDate = "1990-01-01", gender = "male",
            createdAt = "2024-01-01T00:00:00Z", updatedAt = "2024-01-01T00:00:00Z"
        )

        patientDao.insertPatient(patient)

        val patients = patientDao.getAllPatientsFlow().first()
        assertEquals(1, patients.size)
        assertEquals("Flow Patient", patients[0].fullName)
    }

    @Test
    fun searchPatientsReturnsEmptyForNoMatch() = runBlocking {
        val patient = PatientEntity(
            id = "p1", fullName = "Unique Name", phone = "07701111111",
            birthDate = "1990-01-01", gender = "male",
            createdAt = "2024-01-01T00:00:00Z", updatedAt = "2024-01-01T00:00:00Z"
        )

        patientDao.insertPatient(patient)
        val results = patientDao.searchPatients("NonExistent")

        assert(results.isEmpty())
    }

    @Test
    fun insertAllReplacesExistingOnConflict() = runBlocking {
        val original = PatientEntity(
            id = "p1", fullName = "Original", phone = "07701111111",
            birthDate = "1990-01-01", gender = "male",
            createdAt = "2024-01-01T00:00:00Z", updatedAt = "2024-01-01T00:00:00Z"
        )

        patientDao.insertPatient(original)

        val replacement = listOf(
            PatientEntity(
                id = "p1", fullName = "Replacement", phone = "07709999999",
                birthDate = "1990-01-01", gender = "male",
                createdAt = "2024-01-01T00:00:00Z", updatedAt = "2024-06-01T00:00:00Z"
            )
        )

        patientDao.insertAll(replacement)

        val retrieved = patientDao.getPatientById("p1")
        assertNotNull(retrieved)
        assertEquals("Replacement", retrieved.fullName)
        assertEquals("07709999999", retrieved.phone)
    }
}
