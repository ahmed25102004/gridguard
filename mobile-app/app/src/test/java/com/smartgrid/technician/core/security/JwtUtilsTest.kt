package com.smartgrid.technician.core.security

import com.smartgrid.technician.fakes.TestJwtHelper
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class JwtUtilsTest {

    @Test
    fun `getExpirationTimestamp extracts valid epoch millis from token`() {
        val token = TestJwtHelper.createToken(expiresInSeconds = 3600)
        val exp = JwtUtils.getExpirationTimestamp(token)

        assertNotNull(exp)
        assertTrue(exp!! > System.currentTimeMillis())
    }

    @Test
    fun `isTokenExpired returns false for fresh token`() {
        val freshToken = TestJwtHelper.createToken(expiresInSeconds = 7200)
        assertFalse(JwtUtils.isTokenExpired(freshToken))
    }

    @Test
    fun `isTokenExpired returns true for expired token`() {
        val expiredToken = TestJwtHelper.createExpiredToken()
        assertTrue(JwtUtils.isTokenExpired(expiredToken))
    }

    @Test
    fun `isTokenExpired returns true for malformed token`() {
        assertTrue(JwtUtils.isTokenExpired("invalid.jwt.token"))
        assertTrue(JwtUtils.isTokenExpired(""))
    }

    @Test
    fun `getClaim extracts subject and role correctly`() {
        val token = TestJwtHelper.createToken(subject = "tech_789", role = "senior_technician")

        assertEquals("tech_789", JwtUtils.getClaim(token, "sub"))
        assertEquals("senior_technician", JwtUtils.getClaim(token, "role"))
        assertNull(JwtUtils.getClaim(token, "non_existent_claim"))
    }
}
