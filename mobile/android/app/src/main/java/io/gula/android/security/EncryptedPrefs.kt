package io.gula.android.security

import android.content.Context
import android.content.SharedPreferences
import android.util.Base64
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import java.security.SecureRandom
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class EncryptedPrefs @Inject constructor(
    @ApplicationContext context: Context
) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val prefs: SharedPreferences = EncryptedSharedPreferences.create(
        context,
        PREFS_FILE,
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    var accessToken: String?
        get() = prefs.getString(KEY_ACCESS_TOKEN, null)
        set(value) = prefs.edit().putString(KEY_ACCESS_TOKEN, value).apply()

    var refreshToken: String?
        get() = prefs.getString(KEY_REFRESH_TOKEN, null)
        set(value) = prefs.edit().putString(KEY_REFRESH_TOKEN, value).apply()

    var userId: Int
        get() = prefs.getInt(KEY_USER_ID, -1)
        set(value) = prefs.edit().putInt(KEY_USER_ID, value).apply()

    var userEmail: String?
        get() = prefs.getString(KEY_USER_EMAIL, null)
        set(value) = prefs.edit().putString(KEY_USER_EMAIL, value).apply()

    var userName: String?
        get() = prefs.getString(KEY_USER_NAME, null)
        set(value) = prefs.edit().putString(KEY_USER_NAME, value).apply()

    var userRole: String?
        get() = prefs.getString(KEY_USER_ROLE, null)
        set(value) = prefs.edit().putString(KEY_USER_ROLE, value).apply()

    var labId: Int
        get() = prefs.getInt(KEY_LAB_ID, -1)
        set(value) = prefs.edit().putInt(KEY_LAB_ID, value).apply()

    var mfaEnabled: Boolean
        get() = prefs.getBoolean(KEY_MFA_ENABLED, false)
        set(value) = prefs.edit().putBoolean(KEY_MFA_ENABLED, value).apply()

    var mfaVerified: Boolean
        get() = prefs.getBoolean(KEY_MFA_VERIFIED, false)
        set(value) = prefs.edit().putBoolean(KEY_MFA_VERIFIED, value).apply()

    var isLoggedIn: Boolean
        get() = prefs.getBoolean(KEY_IS_LOGGED_IN, false)
        set(value) = prefs.edit().putBoolean(KEY_IS_LOGGED_IN, value).apply()

    var biometricEnabled: Boolean
        get() = prefs.getBoolean(KEY_BIOMETRIC_ENABLED, false)
        set(value) = prefs.edit().putBoolean(KEY_BIOMETRIC_ENABLED, value).apply()

    var deviceToken: String?
        get() = prefs.getString(KEY_DEVICE_TOKEN, null)
        set(value) = prefs.edit().putString(KEY_DEVICE_TOKEN, value).apply()

    val syncDeviceId: String
        get() = prefs.getString(KEY_SYNC_DEVICE_ID, null) ?: UUID.randomUUID().toString().also { id ->
            check(prefs.edit().putString(KEY_SYNC_DEVICE_ID, id).commit()) { "Unable to persist sync device identity" }
        }

    var syncCursor: String?
        get() = prefs.getString(KEY_SYNC_CURSOR, null)
        set(value) = prefs.edit().putString(KEY_SYNC_CURSOR, value).apply()

    val databaseEncryptionKey: String
        get() = getOrCreateKey(KEY_DATABASE_ENCRYPTION_KEY)

    val syncPayloadKey: String
        get() = getOrCreateKey(KEY_SYNC_PAYLOAD_KEY)

    private fun getOrCreateKey(keyName: String): String {
        prefs.getString(keyName, null)?.let { return it }
        val bytes = ByteArray(32)
        SecureRandom().nextBytes(bytes)
        val key = Base64.encodeToString(bytes, Base64.NO_WRAP)
        check(prefs.edit().putString(keyName, key).commit()) { "Unable to persist encrypted key" }
        return key
    }

    var locale: String
        get() = prefs.getString(KEY_LOCALE, "ar") ?: "ar"
        set(value) = prefs.edit().putString(KEY_LOCALE, value).apply()

    var darkMode: String
        get() = prefs.getString(KEY_DARK_MODE, "system") ?: "system"
        set(value) = prefs.edit().putString(KEY_DARK_MODE, value).apply()

    var accessibilityTextScale: Float
        get() = prefs.getFloat(KEY_ACCESSIBILITY_TEXT_SCALE, 1.0f)
        set(value) = prefs.edit().putFloat(KEY_ACCESSIBILITY_TEXT_SCALE, value.coerceIn(0.85f, 2.0f)).apply()

    var accessibilityHighContrast: Boolean
        get() = prefs.getBoolean(KEY_ACCESSIBILITY_HIGH_CONTRAST, false)
        set(value) = prefs.edit().putBoolean(KEY_ACCESSIBILITY_HIGH_CONTRAST, value).apply()

    var accessibilityReducedMotion: Boolean
        get() = prefs.getBoolean(KEY_ACCESSIBILITY_REDUCED_MOTION, false)
        set(value) = prefs.edit().putBoolean(KEY_ACCESSIBILITY_REDUCED_MOTION, value).apply()

    var accessibilityScreenReader: Boolean
        get() = prefs.getBoolean(KEY_ACCESSIBILITY_SCREEN_READER, false)
        set(value) = prefs.edit().putBoolean(KEY_ACCESSIBILITY_SCREEN_READER, value).apply()

    var accessibilityLargerTouchTargets: Boolean
        get() = prefs.getBoolean(KEY_ACCESSIBILITY_LARGER_TOUCH_TARGETS, false)
        set(value) = prefs.edit().putBoolean(KEY_ACCESSIBILITY_LARGER_TOUCH_TARGETS, value).apply()

    var accessibilityColorBlindMode: String
        get() = prefs.getString(KEY_ACCESSIBILITY_COLOR_BLIND_MODE, "none") ?: "none"
        set(value) = prefs.edit().putString(KEY_ACCESSIBILITY_COLOR_BLIND_MODE, value).apply()

    fun clearAll() {
        val preservedKeys = listOf(
            KEY_SYNC_DEVICE_ID,
            KEY_SYNC_CURSOR,
            KEY_SYNC_PAYLOAD_KEY,
            KEY_DATABASE_ENCRYPTION_KEY,
        )
        val preserved = preservedKeys.mapNotNull { key -> prefs.getString(key, null)?.let { key to it } }
        val editor = prefs.edit().clear()
        preserved.forEach { (key, value) -> editor.putString(key, value) }
        editor.commit()
    }

    companion object {
        private const val PREFS_FILE = "gula_encrypted_prefs"
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
        private const val KEY_USER_ID = "user_id"
        private const val KEY_USER_EMAIL = "user_email"
        private const val KEY_USER_NAME = "user_name"
        private const val KEY_USER_ROLE = "user_role"
        private const val KEY_LAB_ID = "lab_id"
        private const val KEY_MFA_ENABLED = "mfa_enabled"
        private const val KEY_MFA_VERIFIED = "mfa_verified"
        private const val KEY_IS_LOGGED_IN = "is_logged_in"
        private const val KEY_BIOMETRIC_ENABLED = "biometric_enabled"
        private const val KEY_DEVICE_TOKEN = "device_token"
        private const val KEY_SYNC_DEVICE_ID = "sync_device_id"
        private const val KEY_SYNC_CURSOR = "sync_cursor"
        private const val KEY_SYNC_PAYLOAD_KEY = "sync_payload_key"
        private const val KEY_DATABASE_ENCRYPTION_KEY = "database_encryption_key"
        private const val KEY_LOCALE = "locale"
        private const val KEY_DARK_MODE = "dark_mode"
        private const val KEY_ACCESSIBILITY_TEXT_SCALE = "accessibility_text_scale"
        private const val KEY_ACCESSIBILITY_HIGH_CONTRAST = "accessibility_high_contrast"
        private const val KEY_ACCESSIBILITY_REDUCED_MOTION = "accessibility_reduced_motion"
        private const val KEY_ACCESSIBILITY_SCREEN_READER = "accessibility_screen_reader"
        private const val KEY_ACCESSIBILITY_LARGER_TOUCH_TARGETS = "accessibility_larger_touch_targets"
        private const val KEY_ACCESSIBILITY_COLOR_BLIND_MODE = "accessibility_color_blind_mode"
    }
}
