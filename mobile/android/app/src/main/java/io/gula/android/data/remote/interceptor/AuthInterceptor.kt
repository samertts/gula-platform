package io.gula.android.data.remote.interceptor

import io.gula.android.security.EncryptedPrefs
import kotlinx.coroutines.runBlocking
import okhttp3.Authenticator
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route
import org.json.JSONObject
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthInterceptor @Inject constructor(
    private val encryptedPrefs: EncryptedPrefs,
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val token = encryptedPrefs.accessToken

        if (token.isNullOrBlank()) {
            return chain.proceed(originalRequest)
        }

        val authenticatedRequest = originalRequest.newBuilder()
            .header("Authorization", "Bearer $token")
            .build()

        val response = chain.proceed(authenticatedRequest)

        if (response.code == 401) {
            response.close()
            val newToken = refreshTokenSync()
            if (newToken != null) {
                val retryRequest = originalRequest.newBuilder()
                    .header("Authorization", "Bearer $newToken")
                    .build()
                return chain.proceed(retryRequest)
            }
            encryptedPrefs.clearAll()
        }

        return response
    }

    private fun refreshTokenSync(): String? {
        return runBlocking {
            val refreshToken = encryptedPrefs.refreshToken ?: return@runBlocking null
            try {
                val client = OkHttpClient.Builder().build()
                val json = JSONObject().apply {
                    put("refresh_token", refreshToken)
                }
                val body = okhttp3.RequestBody.create(
                    okhttp3.MediaType.parse("application/json"),
                    json.toString()
                )
                val request = Request.Builder()
                    .url("${BASE_URL}auth/refresh")
                    .post(body)
                    .build()
                val response = client.newCall(request).execute()
                if (response.isSuccessful) {
                    val bodyStr = response.body()?.string()
                    val jsonResponse = JSONObject(bodyStr)
                    val newAccessToken = jsonResponse.optString("access_token")
                    val newRefreshToken = jsonResponse.optString("refresh_token")
                    if (newAccessToken.isNotBlank()) {
                        encryptedPrefs.accessToken = newAccessToken
                        if (newRefreshToken.isNotBlank()) {
                            encryptedPrefs.refreshToken = newRefreshToken
                        }
                        return@runBlocking newAccessToken
                    }
                }
                null
            } catch (e: Exception) {
                null
            }
        }
    }

    companion object {
        private const val BASE_URL = "https://api.gulaplatform.com/api/v1/"
    }
}

@Singleton
class TokenAuthenticator @Inject constructor(
    private val encryptedPrefs: EncryptedPrefs,
) : Authenticator {
    override fun authenticate(route: Route?, response: Response): Request? {
        val refreshToken = encryptedPrefs.refreshToken ?: return null
        synchronized(this) {
            val currentToken = encryptedPrefs.accessToken
            if (currentToken != null && !response.request.header("Authorization").isNullOrBlank()) {
                val headerToken = response.request.header("Authorization")!!.removePrefix("Bearer ")
                if (headerToken == currentToken) {
                    return try {
                        val client = OkHttpClient.Builder().build()
                        val json = JSONObject().apply { put("refresh_token", refreshToken) }
                        val body = okhttp3.RequestBody.create(
                            okhttp3.MediaType.parse("application/json"),
                            json.toString()
                        )
                        val refreshRequest = Request.Builder()
                            .url("${response.request.url.scheme()}://${response.request.url.host()}/auth/refresh")
                            .post(body)
                            .build()
                        val refreshResponse = client.newCall(refreshRequest).execute()
                        if (refreshResponse.isSuccessful) {
                            val bodyStr = refreshResponse.body()?.string()
                            val jsonResponse = JSONObject(bodyStr)
                            val newAccessToken = jsonResponse.optString("access_token")
                            if (newAccessToken.isNotBlank()) {
                                encryptedPrefs.accessToken = newAccessToken
                                return response.request.newBuilder()
                                    .header("Authorization", "Bearer $newAccessToken")
                                    .build()
                            }
                        }
                        null
                    } catch (e: Exception) {
                        null
                    }
                }
            }
            return null
        }
    }
}
