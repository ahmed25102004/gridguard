package com.smartgrid.technician.core.security

import com.google.gson.Gson
import com.google.gson.JsonObject
import java.nio.charset.StandardCharsets

/**
 * Utility for parsing and inspecting JWT tokens securely.
 */
object JwtUtils {

    private val gson = Gson()

    /**
     * Extracts expiration timestamp (in milliseconds) from a JWT access token.
     * Returns null if token is malformed or does not contain 'exp' claim.
     */
    fun getExpirationTimestamp(token: String): Long? {
        val payloadJson = getPayloadJsonObject(token) ?: return null
        return if (payloadJson.has("exp")) {
            val expElement = payloadJson.get("exp")
            if (expElement != null && !expElement.isJsonNull) {
                val expInSeconds = expElement.asLong
                expInSeconds * 1000L
            } else null
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
        if (!payloadJson.has(claimName)) return null
        val element = payloadJson.get(claimName)
        return if (element != null && !element.isJsonNull) {
            element.asString
        } else null
    }

    private fun getPayloadJsonObject(token: String): JsonObject? {
        return try {
            val parts = token.split(".")
            if (parts.size < 2) return null
            val payloadBase64 = parts[1]
            val decodedBytes = try {
                java.util.Base64.getUrlDecoder().decode(payloadBase64)
            } catch (_: Exception) {
                android.util.Base64.decode(payloadBase64, android.util.Base64.URL_SAFE or android.util.Base64.NO_PADDING or android.util.Base64.NO_WRAP)
            }
            val jsonString = String(decodedBytes, StandardCharsets.UTF_8)
            gson.fromJson(jsonString, JsonObject::class.java)
        } catch (_: Exception) {
            null
        }
    }
}
