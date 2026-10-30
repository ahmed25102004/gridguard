package com.smartgrid.technician.fakes

import java.nio.charset.StandardCharsets
import java.util.Base64

object TestJwtHelper {

    fun createToken(
        subject: String = "tech_123",
        email: String = "technician@smartgrid.com",
        role: String = "technician",
        expiresInSeconds: Long = 3600
    ): String {
        val header = "{\"alg\":\"HS256\",\"typ\":\"JWT\"}"
        val exp = (System.currentTimeMillis() / 1000L) + expiresInSeconds
        val payload = "{\"sub\":\"$subject\",\"email\":\"$email\",\"role\":\"$role\",\"exp\":$exp}"

        val headerBase64 = Base64.getUrlEncoder().withoutPadding().encodeToString(header.toByteArray(StandardCharsets.UTF_8))
        val payloadBase64 = Base64.getUrlEncoder().withoutPadding().encodeToString(payload.toByteArray(StandardCharsets.UTF_8))
        val signature = "dummy_signature_for_test"

        return "$headerBase64.$payloadBase64.$signature"
    }

    fun createExpiredToken(
        subject: String = "tech_123",
        email: String = "technician@smartgrid.com"
    ): String {
        // Expired 1 hour ago
        return createToken(subject, email, expiresInSeconds = -3600)
    }
}
