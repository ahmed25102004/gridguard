package com.smartgrid.technician.features.auth

import com.smartgrid.technician.core.network.ApiService
import com.smartgrid.technician.core.network.ConnectivityObserver
import com.smartgrid.technician.core.network.NetworkException
import com.smartgrid.technician.core.network.models.LoginRequest
import com.smartgrid.technician.core.security.JwtUtils
import com.smartgrid.technician.core.security.SecureStorage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.IOException

interface AuthRepository {
    suspend fun login(email: String, password: String): Result<UserSession>
    suspend fun restoreSession(): Result<UserSession?>
    suspend fun logout(): Result<Unit>
    fun getCurrentSession(): UserSession?
    fun isSessionValid(session: UserSession?): Boolean
}

class AuthRepositoryImpl(
    private val apiService: ApiService,
    private val secureStorage: SecureStorage,
    private val connectivityObserver: ConnectivityObserver
) : AuthRepository {

    private var currentSession: UserSession? = null

    override suspend fun login(email: String, password: String): Result<UserSession> = withContext(Dispatchers.IO) {
        if (!connectivityObserver.isConnected()) {
            return@withContext Result.failure(
                NetworkException.NoConnectivityException("No internet connection. Initial login requires network connectivity.")
            )
        }

        try {
            val response = apiService.login(LoginRequest(email = email.trim(), password = password))
            if (response.isSuccessful) {
                val body = response.body()
                    ?: return@withContext Result.failure(
                        NetworkException.ApiException("Server returned empty authentication payload.")
                    )

                val token = body.accessToken
                if (token.isBlank()) {
                    return@withContext Result.failure(
                        NetworkException.ApiException("Invalid server response: Access token is empty.")
                    )
                }

                secureStorage.saveAccessToken(token)
                body.refreshToken?.let { secureStorage.saveRefreshToken(it) }

                val jwtExpiry = JwtUtils.getExpirationTimestamp(token)
                val expiresAt = jwtExpiry ?: (System.currentTimeMillis() + (body.expiresIn ?: 3600L) * 1000L)

                val userId = body.user?.id ?: JwtUtils.getClaim(token, "user_id") ?: JwtUtils.getClaim(token, "sub") ?: "tech_${System.currentTimeMillis()}"
                val userEmail = body.user?.email ?: email.trim()
                val userName = body.user?.name ?: userEmail.substringBefore("@")
                val userRole = body.user?.role ?: JwtUtils.getClaim(token, "role") ?: "technician"

                secureStorage.saveUserData(
                    userId = userId,
                    email = userEmail,
                    name = userName,
                    role = userRole
                )

                val session = UserSession(
                    userId = userId,
                    email = userEmail,
                    name = userName,
                    role = userRole,
                    accessToken = token,
                    expiresAt = expiresAt
                )
                currentSession = session
                Result.success(session)
            } else {
                val code = response.code()
                val errorResult = when (code) {
                    401, 403 -> NetworkException.InvalidCredentialsException("Invalid email or password.", code)
                    in 500..599 -> NetworkException.ServerException("Smart Grid authentication service is temporarily unavailable ($code).", code)
                    else -> NetworkException.ApiException("Authentication request failed with status code: $code", code)
                }
                Result.failure(errorResult)
            }
        } catch (e: IOException) {
            Result.failure(
                NetworkException.NoConnectivityException(
                    message = "Network error: Unable to reach authentication server. Please check your connection.",
                    cause = e
                )
            )
        } catch (e: Exception) {
            Result.failure(
                NetworkException.UnknownException("Unexpected authentication error: ${e.message}", e)
            )
        }
    }

    override suspend fun restoreSession(): Result<UserSession?> = withContext(Dispatchers.IO) {
        val token = secureStorage.getAccessToken()
        if (token.isNullOrBlank()) {
            return@withContext Result.success(null)
        }

        if (JwtUtils.isTokenExpired(token)) {
            secureStorage.clearSession()
            currentSession = null
            return@withContext Result.failure(
                NetworkException.SessionExpiredException("Saved session has expired. Please log in again.")
            )
        }

        val storedUser = secureStorage.getUserData()
        val userId = storedUser?.userId ?: JwtUtils.getClaim(token, "user_id") ?: JwtUtils.getClaim(token, "sub") ?: "technician"
        val userEmail = storedUser?.email ?: JwtUtils.getClaim(token, "sub") ?: JwtUtils.getClaim(token, "email") ?: ""
        val userName = storedUser?.name ?: userEmail.substringBefore("@")
        val userRole = storedUser?.role ?: JwtUtils.getClaim(token, "role") ?: "technician"
        val expiresAt = JwtUtils.getExpirationTimestamp(token) ?: (System.currentTimeMillis() + 3600000L)

        val session = UserSession(
            userId = userId,
            email = userEmail,
            name = userName,
            role = userRole,
            accessToken = token,
            expiresAt = expiresAt
        )
        currentSession = session
        Result.success(session)
    }

    override suspend fun logout(): Result<Unit> = withContext(Dispatchers.IO) {
        secureStorage.clearSession()
        currentSession = null
        Result.success(Unit)
    }

    override fun getCurrentSession(): UserSession? = currentSession

    override fun isSessionValid(session: UserSession?): Boolean {
        if (session == null) return false
        return !JwtUtils.isTokenExpired(session.accessToken)
    }
}
