package io.gula.android.util

import androidx.room.TypeConverter
import java.util.Date

class DateConverters {
    @TypeConverter
    fun fromTimestamp(value: Long?): Date? {
        return value?.let { Date(it) }
    }

    @TypeConverter
    fun dateToTimestamp(date: Date?): Long? {
        return date?.time
    }

    @TypeConverter
    fun fromStringList(value: String?): List<String>? {
        if (value == null) return null
        return value.split(",").map { it.trim() }.filter { it.isNotEmpty() }
    }

    @TypeConverter
    fun toStringList(list: List<String>?): String? {
        return list?.joinToString(",")
    }

    @TypeConverter
    fun fromMapStringString(value: String?): Map<String, String>? {
        if (value == null) return null
        return value.split("&").mapNotNull { entry ->
            val parts = entry.split("=", limit = 2)
            if (parts.size == 2) parts[0] to parts[1] else null
        }.toMap()
    }

    @TypeConverter
    fun toStringMapStringString(map: Map<String, String>?): String? {
        return map?.entries?.joinToString("&") { "${it.key}=${it.value}" }
    }
}
