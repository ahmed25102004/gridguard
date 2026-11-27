package com.smartgrid.technician.core.network

import com.smartgrid.technician.core.network.models.AssetDto
import com.smartgrid.technician.core.network.models.LoginRequest
import com.smartgrid.technician.core.network.models.LoginResponse
import com.smartgrid.technician.core.network.models.RefreshTokenRequest
import com.smartgrid.technician.core.network.models.UserDto
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query
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

    @GET(ApiConfig.ENDPOINT_ASSETS)
    suspend fun getAssets(
        @Query("category") category: String? = null,
        @Query("search") search: String? = null
    ): retrofit2.Response<List<AssetDto>>

    @GET("${ApiConfig.ENDPOINT_ASSETS}/{id}")
    suspend fun getAssetById(
        @Path("id") id: String
    ): retrofit2.Response<AssetDto>
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
 * OkHttp interceptor that dynamically applies runtime base URL overrides.
 */
class DynamicBaseUrlInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        var request = chain.request()
        val custom = ApiConfig.customBaseUrl?.trim()
        if (!custom.isNullOrBlank()) {
            val normalizedUrl = if (custom.endsWith("/")) custom else "$custom/"
            val customUrl = try {
                normalizedUrl.toHttpUrlOrNull()
            } catch (_: Exception) {
                null
            }
            if (customUrl != null) {
                val newUrl = request.url.newBuilder()
                    .scheme(customUrl.scheme)
                    .host(customUrl.host)
                    .port(customUrl.port)
                    .build()
                request = request.newBuilder().url(newUrl).build()
            }
        }
        return chain.proceed(request)
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
            .addInterceptor(DynamicBaseUrlInterceptor())
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
