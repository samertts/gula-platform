package io.gula.android.util

import android.content.Context
import android.content.res.Configuration
import android.os.Build
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class LocaleManager @Inject constructor() {

    fun setLocale(context: Context, languageCode: String): Context {
        val locale = when (languageCode) {
            "ar" -> Locale("ar")
            "en" -> Locale("en")
            else -> Locale("ar")
        }
        Locale.setDefault(locale)
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            updateConfiguration(context, locale)
        } else {
            @Suppress("DEPRECATION")
            updateConfigurationLegacy(context, locale)
        }
    }

    fun getCurrentLocale(context: Context): Locale {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            context.resources.configuration.locales[0]
        } else {
            @Suppress("DEPRECATION")
            context.resources.configuration.locale
        }
    }

    fun isRtl(locale: Locale = Locale.getDefault()): Boolean {
        return locale.language == "ar" ||
            Character.getDirectionality(locale.displayName[0]) ==
            Character.DIRECTIONALITY_RIGHT_TO_LEFT
    }

    private fun updateConfiguration(context: Context, locale: Locale): Context {
        val configuration = Configuration(context.resources.configuration)
        configuration.setLocale(locale)
        return context.createConfigurationContext(configuration)
    }

    @Suppress("DEPRECATION")
    private fun updateConfigurationLegacy(context: Context, locale: Locale): Context {
        val configuration = Configuration(context.resources.configuration)
        configuration.locale = locale
        context.resources.updateConfiguration(configuration, context.resources.displayMetrics)
        return context
    }
}
