package com.smartgrid.technician.features.auth

import com.smartgrid.technician.core.network.ConnectivityObserver
import com.smartgrid.technician.core.network.NetworkException
import com.smartgrid.technician.core.network.models.LoginResponse
import com.smartgrid.technician.core.network.models.UserDto
import com.smartgrid.technician.fakes.FakeApiService
import com.smartgrid.technician.fakes.FakeConnectivityObserver
import com.smartgrid.technician.fakes.FakeSecureStorage
import com.smartgrid.technician.fakes.TestJwtHelper
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class AuthRepositoryTest {

    private lateinit var fakeApiService: FakeApiService
    private lateinit var fakeSecureStorage: FakeSecureStorage
    private lateinit var fakeConnectivityObserver: FakeConnectivityObserver
    private lateinit var repository: AuthRepository

    @Before
    fun setUp() {
        fakeApiService = FakeApiService()
        fakeSecureStorage = FakeSecureStorage()
        fakeConnectivityObserver = FakeConnectivityObserver(ConnectivityObserver.Status.AVAILABLE)
        repository = AuthRepositoryImpl(
            apiService = fakeApiService,
            secureStorage = fakeSecureStorage,
            connectivityObserver = fakeConnectivityObserver
        )
    }

    @Test
    fun `login with valid credentials stores token and returns UserSession`() = runTest {
        val testToken = TestJwtHelper.createToken(
            subject = "tech_42",
            email = "tech@smartgrid.com",
            role = "field_engineer"
        )
        fakeApiService.loginResult = Result.success(
            LoginResponse(
                accessToken = testToken,
                refreshToken = "refresh_token_123",
                expiresIn = 3600,
                user = UserDto(id = "tech_42", email = "tech@smartgrid.com", name = "Jane Doe", role = "field_engineer")
            )
        )

        val result = repository.login("tech@smartgrid.com", "SecurePass123!")

        assertTrue(result.isSuccess)
        val session = result.getOrNull()
        assertNotNull(session)
        assertEquals("tech_42", session?.userId)
        assertEquals("tech@smartgrid.com", session?.email)
        assertEquals("Jane Doe", session?.name)
        assertEquals("field_engineer", session?.role)
        assertEquals(testToken, fakeSecureStorage.getAccessToken())
        assertEquals("refresh_token_123", fakeSecureStorage.getRefreshToken())
    }

    @Test
    fun `login returns InvalidCredentialsException on 401 error`() = runTest {
        fakeApiService.loginResult = Result.failure(Exception("401 Unauthorized"))

        val result = repository.login("tech@smartgrid.com", "WrongPassword")

        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull() is NetworkException.InvalidCredentialsException)
        assertNull(fakeSecureStorage.getAccessToken())
    }

    @Test
    fun `login returns ServerException on 500 error`() = runTest {
        fakeApiService.loginResult = Result.failure(Exception("500 Internal Server Error"))

        val result = repository.login("tech@smartgrid.com", "Password123!")

        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull() is NetworkException.ServerException)
    }

    @Test
    fun `login returns NoConnectivityException when device is offline`() = runTest {
        fakeConnectivityObserver.setStatus(ConnectivityObserver.Status.UNAVAILABLE)

        val result = repository.login("tech@smartgrid.com", "Password123!")

        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull() is NetworkException.NoConnectivityException)
    }

    @Test
    fun `login returns NoConnectivityException on IOException network failure`() = runTest {
        fakeApiService.shouldThrowNetworkException = true

        val result = repository.login("tech@smartgrid.com", "Password123!")

        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull() is NetworkException.NoConnectivityException)
    }

    @Test
    fun `restoreSession returns active session when valid token exists`() = runTest {
        val testToken = TestJwtHelper.createToken(
            subject = "tech_99",
            email = "restored@smartgrid.com"
        )
        fakeSecureStorage.saveAccessToken(testToken)
        fakeSecureStorage.saveUserData("tech_99", "restored@smartgrid.com", "Restored Tech", "technician")

        val result = repository.restoreSession()

        assertTrue(result.isSuccess)
        val session = result.getOrNull()
        assertNotNull(session)
        assertEquals("tech_99", session?.userId)
        assertEquals("restored@smartgrid.com", session?.email)
    }

    @Test
    fun `restoreSession cleans up storage and fails when token is expired`() = runTest {
        val expiredToken = TestJwtHelper.createExpiredToken()
        fakeSecureStorage.saveAccessToken(expiredToken)
        fakeSecureStorage.saveUserData("tech_old", "old@smartgrid.com", "Old Tech", "technician")

        val result = repository.restoreSession()

        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull() is NetworkException.SessionExpiredException)
        assertNull(fakeSecureStorage.getAccessToken())
        assertNull(fakeSecureStorage.getUserData())
    }

    @Test
    fun `restoreSession returns null when no token exists`() = runTest {
        val result = repository.restoreSession()

        assertTrue(result.isSuccess)
        assertNull(result.getOrNull())
    }

    @Test
    fun `logout clears session and credentials from secure storage`() = runTest {
        val token = TestJwtHelper.createToken()
        fakeSecureStorage.saveAccessToken(token)
        fakeSecureStorage.saveRefreshToken("ref_token")
        fakeSecureStorage.saveUserData("id", "email", "name", "role")

        val result = repository.logout()

        assertTrue(result.isSuccess)
        assertNull(fakeSecureStorage.getAccessToken())
        assertNull(fakeSecureStorage.getRefreshToken())
        assertNull(fakeSecureStorage.getUserData())
        assertNull(repository.getCurrentSession())
    }

    @Test
    fun `isSessionValid returns true for non-expired session and false for expired session`() {
        val validToken = TestJwtHelper.createToken(expiresInSeconds = 3600)
        val validSession = UserSession("1", "a@b.com", "A", "tech", validToken, System.currentTimeMillis() + 3600000)

        val expiredToken = TestJwtHelper.createExpiredToken()
        val expiredSession = UserSession("2", "b@b.com", "B", "tech", expiredToken, System.currentTimeMillis() - 3600000)

        assertTrue(repository.isSessionValid(validSession))
        assertFalse(repository.isSessionValid(expiredSession))
        assertFalse(repository.isSessionValid(null))
    }
}
