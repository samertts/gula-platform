package io.gula.android.data.remote.api

import io.gula.android.data.remote.dto.*
import retrofit2.Response
import retrofit2.http.*

interface AuthApi {
    @POST("login")
    suspend fun login(@Body request: LoginRequestDto): Response<LoginResponseDto>

    @POST("logout")
    suspend fun logout(): Response<MessageResponseDto>

    @POST("auth/refresh")
    suspend fun refreshToken(@Body request: RefreshRequestDto): Response<RefreshResponseDto>

    @POST("auth/mfa/verify")
    suspend fun verifyMfa(@Body request: MfaVerifyRequestDto): Response<MfaVerifyResponseDto>

    @POST("auth/change-password")
    suspend fun changePassword(@Body request: ChangePasswordRequestDto): Response<MessageResponseDto>

    @POST("auth/password-reset")
    suspend fun requestPasswordReset(@Body request: PasswordResetRequestDto): Response<MessageResponseDto>

    @POST("auth/password-reset/confirm")
    suspend fun confirmPasswordReset(@Body request: PasswordResetConfirmDto): Response<MessageResponseDto>

    @GET("auth/me")
    suspend fun getCurrentUser(): Response<UserBriefDto>

    @POST("mobile/register-device")
    suspend fun registerDeviceToken(@Body request: DeviceTokenRequestDto): Response<MessageResponseDto>

    @POST("register")
    suspend fun registerLab(@Body request: LabRegisterRequestDto): Response<Map<String, Any>>

    @POST("register/staff")
    suspend fun registerStaff(@Body request: StaffRegisterRequestDto): Response<Map<String, Any>>
}
