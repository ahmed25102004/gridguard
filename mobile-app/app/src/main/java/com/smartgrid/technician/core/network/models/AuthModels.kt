package com.smartgrid.technician.core.network.models

import com.google.gson.annotations.SerializedName

/**
 * Request payload for technician authentication.
 */
data class LoginRequest(
    @SerializedName("email")
    val email: String,

    @SerializedName("password")
    val password: String
)

/**
 * Standard backend response payload for authentication.
 */
data class LoginResponse(
    @SerializedName("access_token")
    val accessToken: String,

    @SerializedName("refresh_token")
    val refreshToken: String? = null,

    @SerializedName("token_type")
    val tokenType: String? = "Bearer",

    @SerializedName("expires_in")
    val expiresIn: Long? = 3600L,

    @SerializedName("user")
    val user: UserDto? = null
)

/**
 * Technician user representation from the authentication service.
 */
data class UserDto(
    @SerializedName("id")
    val id: String,

    @SerializedName("email")
    val email: String,

    @SerializedName("name")
    val name: String? = null,

    @SerializedName("role")
    val role: String? = "technician"
)

/**
 * Token refresh request payload.
 */
data class RefreshTokenRequest(
    @SerializedName("refresh_token")
    val refreshToken: String
)
