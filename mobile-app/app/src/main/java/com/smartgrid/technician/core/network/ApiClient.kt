package com.smartgrid.technician.core.network

import com.smartgrid.technician.core.network.models.LoginRequest
import com.smartgrid.technician.core.network.models.LoginResponse
import com.smartgrid.technician.core.network.models.RefreshTokenRequest
import com.smartgrid.technician.core.network.models.UserDto
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import java.util.concurrent.TimeUnit

/**
 * Retrofit service definition for Smart Grid Asset Platform authentication and technician APIs.
 */
interface ApiService {

    @POST(ApiConfig.ENDPOINT_LOGIN)
    suspend fun login(
        @Body request: LoginRequest
    ): retrofit2.Response<LoginResponse>

    @POST(ApiConfig.ENDPOINT_REFRESH)
    suspend fun refreshToken(
        @Body request: RefreshTokenRequest
    ): retrofit2.Response<LoginResponse>

    @GET(ApiConfig.ENDPOINT_PROFILE)
    suspend fun getProfile(): retrofit2.Response<UserDto>
}

/**
 * OkHttp interceptor that attaches the Bearer JWT token to outgoing API requests,
 * except for public authentication endpoints.
 */
class AuthInterceptor(
    private val tokenProvider: () -> String?
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val path = originalRequest.url.encodedPath

        // Do not attach token to the login endpoint
        if (path.contains(ApiConfig.ENDPOINT_LOGIN)) {
            return chain.proceed(originalRequest)
        }

        val token = tokenProvider()
        return if (!token.isNullOrBlank()) {
            val authenticatedRequest = originalRequest.newBuilder()
                .header("Authorization", "Bearer $token")
                .header("Accept", "application/json")
                .build()
            chain.proceed(authenticatedRequest)
        } else {
            chain.proceed(originalRequest)
        }
    }
}

/**
 * Factory and client provider for Retrofit and OkHttp.
 */
object ApiClient {

    fun createOkHttpClient(
        tokenProvider: () -> String?,
        isDebug: Boolean = false
    ): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            // In release, minimal exposure of sensitive request/response bodies
            level = if (isDebug) {
                HttpLoggingInterceptor.Level.HEADERS
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }

        return OkHttpClient.Builder()
            .connectTimeout(ApiConfig.TIMEOUT_CONNECT_SECONDS, TimeUnit.SECONDS)
            .readTimeout(ApiConfig.TIMEOUT_READ_SECONDS, TimeUnit.SECONDS)
            .writeTimeout(ApiConfig.TIMEOUT_WRITE_SECONDS, TimeUnit.SECONDS)
            .addInterceptor(AuthInterceptor(tokenProvider))
            .addInterceptor(loggingInterceptor)
            .retryOnConnectionFailure(true)
            .build()
    }

    fun createApiService(
        baseUrl: String = ApiConfig.defaultBaseUrl,
        okHttpClient: OkHttpClient
    ): ApiService {
        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}
