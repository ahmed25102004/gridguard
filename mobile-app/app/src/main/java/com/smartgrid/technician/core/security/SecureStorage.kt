package com.smartgrid.technician.core.security

/**
 * Interface defining secure key, token, and database passphrase storage operations.
 * Implementations must back keys using Android Keystore and never persist secrets as plaintext.
 */
interface SecureStorage {
    fun saveAccessToken(token: String)
    fun getAccessToken(): String?
    fun clearAccessToken()

    fun saveRefreshToken(refreshToken: String)
    fun getRefreshToken(): String?
    fun clearRefreshToken()

    fun saveUserData(userId: String, email: String, name: String, role: String)
    fun getUserData(): StoredUser?
    fun clearUserData()

    /**
     * Obtains or generates a cryptographically secure 256-bit (32 bytes) passphrase
     * for SQLCipher database encryption. The key is encrypted using Android Keystore.
     */
    fun getOrCreateDatabasePassphrase(): ByteArray

    /**
     * Clears all session credentials, tokens, and cached user data.
     */
    fun clearSession()
}

data class StoredUser(
    val userId: String,
    val email: String,
    val name: String,
    val role: String
)
