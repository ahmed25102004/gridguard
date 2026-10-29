package com.smartgrid.technician.core.network

import com.smartgrid.technician.BuildConfig

/**
 * Isolated configuration for backend API communication.
 *
 * NOTE FOR BACKEND INTEGRATION:
 * The Smart Grid Asset Platform backend must supply:
 * 1. Base URL pointing to the deployed API gateway (configured via BuildConfig.API_BASE_URL).
 * 2. An endpoint at POST `auth/login` accepting `{"email": "...", "password": "..."}`
 *    and returning `{"access_token": "...", "refresh_token": "...", "expires_in": 3600, "user": {...}}`.
 * 3. Standard HTTPS TLS 1.3/1.2 endpoint certificates in production.
 */
object ApiConfig {

    /**
     * Default base URL obtained from Gradle BuildConfig.
     * Can be overridden at runtime or during testing.
     */
    val defaultBaseUrl: String
        get() = BuildConfig.API_BASE_URL

    const val TIMEOUT_CONNECT_SECONDS = 15L
    const val TIMEOUT_READ_SECONDS = 15L
    const val TIMEOUT_WRITE_SECONDS = 15L

    // Authentication Endpoints
    const val ENDPOINT_LOGIN = "auth/login"
    const val ENDPOINT_REFRESH = "auth/refresh"
    const val ENDPOINT_PROFILE = "auth/profile"
}
