package io.gula.android.security

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
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

    var locale: String
        get() = prefs.getString(KEY_LOCALE, "ar") ?: "ar"
        set(value) = prefs.edit().putString(KEY_LOCALE, value).apply()

    var darkMode: String
        get() = prefs.getString(KEY_DARK_MODE, "system") ?: "system"
        set(value) = prefs.edit().putString(KEY_DARK_MODE, value).apply()

    fun clearAll() {
        prefs.edit().clear().apply()
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
        private const val KEY_LOCALE = "locale"
        private const val KEY_DARK_MODE = "dark_mode"
    }
}
