package io.gula.android.security

import android.content.Context
import android.os.Build
import java.io.File
import java.security.MessageDigest
import java.security.cert.CertificateFactory
import java.security.cert.X509Certificate
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SecurityUtils @Inject constructor(
    private val context: Context
) {
    fun isRootDetected(): Boolean {
        val knownPaths = listOf(
            "/system/app/Superuser.apk",
            "/sbin/su",
            "/system/bin/su",
            "/system/xbin/su",
            "/data/local/xbin/su",
            "/data/local/bin/su",
            "/system/sd/xbin/su",
            "/system/bin/failsafe/su",
            "/data/local/su",
            "/su/bin/su"
        )
        return knownPaths.any { File(it).exists() } ||
            checkBuildTags() ||
            checkMagisk() ||
            checkRootCloakingApps()
    }

    fun isEmulator(): Boolean {
        return (Build.FINGERPRINT.startsWith("generic") ||
            Build.FINGERPRINT.startsWith("unknown") ||
            Build.MODEL.contains("google_sdk") ||
            Build.MODEL.contains("Emulator") ||
            Build.MODEL.contains("Android SDK built for x86") ||
            Build.MANUFACTURER.contains("Genymotion") ||
            Build.HARDWARE.contains("goldfish") ||
            Build.HARDWARE.contains("ranchu") ||
            Build.PRODUCT.contains("sdk") ||
            Build.PRODUCT.contains("vbox86p") ||
            Build.PRODUCT.contains("emulator") ||
            Build.PRODUCT.contains("simulator") ||
            Build.BOARD.lowercase().contains("nox") ||
            Build.BOOTLOADER.lowercase().contains("nox") ||
            Build.HARDWARE.lowercase().contains("nox") ||
            Build.SERIAL.lowercase().contains("nox"))
    }

    fun validateCertificate(certPem: String): Boolean {
        return try {
            val factory = CertificateFactory.getInstance("X.509")
            val cert = factory.generateCertificate(certPem.byteInputStream()) as X509Certificate
            cert.checkValidity()
            true
        } catch (e: Exception) {
            false
        }
    }

    fun hashString(input: String, algorithm: String = "SHA-256"): String {
        return MessageDigest.getInstance(algorithm)
            .digest(input.toByteArray())
            .joinToString("") { "%02x".format(it) }
    }

    private fun checkBuildTags(): Boolean {
        return Build.TAGS?.contains("test-keys") == true
    }

    private fun checkMagisk(): Boolean {
        return try {
            val paths = listOf(
                "/data/adb/magisk",
                "/data/adb/magisk.db",
                "/data/adb/magisk.img",
            )
            paths.any { File(it).exists() }
        } catch (e: Exception) {
            false
        }
    }

    private fun checkRootCloakingApps(): Boolean {
        return try {
            val packages = context.packageManager.getInstalledApplications(0)
            packages.any { pkg ->
                val name = pkg.packageName.lowercase()
                name.contains("root") || name.contains("supersu") ||
                    name.contains("magisk") || name.contains("xposed")
            }
        } catch (e: Exception) {
            false
        }
    }
}
