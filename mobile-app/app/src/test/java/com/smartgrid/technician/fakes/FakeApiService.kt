package com.smartgrid.technician.fakes

import com.smartgrid.technician.core.network.ApiService
import com.smartgrid.technician.core.network.models.LoginRequest
import com.smartgrid.technician.core.network.models.LoginResponse
import com.smartgrid.technician.core.network.models.RefreshTokenRequest
import com.smartgrid.technician.core.network.models.UserDto
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import retrofit2.Response
import java.io.IOException

class FakeApiService : ApiService {

    var loginResult: Result<LoginResponse>? = null
    var shouldThrowNetworkException: Boolean = false

    override suspend fun login(request: LoginRequest): Response<LoginResponse> {
        if (shouldThrowNetworkException) {
            throw IOException("Simulated network timeout/socket error")
        }

        val result = loginResult ?: return Response.error(
            500,
            "{\"error\":\"Server error\"}".toResponseBody("application/json".toMediaType())
        )

        return if (result.isSuccess) {
            Response.success(result.getOrThrow())
        } else {
            val exception = result.exceptionOrNull()
            val code = when {
                exception?.message?.contains("401") == true -> 401
                exception?.message?.contains("403") == true -> 403
                else -> 500
            }
            Response.error(
                code,
                "{\"error\":\"${exception?.message}\"}".toResponseBody("application/json".toMediaType())
            )
        }
    }

    override suspend fun refreshToken(request: RefreshTokenRequest): Response<LoginResponse> {
        return Response.error(
            501,
            "{\"error\":\"Not implemented in test fake\"}".toResponseBody("application/json".toMediaType())
        )
    }

    override suspend fun getProfile(): Response<UserDto> {
        return Response.success(UserDto(id = "tech_1", email = "technician@smartgrid.com", name = "Test Tech", role = "technician"))
    }
}
