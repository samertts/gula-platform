package io.gula.android.data.remote.interceptor

import okhttp3.CertificatePinner
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CertificatePinningInterceptor @Inject constructor() {

    fun getCertificatePinner(): CertificatePinner {
        // This is the SPKI pin observed for api.gula-platform.org on 2026-08-12.
        // Rotate this pin before the certificate expires and add a verified backup
        // pin before changing the production certificate or CA chain.
        return CertificatePinner.Builder()
            .add("api.gula-platform.org", "sha256/g9F05XEMwoJmxPy/otHWQ4jyLsg5jcPWyh4PYBrOEM0=")
            .build()
    }

    companion object {
        val PINNED_DOMAINS = listOf("api.gula-platform.org")
    }
}
