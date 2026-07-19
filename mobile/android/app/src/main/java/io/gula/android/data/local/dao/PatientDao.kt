package io.gula.android.data.local.dao

import androidx.room.*
import io.gula.android.data.local.entity.PatientEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface PatientDao {
    @Query("""
        SELECT * FROM patients 
        WHERE (:search IS NULL OR full_name LIKE '%' || :search || '%' OR phone LIKE '%' || :search || '%')
        ORDER BY full_name ASC 
        LIMIT :limit OFFSET :offset
    """)
    fun getPatients(search: String? = null, limit: Int = 20, offset: Int = 0): Flow<List<PatientEntity>>

    @Query("SELECT * FROM patients WHERE id = :id")
    fun getPatientById(id: Int): Flow<PatientEntity?>

    @Query("SELECT * FROM patients WHERE family_id = :familyId")
    fun getPatientsByFamilyId(familyId: String): Flow<List<PatientEntity>>

    @Query("SELECT * FROM patients WHERE phone = :phone LIMIT 1")
    suspend fun getPatientByPhone(phone: String): PatientEntity?

    @Query("SELECT * FROM patients WHERE full_name LIKE '%' || :query || '%' OR phone LIKE '%' || :query || '%' OR national_id LIKE '%' || :query || '%'")
    suspend fun searchPatients(query: String): List<PatientEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(patients: List<PatientEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(patient: PatientEntity)

    @Update
    suspend fun update(patient: PatientEntity)

    @Delete
    suspend fun delete(patient: PatientEntity)

    @Query("DELETE FROM patients WHERE id = :id")
    suspend fun deleteById(id: Int)

    @Query("DELETE FROM patients")
    suspend fun deleteAll()

    @Query("SELECT COUNT(*) FROM patients")
    fun getCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM patients WHERE (:search IS NULL OR full_name LIKE '%' || :search || '%' OR phone LIKE '%' || :search || '%')")
    suspend fun getFilteredCount(search: String? = null): Int

    @Query("UPDATE patients SET synced_at = :syncedAt WHERE id = :id")
    suspend fun updateSyncStatus(id: Int, syncedAt: Long)
}
