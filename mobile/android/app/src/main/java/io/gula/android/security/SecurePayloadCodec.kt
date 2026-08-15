package io.gula.android.security

import android.util.Base64
import java.nio.charset.StandardCharsets
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SecurePayloadCodec @Inject constructor(
    private val encryptedPrefs: EncryptedPrefs,
) {
    private val random = SecureRandom()

    fun encrypt(plaintext: String): String {
        val iv = ByteArray(IV_BYTES)
        random.nextBytes(iv)
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, key(), GCMParameterSpec(TAG_BITS, iv))
        val ciphertext = cipher.doFinal(plaintext.toByteArray(StandardCharsets.UTF_8))
        val packed = ByteArray(iv.size + ciphertext.size)
        iv.copyInto(packed, 0)
        ciphertext.copyInto(packed, iv.size)
        return "$PREFIX${Base64.encodeToString(packed, Base64.NO_WRAP)}"
    }

    fun decrypt(value: String): String {
        if (!value.startsWith(PREFIX)) return value
        val packed = Base64.decode(value.removePrefix(PREFIX), Base64.NO_WRAP)
        require(packed.size > IV_BYTES) { "Encrypted sync payload is malformed" }
        val iv = packed.copyOfRange(0, IV_BYTES)
        val ciphertext = packed.copyOfRange(IV_BYTES, packed.size)
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(TAG_BITS, iv))
        return String(cipher.doFinal(ciphertext), StandardCharsets.UTF_8)
    }

    fun isEncrypted(value: String): Boolean = value.startsWith(PREFIX)

    private fun key(): SecretKeySpec {
        val encoded = Base64.decode(encryptedPrefs.syncPayloadKey, Base64.NO_WRAP)
        require(encoded.size == KEY_BYTES) { "Sync payload key must be 256 bits" }
        return SecretKeySpec(encoded, "AES")
    }

    companion object {
        private const val PREFIX = "v1:"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
        private const val IV_BYTES = 12
        private const val TAG_BITS = 128
        private const val KEY_BYTES = 32
    }
}
