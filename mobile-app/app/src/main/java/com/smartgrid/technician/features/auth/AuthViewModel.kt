package com.smartgrid.technician.features.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.smartgrid.technician.core.network.ConnectivityObserver
import com.smartgrid.technician.core.network.NetworkException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.regex.Pattern

/**
 * UI State representation for the authentication screen.
 */
data class AuthUiState(
    val email: String = "",
    val password: String = "",
    val emailError: String? = null,
    val passwordError: String? = null,
    val isPasswordVisible: Boolean = false,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val errorType: AuthErrorType? = null,
    val isOnline: Boolean = true,
    val authState: AuthState = AuthState.Idle
) {
    val isLoginEnabled: Boolean
        get() = email.isNotBlank() &&
                password.isNotBlank() &&
                emailError == null &&
                passwordError == null &&
                !isLoading
}

/**
 * ViewModel managing authentication state, input validation, network status,
 * and offline cold-start session restoration.
 */
class AuthViewModel(
    private val authRepository: AuthRepository,
    private val connectivityObserver: ConnectivityObserver
) : ViewModel() {

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    companion object {
        private val EMAIL_REGEX_PATTERN = Pattern.compile(
            "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}$"
        )
        const val MIN_PASSWORD_LENGTH = 6
    }

    init {
        observeConnectivity()
        restoreSession()
    }

    private fun observeConnectivity() {
        viewModelScope.launch {
            connectivityObserver.observe().collect { status ->
                val isOnline = (status == ConnectivityObserver.Status.AVAILABLE)
                _uiState.update { current ->
                    val updatedState = when (val auth = current.authState) {
                        is AuthState.Authenticated -> auth.copy(isOffline = !isOnline)
                        else -> auth
                    }
                    current.copy(
                        isOnline = isOnline,
                        authState = updatedState
                    )
                }
            }
        }
    }

    fun onEmailChange(newEmail: String) {
        _uiState.update {
            it.copy(
                email = newEmail,
                emailError = null,
                errorMessage = null
            )
        }
    }

    fun onPasswordChange(newPassword: String) {
        _uiState.update {
            it.copy(
                password = newPassword,
                passwordError = null,
                errorMessage = null
            )
        }
    }

    fun togglePasswordVisibility() {
        _uiState.update { it.copy(isPasswordVisible = !it.isPasswordVisible) }
    }

    fun dismissError() {
        _uiState.update { it.copy(errorMessage = null, errorType = null) }
    }

    fun validateInputs(): Boolean {
        val current = _uiState.value
        val emailTrimmed = current.email.trim()
        val password = current.password

        var emailError: String? = null
        var passwordError: String? = null

        if (emailTrimmed.isEmpty()) {
            emailError = "Email address is required."
        } else if (!EMAIL_REGEX_PATTERN.matcher(emailTrimmed).matches()) {
            emailError = "Please enter a valid email address (e.g. technician@smartgrid.com)."
        }

        if (password.isEmpty()) {
            passwordError = "Password is required."
        } else if (password.length < MIN_PASSWORD_LENGTH) {
            passwordError = "Password must be at least $MIN_PASSWORD_LENGTH characters."
        }

        _uiState.update {
            it.copy(
                emailError = emailError,
                passwordError = passwordError
            )
        }

        return emailError == null && passwordError == null
    }

    fun login() {
        if (!validateInputs()) return

        val state = _uiState.value
        if (!state.isOnline) {
            val message = "No internet connection. Initial technician login requires an active cellular or Wi-Fi network."
            _uiState.update {
                it.copy(
                    errorMessage = message,
                    errorType = AuthErrorType.NETWORK_UNAVAILABLE,
                    authState = AuthState.Error(message, AuthErrorType.NETWORK_UNAVAILABLE)
                )
            }
            return
        }

        _uiState.update {
            it.copy(
                isLoading = true,
                errorMessage = null,
                errorType = null,
                authState = AuthState.Loading
            )
        }

        viewModelScope.launch {
            val result = authRepository.login(state.email.trim(), state.password)
            result.fold(
                onSuccess = { session ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = null,
                            errorType = null,
                            authState = AuthState.Authenticated(session, isOffline = !it.isOnline)
                        )
                    }
                },
                onFailure = { throwable ->
                    val (errorType, message) = when (throwable) {
                        is NetworkException.InvalidCredentialsException -> {
                            AuthErrorType.INVALID_CREDENTIALS to (throwable.message ?: "Invalid email or password.")
                        }
                        is NetworkException.NoConnectivityException -> {
                            AuthErrorType.NETWORK_UNAVAILABLE to (throwable.message ?: "Network unavailable. Please check connection.")
                        }
                        is NetworkException.ServerException -> {
                            AuthErrorType.SERVER_ERROR to (throwable.message ?: "Smart Grid server is currently unreachable.")
                        }
                        is NetworkException.SessionExpiredException -> {
                            AuthErrorType.SESSION_EXPIRED to (throwable.message ?: "Session expired. Please log in again.")
                        }
                        else -> {
                            AuthErrorType.UNKNOWN to (throwable.message ?: "Authentication failed unexpectedly.")
                        }
                    }

                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = message,
                            errorType = errorType,
                            authState = AuthState.Error(message, errorType)
                        )
                    }
                }
            )
        }
    }

    fun restoreSession() {
        _uiState.update { it.copy(authState = AuthState.CheckingSession) }

        viewModelScope.launch {
            val result = authRepository.restoreSession()
            result.fold(
                onSuccess = { session ->
                    if (session != null) {
                        val isOffline = !_uiState.value.isOnline
                        _uiState.update {
                            it.copy(
                                authState = AuthState.Authenticated(session, isOffline = isOffline),
                                errorMessage = null
                            )
                        }
                    } else {
                        _uiState.update {
                            it.copy(authState = AuthState.Unauthenticated())
                        }
                    }
                },
                onFailure = { throwable ->
                    val reason = throwable.message ?: "Session restoration failed."
                    _uiState.update {
                        it.copy(
                            authState = AuthState.Unauthenticated(reason),
                            errorMessage = reason,
                            errorType = AuthErrorType.SESSION_EXPIRED
                        )
                    }
                }
            )
        }
    }

    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
            _uiState.update {
                it.copy(
                    email = "",
                    password = "",
                    emailError = null,
                    passwordError = null,
                    isLoading = false,
                    errorMessage = null,
                    errorType = null,
                    authState = AuthState.Unauthenticated("Technician logged out successfully.")
                )
            }
        }
    }
}
