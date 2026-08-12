package io.gula.android.util

sealed class Resource<out T> {
    data class Loading<T>(val data: T? = null) : Resource<T>()
    data class Success<T>(val data: T) : Resource<T>()
    data class Error<T>(val message: String, val data: T? = null, val code: Int? = null) : Resource<T>()

    val isLoading: Boolean get() = this is Loading
    val isSuccess: Boolean get() = this is Success
    val isError: Boolean get() = this is Error

    fun <R> map(transform: (T) -> R): Resource<R> = when (this) {
        is Loading -> Loading(data?.let { transform(it) })
        is Success -> Success(transform(data))
        is Error -> Error(message, data?.let { transform(it) }, code)
    }

    fun getOrNull(): T? = when (this) {
        is Loading -> data
        is Success -> data
        is Error -> data
    }

    fun getOrDefault(default: @UnsafeVariance T): T = when (this) {
        is Loading -> data ?: default
        is Success -> data
        is Error -> data ?: default
    }

    companion object {
        fun <T> loading(data: T? = null): Resource<T> = Loading(data)
        fun <T> success(data: T): Resource<T> = Success(data)
        fun <T> error(message: String, data: T? = null, code: Int? = null): Resource<T> = Error(message, data, code)
    }
}
