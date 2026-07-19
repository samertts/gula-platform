package io.gula.android.security

import android.content.Context
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.biometric.BiometricManager.Authenticators
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BiometricAuth @Inject constructor(
    @ApplicationContext private val context: Context
) {
    fun isAvailable(): Boolean {
        val manager = BiometricManager.from(context)
        return manager.canAuthenticate(
            Authenticators.BIOMETRIC_WEAK or Authenticators.DEVICE_CREDENTIAL
        ) == BiometricManager.BIOMETRIC_SUCCESS
    }

    fun authenticate(activity: FragmentActivity, title: String, subtitle: String): Flow<BiometricResult> = callbackFlow {
        val executor = ContextCompat.getMainExecutor(context)
        val callback = object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                trySend(BiometricResult.Success(result.cryptoObject?.cipher?.let {
                    try {
                        (it as? javax.crypto.Cipher)?.let { cipher ->
                            cipher.doFinal()
                        }
                    } catch (e: Exception) { null }
                }))
            }

            override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                trySend(BiometricResult.Error(errorCode, errString.toString()))
                close()
            }

            override fun onAuthenticationFailed() {
                trySend(BiometricResult.Failed)
            }
        }

        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle(title)
            .setSubtitle(subtitle)
            .setAllowedAuthenticators(
                Authenticators.BIOMETRIC_WEAK or Authenticators.DEVICE_CREDENTIAL
            )
            .build()

        val biometricPrompt = BiometricPrompt(activity, executor, callback)
        biometricPrompt.authenticate(promptInfo)

        awaitClose { }
    }
}

sealed class BiometricResult {
    data class Success(val cryptoObject: ByteArray?) : BiometricResult()
    data class Error(val code: Int, val message: String) : BiometricResult()
    data object Failed : BiometricResult()
}
