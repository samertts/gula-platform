package io.gula.android.data.repository

import io.gula.android.data.local.UserDao
import io.gula.android.data.local.entity.UserEntity
import io.gula.android.data.remote.api.AuthApi
import io.gula.android.data.remote.dto.LoginRequestDto
import io.gula.android.data.remote.dto.LoginResponseDto
import io.gula.android.data.remote.dto.MfaRequestDto
import io.gula.android.data.remote.dto.MfaResponseDto
import io.gula.android.data.remote.dto.RegisterRequestDto
import io.gula.android.data.remote.dto.RegisterResponseDto
import io.gula.android.domain.model.AuthTokens
import io.gula.android.domain.model.LoginCredentials
import io.gula.android.domain.model.User
import io.gula.android.security.SecureStorage
import io.gula.android.util.NetworkMonitor
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import io.mockk.slot
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest
import org.junit.Before
import org.junit.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class AuthRepositoryImplTest {

    private lateinit var authApi: AuthApi
    private lateinit var userDao: UserDao
    private lateinit var secureStorage: SecureStorage
    private lateinit var networkMonitor: NetworkMonitor
    private lateinit var repository: AuthRepositoryImpl

    private val testDispatcher = StandardTestDispatcher()

    @Before
    fun setup() {
        authApi = mockk()
        userDao = mockk()
        secureStorage = mockk()
        networkMonitor = mockk()

        every { networkMonitor.isOnline } returns MutableStateFlow(true)

        repository = AuthRepositoryImpl(
            authApi = authApi,
            userDao = userDao,
            secureStorage = secureStorage,
            networkMonitor = networkMonitor,
            ioDispatcher = testDispatcher
        )
    }

    @Test
    fun `login success stores tokens and user`() = runTest(testDispatcher) {
        val credentials = LoginCredentials(
            email = "test@example.com",
            password = "password123"
        )
        val loginResponse = LoginResponseDto(
            accessToken = "access-token-123",
            refreshToken = "refresh-token-456",
            user = LoginResponseDto.UserDto(
                id = "user-1",
                email = "test@example.com",
                fullName = "Test User",
                role = "lab_tech",
                labId = "lab-1",
                isActive = true
            )
        )

        coEvery { authApi.login(any<LoginRequestDto>()) } returns loginResponse
        coEvery { userDao.insertUser(any()) } returns Unit
        coEvery { secureStorage.saveTokens(any(), any()) } returns Unit

        val result = repository.login(credentials)

        assertTrue(result.isSuccess)
        val user = result.getOrThrow()
        assertEquals("user-1", user.id)
        assertEquals("test@example.com", user.email)
        assertEquals("Test User", user.fullName)

        coVerify {
            authApi.login(LoginRequestDto(email = "test@example.com", password = "password123"))
            secureStorage.saveTokens("access-token-123", "refresh-token-456")
            userDao.insertUser(any())
        }
    }

    @Test
    fun `login with invalid credentials returns error`() = runTest(testDispatcher) {
        val credentials = LoginCredentials(
            email = "wrong@example.com",
            password = "wrongpass"
        )

        coEvery { authApi.login(any<LoginRequestDto>()) } throws
            retrofit2.HttpException(
                retrofit2.Response.error<Any>(
                    401,
                    okhttp3.ResponseBody.create(null, "{\"detail\":\"Invalid credentials\"}")
                )
            )

        val result = repository.login(credentials)

        assertTrue(result.isFailure)
        val exception = result.exceptionOrNull()
        assertNotNull(exception)
    }

    @Test
    fun `login with mfa required returns mfa needed`() = runTest(testDispatcher) {
        val credentials = LoginCredentials(
            email = "mfa@example.com",
            password = "password123"
        )

        coEvery { authApi.login(any<LoginRequestDto>()) } throws
            retrofit2.HttpException(
                retrofit2.Response.error<Any>(
                    428,
                    okhttp3.ResponseBody.create(null, "{\"detail\":\"MFA required\"}")
                )
            )

        val result = repository.login(credentials)

        assertTrue(result.isFailure)
    }

    @Test
    fun `verify mfa success completes authentication`() = runTest(testDispatcher) {
        val mfaCode = "123456"
        val mfaToken = "mfa-temp-token"
        val mfaResponse = MfaResponseDto(
            accessToken = "access-token-789",
            refreshToken = "refresh-token-012",
            user = MfaResponseDto.UserDto(
                id = "user-2",
                email = "mfa@example.com",
                fullName = "MFA User",
                role = "admin",
                labId = "lab-2",
                isActive = true
            )
        )

        coEvery { authApi.verifyMfa(any<MfaRequestDto>()) } returns mfaResponse
        coEvery { userDao.insertUser(any()) } returns Unit
        coEvery { secureStorage.saveTokens(any(), any()) } returns Unit

        val result = repository.verifyMfa(mfaCode, mfaToken)

        assertTrue(result.isSuccess)
        val user = result.getOrThrow()
        assertEquals("user-2", user.id)

        coVerify {
            authApi.verifyMfa(MfaRequestDto(code = mfaCode, mfaToken = mfaToken))
            secureStorage.saveTokens("access-token-789", "refresh-token-012")
        }
    }

    @Test
    fun `register creates account and logs in`() = runTest(testDispatcher) {
        val registerResponse = RegisterResponseDto(
            message = "Account created successfully",
            userId = "user-3"
        )
        val loginResponse = LoginResponseDto(
            accessToken = "access-new",
            refreshToken = "refresh-new",
            user = LoginResponseDto.UserDto(
                id = "user-3",
                email = "new@example.com",
                fullName = "New User",
                role = "lab_tech",
                labId = "lab-1",
                isActive = true
            )
        )

        val requestSlot = slot<RegisterRequestDto>()

        coEvery { authApi.register(capture(requestSlot)) } returns registerResponse
        coEvery { authApi.login(any<LoginRequestDto>()) } returns loginResponse
        coEvery { userDao.insertUser(any()) } returns Unit
        coEvery { secureStorage.saveTokens(any(), any()) } returns Unit

        val result = repository.register(
            fullName = "New User",
            email = "new@example.com",
            password = "securePass1",
            labName = "Test Lab",
            role = "lab_tech"
        )

        assertTrue(result.isSuccess)
        val user = result.getOrThrow()
        assertEquals("New User", user.fullName)

        assertEquals("new@example.com", requestSlot.captured.email)
        assertEquals("New User", requestSlot.captured.fullName)
        assertEquals("Test Lab", requestSlot.captured.labName)
    }

    @Test
    fun `checkAuth returns cached user when tokens exist`() = runTest(testDispatcher) {
        val cachedUser = UserEntity(
            id = "user-1",
            email = "test@example.com",
            fullName = "Test User",
            role = "lab_tech",
            labId = "lab-1",
            isActive = true
        )

        coEvery { secureStorage.getAccessToken() } returns "existing-token"
        coEvery { userDao.getUser() } returns cachedUser

        val result = repository.checkAuth()

        assertTrue(result.isSuccess)
        val user = result.getOrThrow()
        assertNotNull(user)
        assertEquals("user-1", user.id)
    }

    @Test
    fun `checkAuth returns null when no tokens`() = runTest(testDispatcher) {
        coEvery { secureStorage.getAccessToken() } returns null

        val result = repository.checkAuth()

        assertTrue(result.isSuccess)
        assertEquals(null, result.getOrNull())
    }

    @Test
    fun `logout clears all stored data`() = runTest(testDispatcher) {
        coEvery { secureStorage.clearAll() } returns Unit
        coEvery { userDao.clearUser() } returns Unit

        repository.logout()

        coVerify {
            secureStorage.clearAll()
            userDao.clearUser()
        }
    }
}
