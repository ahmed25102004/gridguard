package com.smartgrid.technician.core.di

import android.content.Context
import com.smartgrid.technician.BuildConfig
import com.smartgrid.technician.core.database.LocalDb
import com.smartgrid.technician.core.database.SqlCipherLocalDb
import com.smartgrid.technician.core.network.ApiClient
import com.smartgrid.technician.core.network.ApiService
import com.smartgrid.technician.core.network.ConnectivityObserver
import com.smartgrid.technician.core.network.NetworkConnectivityObserver
import com.smartgrid.technician.core.security.KeystoreSecureStorage
import com.smartgrid.technician.core.security.SecureStorage
import com.smartgrid.technician.features.auth.AuthRepository
import com.smartgrid.technician.features.auth.AuthRepositoryImpl

/**
 * Dependency container providing core and feature singletons for the application.
 */
interface AppContainer {
    val secureStorage: SecureStorage
    val localDb: LocalDb
    val connectivityObserver: ConnectivityObserver
    val apiService: ApiService
    val authRepository: AuthRepository
}

class DefaultAppContainer(private val context: Context) : AppContainer {

    override val secureStorage: SecureStorage by lazy {
        KeystoreSecureStorage(context)
    }

    override val localDb: LocalDb by lazy {
        SqlCipherLocalDb(context).apply {
            // Unlock/initialize encrypted SQLCipher database using Android Keystore AES-256 passphrase
            try {
                val passphrase = secureStorage.getOrCreateDatabasePassphrase()
                initialize(passphrase)
            } catch (_: Exception) {}
        }
    }

    override val connectivityObserver: ConnectivityObserver by lazy {
        NetworkConnectivityObserver(context)
    }

    override val apiService: ApiService by lazy {
        val okHttpClient = ApiClient.createOkHttpClient(
            tokenProvider = { secureStorage.getAccessToken() },
            isDebug = BuildConfig.DEBUG
        )
        ApiClient.createApiService(okHttpClient = okHttpClient)
    }

    override val authRepository: AuthRepository by lazy {
        AuthRepositoryImpl(
            apiService = apiService,
            secureStorage = secureStorage,
            connectivityObserver = connectivityObserver
        )
    }
}
