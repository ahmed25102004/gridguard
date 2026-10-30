package com.smartgrid.technician.fakes

import com.smartgrid.technician.core.network.ConnectivityObserver
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class FakeConnectivityObserver(
    initialStatus: ConnectivityObserver.Status = ConnectivityObserver.Status.AVAILABLE
) : ConnectivityObserver {

    private val statusFlow = MutableStateFlow(initialStatus)

    fun setStatus(status: ConnectivityObserver.Status) {
        statusFlow.value = status
    }

    override fun observe(): Flow<ConnectivityObserver.Status> = statusFlow.asStateFlow()

    override fun isConnected(): Boolean {
        return statusFlow.value == ConnectivityObserver.Status.AVAILABLE
    }
}
