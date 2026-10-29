package com.smartgrid.technician.core.network

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.distinctUntilChanged

/**
 * Interface for observing network connectivity state changes.
 */
interface ConnectivityObserver {
    fun observe(): Flow<Status>
    fun isConnected(): Boolean

    enum class Status {
        AVAILABLE,
        UNAVAILABLE,
        LOSING,
        LOST
    }
}

/**
 * Android ConnectivityManager implementation of [ConnectivityObserver].
 */
class NetworkConnectivityObserver(
    context: Context
) : ConnectivityObserver {

    private val connectivityManager =
        context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager

    override fun isConnected(): Boolean {
        val cm = connectivityManager ?: return false
        val activeNetwork = cm.activeNetwork ?: return false
        val capabilities = cm.getNetworkCapabilities(activeNetwork) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
                capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }

    override fun observe(): Flow<ConnectivityObserver.Status> {
        return callbackFlow {
            val cm = connectivityManager
            if (cm == null) {
                trySend(ConnectivityObserver.Status.UNAVAILABLE)
                close()
                return@callbackFlow
            }

            // Emit initial status
            trySend(if (isConnected()) ConnectivityObserver.Status.AVAILABLE else ConnectivityObserver.Status.UNAVAILABLE)

            val callback = object : ConnectivityManager.NetworkCallback() {
                override fun onAvailable(network: Network) {
                    super.onAvailable(network)
                    trySend(ConnectivityObserver.Status.AVAILABLE)
                }

                override fun onLosing(network: Network, maxMsToLive: Int) {
                    super.onLosing(network, maxMsToLive)
                    trySend(ConnectivityObserver.Status.LOSING)
                }

                override fun onLost(network: Network) {
                    super.onLost(network)
                    trySend(ConnectivityObserver.Status.LOST)
                }

                override fun onUnavailable() {
                    super.onUnavailable()
                    trySend(ConnectivityObserver.Status.UNAVAILABLE)
                }
            }

            val request = NetworkRequest.Builder()
                .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
                .build()

            try {
                cm.registerNetworkCallback(request, callback)
            } catch (_: Exception) {
                trySend(ConnectivityObserver.Status.UNAVAILABLE)
            }

            awaitClose {
                try {
                    cm.unregisterNetworkCallback(callback)
                } catch (_: Exception) {}
            }
        }.distinctUntilChanged()
    }
}
