package io.gula.android.data.repository

inline fun parseError(code: Int, errorBody: String?): String {
    return when (code) {
        400 -> "Invalid request"
        401 -> "Unauthorized"
        403 -> "Access denied"
        404 -> "Resource not found"
        409 -> "Resource already exists"
        422 -> "Validation error"
        429 -> "Too many requests. Please try again later."
        500, 502, 503 -> "Server error. Please try again later."
        else -> errorBody ?: "Unknown error"
    }
}
