package com.smartgrid.technician.features.auth

/**
 * Domain model representing an authenticated technician session.
 */
data class UserSession(
    val userId: String,
    val email: String,
    val name: String,
    val role: String,
    val accessToken: String,
    val expiresAt: Long
)

/**
 * Categorized error types for authentication and network failures.
 */
enum class AuthErrorType {
    INVALID_CREDENTIALS,
    NETWORK_UNAVAILABLE,
    SERVER_ERROR,
    SESSION_EXPIRED,
    VALIDATION_ERROR,
    UNKNOWN
}

/**
 * State machine representing high-level authentication status.
 */
sealed interface AuthState {
    data object Idle : AuthState
    data object CheckingSession : AuthState
    data class Authenticated(val session: UserSession, val isOffline: Boolean = false) : AuthState
    data class Unauthenticated(val reason: String? = null) : AuthState
    data object Loading : AuthState
    data class Error(val message: String, val errorType: AuthErrorType) : AuthState
}
