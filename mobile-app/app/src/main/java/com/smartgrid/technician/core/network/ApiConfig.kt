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
 * 3. Endpoints at GET `assets` and GET `assets/{id}` for querying substation power assets.
 * 4. Standard HTTPS TLS 1.3/1.2 endpoint certificates in production.
 */
object ApiConfig {

    /**
     * Optional user-configured base URL override for field testing on physical devices.
     */
    @Volatile
    var customBaseUrl: String? = null

    /**
     * Default base URL obtained from customBaseUrl (if set) or Gradle BuildConfig.
     */
    val defaultBaseUrl: String
        get() {
            val custom = customBaseUrl?.trim()
            return if (!custom.isNullOrBlank()) {
                if (custom.endsWith("/")) custom else "$custom/"
            } else {
                BuildConfig.API_BASE_URL
            }
        }

    const val TIMEOUT_CONNECT_SECONDS = 15L
    const val TIMEOUT_READ_SECONDS = 15L
    const val TIMEOUT_WRITE_SECONDS = 15L

    // Authentication Endpoints
    const val ENDPOINT_LOGIN = "auth/login"
    const val ENDPOINT_REFRESH = "auth/refresh"
    const val ENDPOINT_PROFILE = "auth/me"

    // Asset Endpoints
    const val ENDPOINT_ASSETS = "assets"
}
