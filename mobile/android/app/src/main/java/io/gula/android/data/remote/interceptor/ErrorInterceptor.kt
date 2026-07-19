package io.gula.android.data.remote.interceptor

import okhttp3.Interceptor
import okhttp3.Response
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ErrorInterceptor @Inject constructor() : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        var response: Response
        var attempt = 0
        val maxRetries = 3

        while (true) {
            try {
                response = chain.proceed(request)
            } catch (e: Exception) {
                if (attempt < maxRetries && isRetryable(e)) {
                    attempt++
                    val backoffMs = (1000L shl attempt.coerceAtMost(6)) +
                        (0..100).random().toLong()
                    Thread.sleep(backoffMs)
                    continue
                }
                throw e
            }

            if (response.isSuccessful) {
                return response
            }

            val shouldRetry = response.code in listOf(429, 500, 502, 503, 504) &&
                attempt < maxRetries

            if (shouldRetry && !request.method.equals("POST", ignoreCase = true)) {
                response.close()
                attempt++
                val backoffMs = (1000L shl attempt.coerceAtMost(6)) +
                    (0..100).random().toLong()
                Thread.sleep(backoffMs)
                continue
            }

            return response
        }
    }

    private fun isRetryable(e: Exception): Boolean {
        return e is IOException ||
            e.message?.contains("timeout", ignoreCase = true) == true ||
            e.message?.contains("time out", ignoreCase = true) == true ||
            e.message?.contains("reset", ignoreCase = true) == true
    }
}
