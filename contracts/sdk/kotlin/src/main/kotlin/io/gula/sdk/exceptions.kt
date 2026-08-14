package io.gula.sdk

open class GulaException(
    message: String,
    cause: Throwable? = null,
) : Exception(message, cause)

open class GulaAuthException(
    message: String = "Authentication failed",
    cause: Throwable? = null,
) : GulaException(message, cause)

class GulaTokenExpiredException(
    message: String = "Access token has expired",
    cause: Throwable? = null,
) : GulaAuthException(message, cause)

class GulaRefreshFailedException(
    message: String = "Failed to refresh access token",
    cause: Throwable? = null,
) : GulaAuthException(message, cause)

class GulaNotFoundException(
    val resourceType: String,
    val resourceId: Any? = null,
    message: String? = null,
    cause: Throwable? = null,
) : GulaException(
    message ?: "$resourceType${resourceId?.let { " ($it)" } ?: ""} not found",
    cause,
)

open class GulaConflictException(
    val resourceType: String,
    val resourceId: Any? = null,
    message: String? = null,
    cause: Throwable? = null,
) : GulaException(
    message ?: "Conflict on $resourceType${resourceId?.let { " ($it)" } ?: ""}",
    cause,
)

class GulaValidationException(
    val errors: Map<String, List<String>> = emptyMap(),
    message: String = "Validation failed",
    cause: Throwable? = null,
) : GulaException(message, cause)

class GulaRateLimitException(
    val retryAfterSeconds: Int = 60,
    message: String = "Rate limit exceeded",
    cause: Throwable? = null,
) : GulaException(message, cause)

class GulaPermissionException(
    val requiredPermission: String? = null,
    message: String = "Insufficient permissions",
    cause: Throwable? = null,
) : GulaException(message, cause)

class GulaFeatureNotAvailableException(
    val feature: String,
    message: String? = null,
    cause: Throwable? = null,
) : GulaException(
    message ?: "Feature '$feature' is not available on your current plan",
    cause,
)

class GulaSubscriptionLimitException(
    val limitField: String,
    val limitValue: Int,
    val currentCount: Int,
    message: String? = null,
    cause: Throwable? = null,
) : GulaException(
    message ?: "Subscription limit reached for $limitField ($currentCount/$limitValue)",
    cause,
)

class GulaLockedException(
    val resourceType: String,
    val resourceId: Any? = null,
    message: String? = null,
    cause: Throwable? = null,
) : GulaException(
    message ?: "$resourceType${resourceId?.let { " ($it)" } ?: ""} is locked",
    cause,
)

class GulaNetworkException(
    message: String = "Network error",
    cause: Throwable? = null,
) : GulaException(message, cause)

class GulaServerException(
    val statusCode: Int,
    val responseBody: String? = null,
    message: String = "Server error",
    cause: Throwable? = null,
) : GulaException(message, cause)

class GulaIdempotencyConflictException(
    val idempotencyKey: String,
    message: String = "Idempotency key already exists with a different payload",
    cause: Throwable? = null,
) : GulaConflictException("idempotency", idempotencyKey, message, cause)
