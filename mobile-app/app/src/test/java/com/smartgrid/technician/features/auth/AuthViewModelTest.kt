package com.smartgrid.technician.features.auth

import com.smartgrid.technician.core.network.ConnectivityObserver
import com.smartgrid.technician.core.network.models.LoginResponse
import com.smartgrid.technician.core.network.models.UserDto
import com.smartgrid.technician.fakes.FakeApiService
import com.smartgrid.technician.fakes.FakeConnectivityObserver
import com.smartgrid.technician.fakes.FakeSecureStorage
import com.smartgrid.technician.fakes.TestJwtHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AuthViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var fakeApiService: FakeApiService
    private lateinit var fakeSecureStorage: FakeSecureStorage
    private lateinit var fakeConnectivityObserver: FakeConnectivityObserver
    private lateinit var authRepository: AuthRepository
    private lateinit var viewModel: AuthViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        fakeApiService = FakeApiService()
        fakeSecureStorage = FakeSecureStorage()
        fakeConnectivityObserver = FakeConnectivityObserver(ConnectivityObserver.Status.AVAILABLE)
        authRepository = AuthRepositoryImpl(fakeApiService, fakeSecureStorage, fakeConnectivityObserver)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private fun createViewModel(): AuthViewModel {
        return AuthViewModel(authRepository, fakeConnectivityObserver)
    }

    @Test
    fun `validateInputs flags empty email as error`() = runTest {
        viewModel = createViewModel()
        advanceUntilIdle()

        viewModel.onEmailChange("")
        viewModel.onPasswordChange("ValidPass123!")

        val isValid = viewModel.validateInputs()

        assertFalse(isValid)
        assertEquals("Email address is required.", viewModel.uiState.value.emailError)
    }

    @Test
    fun `validateInputs flags invalid email format as error`() = runTest {
        viewModel = createViewModel()
        advanceUntilIdle()

        viewModel.onEmailChange("invalid-email-format")
        viewModel.onPasswordChange("ValidPass123!")

        val isValid = viewModel.validateInputs()

        assertFalse(isValid)
        assertNotNull(viewModel.uiState.value.emailError)
    }

    @Test
    fun `validateInputs flags short password as error`() = runTest {
        viewModel = createViewModel()
        advanceUntilIdle()

        viewModel.onEmailChange("technician@smartgrid.com")
        viewModel.onPasswordChange("123")

        val isValid = viewModel.validateInputs()

        assertFalse(isValid)
        assertEquals("Password must be at least 6 characters.", viewModel.uiState.value.passwordError)
    }

    @Test
    fun `validateInputs accepts valid email and password`() = runTest {
        viewModel = createViewModel()
        advanceUntilIdle()

        viewModel.onEmailChange("technician@smartgrid.com")
        viewModel.onPasswordChange("SecurePassword123!")

        val isValid = viewModel.validateInputs()

        assertTrue(isValid)
        assertNull(viewModel.uiState.value.emailError)
        assertNull(viewModel.uiState.value.passwordError)
    }

    @Test
    fun `successful login updates state to Authenticated`() = runTest {
        val token = TestJwtHelper.createToken(subject = "tech_1", email = "tech@smartgrid.com")
        fakeApiService.loginResult = Result.success(
            LoginResponse(
                accessToken = token,
                expiresIn = 3600,
                user = UserDto(id = "tech_1", email = "tech@smartgrid.com", name = "Test Tech", role = "technician")
            )
        )

        viewModel = createViewModel()
        advanceUntilIdle()

        viewModel.onEmailChange("tech@smartgrid.com")
        viewModel.onPasswordChange("SecurePass123!")
        viewModel.login()

        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertNull(state.errorMessage)
        assertTrue(state.authState is AuthState.Authenticated)
        val auth = state.authState as AuthState.Authenticated
        assertEquals("tech_1", auth.session.userId)
        assertEquals("tech@smartgrid.com", auth.session.email)
    }

    @Test
    fun `rejected credentials sets INVALID_CREDENTIALS error`() = runTest {
        fakeApiService.loginResult = Result.failure(Exception("401 Unauthorized"))

        viewModel = createViewModel()
        advanceUntilIdle()

        viewModel.onEmailChange("tech@smartgrid.com")
        viewModel.onPasswordChange("WrongPassword!")
        viewModel.login()

        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertNotNull(state.errorMessage)
        assertEquals(AuthErrorType.INVALID_CREDENTIALS, state.errorType)
        assertTrue(state.authState is AuthState.Error)
    }

    @Test
    fun `login when offline immediately sets NETWORK_UNAVAILABLE error without API call`() = runTest {
        fakeConnectivityObserver.setStatus(ConnectivityObserver.Status.UNAVAILABLE)

        viewModel = createViewModel()
        advanceUntilIdle()

        viewModel.onEmailChange("tech@smartgrid.com")
        viewModel.onPasswordChange("Password123!")
        viewModel.login()

        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertEquals(AuthErrorType.NETWORK_UNAVAILABLE, state.errorType)
        assertTrue(state.authState is AuthState.Error)
    }

    @Test
    fun `server 500 failure sets SERVER_ERROR state`() = runTest {
        fakeApiService.loginResult = Result.failure(Exception("500 Internal Server Error"))

        viewModel = createViewModel()
        advanceUntilIdle()

        viewModel.onEmailChange("tech@smartgrid.com")
        viewModel.onPasswordChange("Password123!")
        viewModel.login()

        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertEquals(AuthErrorType.SERVER_ERROR, state.errorType)
        assertTrue(state.authState is AuthState.Error)
    }

    @Test
    fun `cold start session restoration with valid token transitions to Authenticated`() = runTest {
        val validToken = TestJwtHelper.createToken(subject = "tech_persisted", email = "persisted@smartgrid.com")
        fakeSecureStorage.saveAccessToken(validToken)
        fakeSecureStorage.saveUserData("tech_persisted", "persisted@smartgrid.com", "Persisted Tech", "lead_technician")

        viewModel = createViewModel()
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertTrue(state.authState is AuthState.Authenticated)
        val auth = state.authState as AuthState.Authenticated
        assertEquals("tech_persisted", auth.session.userId)
        assertEquals("lead_technician", auth.session.role)
    }

    @Test
    fun `cold start session restoration with expired token transitions to Unauthenticated`() = runTest {
        val expiredToken = TestJwtHelper.createExpiredToken(subject = "tech_expired")
        fakeSecureStorage.saveAccessToken(expiredToken)
        fakeSecureStorage.saveUserData("tech_expired", "expired@smartgrid.com", "Expired Tech", "technician")

        viewModel = createViewModel()
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertTrue(state.authState is AuthState.Unauthenticated)
        assertEquals(AuthErrorType.SESSION_EXPIRED, state.errorType)
        assertNull(fakeSecureStorage.getAccessToken())
    }

    @Test
    fun `cold start without existing session transitions to Unauthenticated`() = runTest {
        viewModel = createViewModel()
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertTrue(state.authState is AuthState.Unauthenticated)
        assertNull(state.errorMessage)
    }

    @Test
    fun `logout resets state to Unauthenticated and clears fields`() = runTest {
        val token = TestJwtHelper.createToken()
        fakeSecureStorage.saveAccessToken(token)

        viewModel = createViewModel()
        advanceUntilIdle()

        viewModel.logout()
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertTrue(state.authState is AuthState.Unauthenticated)
        assertEquals("", state.email)
        assertEquals("", state.password)
        assertNull(fakeSecureStorage.getAccessToken())
    }

    @Test
    fun `password visibility toggles between true and false`() = runTest {
        viewModel = createViewModel()
        advanceUntilIdle()

        assertFalse(viewModel.uiState.value.isPasswordVisible)

        viewModel.togglePasswordVisibility()
        assertTrue(viewModel.uiState.value.isPasswordVisible)

        viewModel.togglePasswordVisibility()
        assertFalse(viewModel.uiState.value.isPasswordVisible)
    }
}
