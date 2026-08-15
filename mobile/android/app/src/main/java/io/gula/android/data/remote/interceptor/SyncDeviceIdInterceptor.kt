package io.gula.android.data.remote.interceptor

import io.gula.android.security.EncryptedPrefs
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SyncDeviceIdInterceptor @Inject constructor(
    private val encryptedPrefs: EncryptedPrefs,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request().newBuilder()
            .header("X-Sync-Device-ID", encryptedPrefs.syncDeviceId)
            .build()
        return chain.proceed(request)
    }
}
