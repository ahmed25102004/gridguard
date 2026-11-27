package com.smartgrid.technician.features.assets.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.smartgrid.technician.core.network.ConnectivityObserver
import com.smartgrid.technician.features.assets.data.AssetRepository
import com.smartgrid.technician.features.assets.domain.Asset
import com.smartgrid.technician.features.assets.domain.DataSource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * UI State for the Asset Details screen.
 */
data class AssetDetailUiState(
    val asset: Asset? = null,
    val dataSource: DataSource = DataSource.LOADED_FROM_CACHE,
    val isOffline: Boolean = false,
    val isLoading: Boolean = false,
    val errorMessage: String? = null
)

class AssetDetailViewModel(
    private val assetRepository: AssetRepository,
    private val connectivityObserver: ConnectivityObserver
) : ViewModel() {

    private val _uiState = MutableStateFlow(AssetDetailUiState())
    val uiState: StateFlow<AssetDetailUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            connectivityObserver.observe().collect { status ->
                val offline = status != ConnectivityObserver.Status.AVAILABLE
                _uiState.update { it.copy(isOffline = offline) }
            }
        }
    }

    fun loadAsset(assetId: String, forceRefresh: Boolean = false) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }

            val result = assetRepository.getAssetById(assetId, forceRefresh = forceRefresh)
            result.onSuccess { detailResult ->
                _uiState.update {
                    it.copy(
                        asset = detailResult.asset,
                        dataSource = detailResult.dataSource,
                        isOffline = detailResult.isOffline,
                        isLoading = false,
                        errorMessage = null
                    )
                }
            }.onFailure { error ->
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = error.localizedMessage ?: "Asset details unavailable"
                    )
                }
            }
        }
    }

    fun loadBySerialNumber(serialNumber: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }

            val result = assetRepository.getAssetBySerialNumber(serialNumber)
            result.onSuccess { detailResult ->
                _uiState.update {
                    it.copy(
                        asset = detailResult.asset,
                        dataSource = detailResult.dataSource,
                        isOffline = detailResult.isOffline,
                        isLoading = false,
                        errorMessage = null
                    )
                }
            }.onFailure { error ->
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = error.localizedMessage ?: "Asset not found"
                    )
                }
            }
        }
    }
}
