package io.gula.android.domain.usecase

import io.gula.android.domain.model.AuthTokens
import io.gula.android.domain.repository.AuthRepository
import io.gula.android.util.Resource
import javax.inject.Inject

class LoginUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(email: String, password: String): Resource<AuthTokens> {
        if (email.isBlank()) return Resource.error("Email is required")
        if (password.isBlank()) return Resource.error("Password is required")
        if (password.length < 6) return Resource.error("Password must be at least 6 characters")
        return authRepository.login(email, password)
    }
}
