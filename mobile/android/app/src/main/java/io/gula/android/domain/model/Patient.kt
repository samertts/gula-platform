package io.gula.android.domain.model

data class Patient(
    val id: Int,
    val fullName: String,
    val phone: String,
    val birthDate: String? = null,
    val gender: String? = null,
    val email: String? = null,
    val labId: Int? = null,
    val nationalId: String? = null,
    val healthId: String? = null,
    val familyId: String? = null,
    val guardianId: Int? = null,
    val status: String? = null,
    val createdAt: String? = null,
    val updatedAt: String? = null,
) {
    val age: Int?
        get() {
            if (birthDate.isNullOrBlank()) return null
            return try {
                val parts = birthDate.split("-")
                if (parts.size != 3) return null
                val birthYear = parts[0].toInt()
                val birthMonth = parts[1].toInt()
                val birthDay = parts[2].toInt()
                val now = java.util.Calendar.getInstance()
                var age = now.get(java.util.Calendar.YEAR) - birthYear
                val currentMonth = now.get(java.util.Calendar.MONTH) + 1
                val currentDay = now.get(java.util.Calendar.DAY_OF_MONTH)
                if (currentMonth < birthMonth || (currentMonth == birthMonth && currentDay < birthDay)) {
                    age--
                }
                age
            } catch (e: Exception) { null }
        }
}

data class PatientCreateRequest(
    val fullName: String,
    val phone: String,
    val birthDate: String? = null,
    val gender: String? = null,
    val email: String? = null,
    val nationalId: String? = null,
    val familyId: String? = null,
    val forceCreate: Boolean = false,
    val guardianId: Int? = null,
)

data class PatientUpdateRequest(
    val fullName: String? = null,
    val phone: String? = null,
    val birthDate: String? = null,
    val gender: String? = null,
    val email: String? = null,
    val familyId: String? = null,
)
