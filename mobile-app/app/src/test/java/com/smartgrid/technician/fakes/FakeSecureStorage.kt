package com.smartgrid.technician.fakes

import com.smartgrid.technician.core.security.SecureStorage
import com.smartgrid.technician.core.security.StoredUser

class FakeSecureStorage : SecureStorage {
    private var accessToken: String? = null
    private var refreshToken: String? = null
    private var user: StoredUser? = null
    private var passphrase = ByteArray(32) { 0x01 }

    override fun saveAccessToken(token: String) {
        accessToken = token
    }

    override fun getAccessToken(): String? = accessToken

    override fun clearAccessToken() {
        accessToken = null
    }

    override fun saveRefreshToken(refreshToken: String) {
        this.refreshToken = refreshToken
    }

    override fun getRefreshToken(): String? = refreshToken

    override fun clearRefreshToken() {
        refreshToken = null
    }

    override fun saveUserData(userId: String, email: String, name: String, role: String) {
        user = StoredUser(userId, email, name, role)
    }

    override fun getUserData(): StoredUser? = user

    override fun clearUserData() {
        user = null
    }

    override fun getOrCreateDatabasePassphrase(): ByteArray = passphrase

    override fun clearSession() {
        accessToken = null
        refreshToken = null
        user = null
    }
}
