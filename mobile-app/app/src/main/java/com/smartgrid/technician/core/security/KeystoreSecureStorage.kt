package com.smartgrid.technician.core.security

import android.content.Context
import android.content.SharedPreferences
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.nio.charset.StandardCharsets
import java.security.KeyStore
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * Android Keystore-backed implementation of [SecureStorage].
 * Uses AES-256-GCM authenticated encryption for all stored sensitive data,
 * including JWT tokens, user metadata, and SQLCipher database passphrases.
 */
class KeystoreSecureStorage(
    context: Context,
    private val prefName: String = PREFS_NAME,
    private val keyAlias: String = KEY_ALIAS
) : SecureStorage {

    private val prefs: SharedPreferences = context.getSharedPreferences(prefName, Context.MODE_PRIVATE)
    private val keyStore: KeyStore = KeyStore.getInstance(ANDROID_KEYSTORE_PROVIDER).apply { load(null) }

    init {
        ensureMasterKeyExists()
    }

    private fun ensureMasterKeyExists() {
        if (!keyStore.containsAlias(keyAlias)) {
            val keyGenerator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES,
                ANDROID_KEYSTORE_PROVIDER
            )
            val spec = KeyGenParameterSpec.Builder(
                keyAlias,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .setRandomizedEncryptionRequired(true)
                .build()

            keyGenerator.init(spec)
            keyGenerator.generateKey()
        }
    }

    private fun getSecretKey(): SecretKey {
        return keyStore.getKey(keyAlias, null) as SecretKey
    }

    private fun encrypt(plainBytes: ByteArray): String {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, getSecretKey())
        val iv = cipher.iv // 12-byte GCM IV
        val cipherText = cipher.doFinal(plainBytes)

        // Prepend 1-byte IV length, IV, then cipherText
        val payload = ByteArray(1 + iv.size + cipherText.size)
        payload[0] = iv.size.toByte()
        System.arraycopy(iv, 0, payload, 1, iv.size)
        System.arraycopy(cipherText, 0, payload, 1 + iv.size, cipherText.size)

        return Base64.encodeToString(payload, Base64.NO_WRAP)
    }

    private fun decrypt(encryptedBase64: String): ByteArray? {
        return try {
            val payload = Base64.decode(encryptedBase64, Base64.NO_WRAP)
            if (payload.isEmpty()) return null

            val ivSize = payload[0].toInt()
            val iv = ByteArray(ivSize)
            System.arraycopy(payload, 1, iv, 0, ivSize)

            val cipherTextSize = payload.size - 1 - ivSize
            val cipherText = ByteArray(cipherTextSize)
            System.arraycopy(payload, 1 + ivSize, cipherText, 0, cipherTextSize)

            val cipher = Cipher.getInstance(TRANSFORMATION)
            val spec = GCMParameterSpec(GCM_TAG_LENGTH_BITS, iv)
            cipher.init(Cipher.DECRYPT_MODE, getSecretKey(), spec)
            cipher.doFinal(cipherText)
        } catch (_: Exception) {
            null
        }
    }

    private fun putEncryptedString(key: String, value: String) {
        val encrypted = encrypt(value.toByteArray(StandardCharsets.UTF_8))
        prefs.edit().putString(key, encrypted).apply()
    }

    private fun getDecryptedString(key: String): String? {
        val encrypted = prefs.getString(key, null) ?: return null
        val decryptedBytes = decrypt(encrypted) ?: return null
        return String(decryptedBytes, StandardCharsets.UTF_8)
    }

    override fun saveAccessToken(token: String) {
        putEncryptedString(KEY_ACCESS_TOKEN, token)
    }

    override fun getAccessToken(): String? {
        return getDecryptedString(KEY_ACCESS_TOKEN)
    }

    override fun clearAccessToken() {
        prefs.edit().remove(KEY_ACCESS_TOKEN).apply()
    }

    override fun saveRefreshToken(refreshToken: String) {
        putEncryptedString(KEY_REFRESH_TOKEN, refreshToken)
    }

    override fun getRefreshToken(): String? {
        return getDecryptedString(KEY_REFRESH_TOKEN)
    }

    override fun clearRefreshToken() {
        prefs.edit().remove(KEY_REFRESH_TOKEN).apply()
    }

    override fun saveUserData(userId: String, email: String, name: String, role: String) {
        putEncryptedString(KEY_USER_ID, userId)
        putEncryptedString(KEY_USER_EMAIL, email)
        putEncryptedString(KEY_USER_NAME, name)
        putEncryptedString(KEY_USER_ROLE, role)
    }

    override fun getUserData(): StoredUser? {
        val userId = getDecryptedString(KEY_USER_ID) ?: return null
        val email = getDecryptedString(KEY_USER_EMAIL) ?: return null
        val name = getDecryptedString(KEY_USER_NAME) ?: ""
        val role = getDecryptedString(KEY_USER_ROLE) ?: "technician"
        return StoredUser(userId = userId, email = email, name = name, role = role)
    }

    override fun clearUserData() {
        prefs.edit()
            .remove(KEY_USER_ID)
            .remove(KEY_USER_EMAIL)
            .remove(KEY_USER_NAME)
            .remove(KEY_USER_ROLE)
            .apply()
    }

    override fun getOrCreateDatabasePassphrase(): ByteArray {
        val existingEncrypted = prefs.getString(KEY_DB_PASSPHRASE, null)
        if (existingEncrypted != null) {
            val decrypted = decrypt(existingEncrypted)
            if (decrypted != null && decrypted.size == 32) {
                return decrypted
            }
        }

        // Generate cryptographically secure random 256-bit (32 bytes) key
        val secureRandom = SecureRandom()
        val keyBytes = ByteArray(32)
        secureRandom.nextBytes(keyBytes)

        val encryptedBase64 = encrypt(keyBytes)
        prefs.edit().putString(KEY_DB_PASSPHRASE, encryptedBase64).commit()
        return keyBytes
    }

    override fun clearSession() {
        clearAccessToken()
        clearRefreshToken()
        clearUserData()
    }

    companion object {
        private const val ANDROID_KEYSTORE_PROVIDER = "AndroidKeyStore"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
        private const val GCM_TAG_LENGTH_BITS = 128
        private const val PREFS_NAME = "smart_grid_secure_vault"
        private const val KEY_ALIAS = "SmartGridTechnicianMasterKey"

        private const val KEY_ACCESS_TOKEN = "enc_access_token"
        private const val KEY_REFRESH_TOKEN = "enc_refresh_token"
        private const val KEY_USER_ID = "enc_user_id"
        private const val KEY_USER_EMAIL = "enc_user_email"
        private const val KEY_USER_NAME = "enc_user_name"
        private const val KEY_USER_ROLE = "enc_user_role"
        private const val KEY_DB_PASSPHRASE = "enc_db_passphrase"
    }
}
