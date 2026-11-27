package com.smartgrid.technician.features.assets.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.smartgrid.technician.core.network.ConnectivityObserver
import com.smartgrid.technician.features.assets.data.AssetRepository
import com.smartgrid.technician.features.assets.domain.Asset
import com.smartgrid.technician.features.assets.domain.AssetCategory
import com.smartgrid.technician.features.assets.domain.DataSource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * UI State for the Asset List screen.
 */
data class AssetListUiState(
    val assets: List<Asset> = emptyList(),
    val selectedCategory: AssetCategory = AssetCategory.ALL,
    val searchQuery: String = "",
    val isLoading: Boolean = false,
    val isOffline: Boolean = false,
    val dataSource: DataSource = DataSource.LOADED_FROM_CACHE,
    val errorMessage: String? = null
)

class AssetListViewModel(
    private val assetRepository: AssetRepository,
    private val connectivityObserver: ConnectivityObserver
) : ViewModel() {

    private val _uiState = MutableStateFlow(AssetListUiState())
    val uiState: StateFlow<AssetListUiState> = _uiState.asStateFlow()

    init {
        // Observe connectivity changes in real-time
        viewModelScope.launch {
            connectivityObserver.observe().collect { status ->
                val offline = status != ConnectivityObserver.Status.AVAILABLE
                _uiState.update { it.copy(isOffline = offline) }
            }
        }
        loadAssets()
    }

    fun loadAssets(forceRefresh: Boolean = false) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }

            val currentState = _uiState.value
            val result = assetRepository.getAssets(
                category = currentState.selectedCategory,
                searchQuery = currentState.searchQuery.takeIf { it.isNotBlank() },
                forceRefresh = forceRefresh
            )

            result.onSuccess { listResult ->
                _uiState.update {
                    it.copy(
                        assets = listResult.assets,
                        dataSource = listResult.dataSource,
                        isOffline = listResult.isOffline,
                        isLoading = false,
                        errorMessage = listResult.errorMessage
                    )
                }
            }.onFailure { error ->
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = error.localizedMessage ?: "Failed to load assets"
                    )
                }
            }
        }
    }

    fun onCategorySelected(category: AssetCategory) {
        if (_uiState.value.selectedCategory == category) return
        _uiState.update { it.copy(selectedCategory = category) }
        loadAssets()
    }

    fun onSearchQueryChanged(query: String) {
        _uiState.update { it.copy(searchQuery = query) }
        loadAssets()
    }

    fun clearSearch() {
        _uiState.update { it.copy(searchQuery = "") }
        loadAssets()
    }
}
