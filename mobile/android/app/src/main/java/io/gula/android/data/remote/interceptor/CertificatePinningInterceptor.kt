package io.gula.android.data.remote.interceptor

import okhttp3.CertificatePinner
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CertificatePinningInterceptor @Inject constructor() {

    fun getCertificatePinner(): CertificatePinner {
        return CertificatePinner.Builder()
            .add("api.gulaplatform.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
            .add("staging.gulaplatform.com", "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=")
            .build()
    }

    companion object {
        val PINNED_DOMAINS = listOf(
            "api.gulaplatform.com",
            "staging.gulaplatform.com",
            "gulaplatform.com",
        )
    }
}
