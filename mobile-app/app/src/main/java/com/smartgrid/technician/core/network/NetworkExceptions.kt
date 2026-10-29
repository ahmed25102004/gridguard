package com.smartgrid.technician.core.network

import java.io.IOException

/**
 * Domain-specific network and authentication exceptions.
 */
sealed class NetworkException(message: String, cause: Throwable? = null) : IOException(message, cause) {

    /**
     * Cellular or Wi-Fi connectivity is unavailable or request timed out.
     */
    class NoConnectivityException(
        message: String = "No network connectivity. Please check your cellular or Wi-Fi connection.",
        cause: Throwable? = null
    ) : NetworkException(message, cause)

    /**
     * Server rejected credentials (HTTP 401 or 403).
     */
    class InvalidCredentialsException(
        message: String = "Invalid email or password.",
        val statusCode: Int = 401
    ) : NetworkException(message)

    /**
     * Remote server responded with 5xx error or internal failure.
     */
    class ServerException(
        message: String = "Smart Grid server error. Please try again later.",
        val statusCode: Int = 500
    ) : NetworkException(message)

    /**
     * Session expired or JWT token is invalid.
     */
    class SessionExpiredException(
        message: String = "Session expired. Please log in again."
    ) : NetworkException(message)

    /**
     * General API communication failure.
     */
    class ApiException(
        message: String,
        val statusCode: Int = 0
    ) : NetworkException(message)

    /**
     * Unexpected exception during network communication.
     */
    class UnknownException(
        message: String = "An unexpected error occurred.",
        cause: Throwable? = null
    ) : NetworkException(message, cause)
}
