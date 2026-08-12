package io.gula.android.util

import java.text.SimpleDateFormat
import java.time.Instant
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.YearMonth
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Date
import java.util.Locale

object DateUtils {
    private val apiFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
    private val apiFormatWithZone = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US)
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.US)
    private val displayDateFormat = SimpleDateFormat("dd/MM/yyyy", Locale.US)
    private val displayDateTimeFormat = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.US)
    private val timeFormat = SimpleDateFormat("HH:mm", Locale.US)

    fun parseApiDate(dateStr: String?): Date? {
        if (dateStr.isNullOrBlank()) return null
        return try {
            apiFormatWithZone.parse(dateStr) ?: apiFormat.parse(dateStr)
        } catch (e: Exception) {
            try {
                apiFormat.parse(dateStr)
            } catch (e2: Exception) {
                null
            }
        }
    }

    fun formatToApiDate(date: Date): String = apiFormat.format(date)

    fun formatToDisplayDate(date: Date?, locale: Locale = Locale.getDefault()): String {
        if (date == null) return ""
        val formatter = DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM).withLocale(locale)
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDate().format(formatter)
    }

    fun formatToDisplayDateTime(date: Date?, locale: Locale = Locale.getDefault()): String {
        if (date == null) return ""
        val formatter = DateTimeFormatter.ofLocalizedDateTime(FormatStyle.SHORT).withLocale(locale)
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime().format(formatter)
    }

    fun formatDate(date: Date?): String = date?.let { displayDateFormat.format(it) } ?: ""
    fun formatDateTime(date: Date?): String = date?.let { displayDateTimeFormat.format(it) } ?: ""
    fun formatTime(date: Date?): String = date?.let { timeFormat.format(it) } ?: ""

    fun formatRelativeTime(date: Date?, locale: Locale = Locale.getDefault()): String {
        if (date == null) return ""
        val now = Date()
        val diff = now.time - date.time
        val seconds = diff / 1000
        val minutes = seconds / 60
        val hours = minutes / 60
        val days = hours / 24

        return when {
            seconds < 60 -> when (locale.language) {
                "ar" -> "الآن"
                else -> "now"
            }
            minutes < 60 -> when (locale.language) {
                "ar" -> "منذ $minutes دقيقة"
                else -> "$minutes min ago"
            }
            hours < 24 -> when (locale.language) {
                "ar" -> "منذ $hours ساعة"
                else -> "$hours hours ago"
            }
            days < 7 -> when (locale.language) {
                "ar" -> "منذ $days يوم"
                else -> "$days days ago"
            }
            else -> formatDate(date)
        }
    }

    fun toDate(localDate: LocalDate): Date = Date.from(localDate.atStartOfDay(ZoneId.systemDefault()).toInstant())
    fun toLocalDate(date: Date): LocalDate = date.toInstant().atZone(ZoneId.systemDefault()).toLocalDate()

    fun getAge(birthDate: String?): Int? {
        if (birthDate.isNullOrBlank()) return null
        return try {
            val date = dateFormat.parse(birthDate) ?: return null
            val birthLocal = toLocalDate(date)
            val now = LocalDate.now()
            now.year - birthLocal.year - if (now.dayOfYear < birthLocal.dayOfYear) 1 else 0
        } catch (e: Exception) {
            null
        }
    }

    fun isValidDate(dateStr: String): Boolean {
        return try {
            dateFormat.parse(dateStr)
            true
        } catch (e: Exception) {
            false
        }
    }

    fun getCurrentDateTime(): String = apiFormat.format(Date())

    fun getStartOfDay(date: Date): Date {
        val local = toLocalDate(date)
        return toDate(local)
    }

    fun getEndOfDay(date: Date): Date {
        val local = toLocalDate(date)
        return Date.from(local.plusDays(1).atStartOfDay(ZoneId.systemDefault()).minusSeconds(1).toInstant())
    }
}
