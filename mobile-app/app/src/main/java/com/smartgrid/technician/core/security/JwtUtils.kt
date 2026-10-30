package com.smartgrid.technician.core.security

import android.util.Base64
import org.json.JSONObject
import java.nio.charset.StandardCharsets

/**
 * Utility for parsing and inspecting JWT tokens securely without third-party dependencies.
 */
object JwtUtils {

    /**
     * Extracts expiration timestamp (in milliseconds) from a JWT access token.
     * Returns null if token is malformed or does not contain 'exp' claim.
     */
    fun getExpirationTimestamp(token: String): Long? {
        val payloadJson = getPayloadJsonObject(token) ?: return null
        return if (payloadJson.has("exp")) {
            val expInSeconds = payloadJson.optLong("exp")
            expInSeconds * 1000L
        } else {
            null
        }
    }

    /**
     * Checks whether the given JWT token is expired.
     * An optional clock skew margin (e.g. 30 seconds) can be provided to handle time drift.
     */
    fun isTokenExpired(token: String, clockSkewSeconds: Long = 30): Boolean {
        val expMillis = getExpirationTimestamp(token) ?: return true
        val currentMillis = System.currentTimeMillis()
        val marginMillis = clockSkewSeconds * 1000L
        return currentMillis >= (expMillis - marginMillis)
    }

    /**
     * Extracts claim value from JWT payload.
     */
    fun getClaim(token: String, claimName: String): String? {
        val payloadJson = getPayloadJsonObject(token) ?: return null
        return if (payloadJson.has(claimName)) payloadJson.optString(claimName) else null
    }

    private fun getPayloadJsonObject(token: String): JSONObject? {
        return try {
            val parts = token.split(".")
            if (parts.size < 2) return null
            val payloadBase64 = parts[1]
            val decodedBytes = Base64.decode(payloadBase64, Base64.URL_SAFE or Base64.NO_PADDING or Base64.NO_WRAP)
            val jsonString = String(decodedBytes, StandardCharsets.UTF_8)
            JSONObject(jsonString)
        } catch (_: Exception) {
            null
        }
    }
}
