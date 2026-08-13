package io.gula.android.data.repository

import io.gula.android.data.local.dao.UserDao
import io.gula.android.data.remote.api.AuthApi
import io.gula.android.data.remote.dto.LoginRequestDto
import io.gula.android.data.remote.dto.LoginResponseDto
import io.gula.android.data.remote.dto.UserBriefDto
import io.gula.android.security.EncryptedPrefs
import io.gula.android.util.Resource
import io.mockk.Runs
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.just
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import retrofit2.Response

class AuthRepositoryImplTest {

    private lateinit var authApi: AuthApi
    private lateinit var userDao: UserDao
    private lateinit var encryptedPrefs: EncryptedPrefs
    private lateinit var repository: AuthRepositoryImpl

    @Before
    fun setup() {
        authApi = mockk()
        userDao = mockk()
        encryptedPrefs = mockk()

        every { encryptedPrefs.isLoggedIn } returns false
        every { encryptedPrefs.accessToken = any() } just Runs
        every { encryptedPrefs.refreshToken = any() } just Runs
        every { encryptedPrefs.userId = any() } just Runs
        every { encryptedPrefs.userEmail = any() } just Runs
        every { encryptedPrefs.userName = any() } just Runs
        every { encryptedPrefs.userRole = any() } just Runs
        every { encryptedPrefs.labId = any() } just Runs
        every { encryptedPrefs.mfaVerified = any() } just Runs
        every { encryptedPrefs.clearAll() } just Runs

        repository = AuthRepositoryImpl(
            authApi = authApi,
            userDao = userDao,
            encryptedPrefs = encryptedPrefs,
        )
    }

    @Test
    fun `login persists tokens and caches the authenticated user`() = runTest {
        val user = UserBriefDto(
            id = 7,
            email = "test@example.com",
            name = "Test User",
            role = "lab_tech",
            labId = 3,
        )
        val response = LoginResponseDto(
            accessToken = "access-token",
            refreshToken = "refresh-token",
            user = user,
        )
        coEvery { authApi.login(LoginRequestDto("test@example.com", "password123")) } returns Response.success(response)
        coEvery { userDao.insert(any()) } returns Unit

        val result = repository.login("test@example.com", "password123")

        assertTrue(result is Resource.Success)
        val tokens = (result as Resource.Success).data
        assertEquals("access-token", tokens.accessToken)
        assertEquals("refresh-token", tokens.refreshToken)
        coVerify(exactly = 1) { userDao.insert(match { it.id == 7 && it.email == "test@example.com" }) }
    }

    @Test
    fun `login returns a resource error for rejected credentials`() = runTest {
        coEvery { authApi.login(LoginRequestDto("wrong@example.com", "wrongpass")) } returns Response.error(
            401,
            "Unauthorized".toResponseBody("text/plain".toMediaType()),
        )

        val result = repository.login("wrong@example.com", "wrongpass")

        assertTrue(result is Resource.Error)
        assertEquals("Invalid email or password", (result as Resource.Error<*>).message)
    }

    @Test
    fun `biometric login reports a missing session when refresh credentials are absent`() = runTest {
        every { encryptedPrefs.accessToken } returns null
        every { encryptedPrefs.refreshToken } returns null

        val result = repository.loginWithBiometric()

        assertTrue(result is Resource.Error)
        assertEquals("No saved session", (result as Resource.Error<*>).message)
    }
}
