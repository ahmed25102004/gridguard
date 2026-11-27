package com.smartgrid.technician.features.assets.data

import android.util.Log
import com.smartgrid.technician.core.database.LocalDb
import com.smartgrid.technician.core.network.ApiService
import com.smartgrid.technician.core.network.ConnectivityObserver
import com.smartgrid.technician.features.assets.domain.Asset
import com.smartgrid.technician.features.assets.domain.AssetCategory
import com.smartgrid.technician.features.assets.domain.DataSource
import com.smartgrid.technician.features.assets.domain.toDomain
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Result data holder for asset list queries, carrying both the data and source metadata.
 */
data class AssetListResult(
    val assets: List<Asset>,
    val dataSource: DataSource,
    val isOffline: Boolean,
    val errorMessage: String? = null
)

/**
 * Result data holder for single asset detail queries.
 */
data class AssetDetailResult(
    val asset: Asset,
    val dataSource: DataSource,
    val isOffline: Boolean
)

/**
 * Repository contract for managing smart grid assets across network and local encrypted storage.
 */
interface AssetRepository {

    suspend fun getAssets(
        category: AssetCategory? = null,
        searchQuery: String? = null,
        forceRefresh: Boolean = false
    ): Result<AssetListResult>

    suspend fun getAssetById(
        id: String,
        forceRefresh: Boolean = false
    ): Result<AssetDetailResult>

    suspend fun getAssetBySerialNumber(
        serialNumber: String
    ): Result<AssetDetailResult>

    suspend fun seedInitialAssetsIfEmpty(initialAssets: List<Asset>): Int
}

/**
 * Implementation of AssetRepository combining Retrofit network calls and SQLCipher local caching.
 * Ensures DataSource.LIVE_NETWORK is strictly used for successful backend responses, while
 * any network failures or offline states transparently fall back to encrypted local storage.
 */
class AssetRepositoryImpl(
    private val apiService: ApiService,
    private val localDb: LocalDb,
    private val connectivityObserver: ConnectivityObserver,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO
) : AssetRepository {

    companion object {
        private const val TAG = "AssetRepository"

        private fun logDebug(msg: String) {
            try { Log.d(TAG, msg) } catch (_: Throwable) {}
        }

        private fun logWarn(msg: String, tr: Throwable? = null) {
            try { if (tr != null) Log.w(TAG, msg, tr) else Log.w(TAG, msg) } catch (_: Throwable) {}
        }

        private fun logErr(msg: String, tr: Throwable? = null) {
            try { if (tr != null) Log.e(TAG, msg, tr) else Log.e(TAG, msg) } catch (_: Throwable) {}
        }
    }

    override suspend fun getAssets(
        category: AssetCategory?,
        searchQuery: String?,
        forceRefresh: Boolean
    ): Result<AssetListResult> = withContext(ioDispatcher) {
        val isOnline = connectivityObserver.isConnected()
        val categoryKey = category?.categoryKey?.takeIf { it != "ALL" }

        if (isOnline) {
            try {
                val response = apiService.getAssets(
                    category = categoryKey,
                    search = searchQuery?.takeIf { it.isNotBlank() }
                )

                if (response.isSuccessful && response.body() != null) {
                    val dtoList = response.body()!!
                    // Persist fresh assets into encrypted local cache
                    val cachedAssets = dtoList.map { it.toCachedAsset() }
                    localDb.saveAssets(cachedAssets)

                    // Return verified live network results
                    val liveAssets = dtoList.map { it.toDomain() }.filter { asset ->
                        val matchesCategory = category == null || category == AssetCategory.ALL || asset.category == category
                        val matchesSearch = searchQuery.isNullOrBlank() ||
                            asset.serialNumber.contains(searchQuery.trim(), ignoreCase = true) ||
                            asset.name.contains(searchQuery.trim(), ignoreCase = true)
                        matchesCategory && matchesSearch
                    }

                    return@withContext Result.success(
                        AssetListResult(
                            assets = liveAssets,
                            dataSource = DataSource.LIVE_NETWORK,
                            isOffline = false
                        )
                    )
                } else {
                    logWarn("Backend assets endpoint returned HTTP ${response.code()} (${response.message()}). Falling back to local encrypted cache.")
                    // Safe fallback to encrypted cache
                    val cachedList = localDb.getCachedAssets(categoryKey, searchQuery)
                    return@withContext Result.success(
                        AssetListResult(
                            assets = cachedList.map { it.toDomain() },
                            dataSource = DataSource.LOADED_FROM_CACHE,
                            isOffline = false,
                            errorMessage = if (cachedList.isEmpty()) {
                                "Backend endpoint unavailable (HTTP ${response.code()}) and local cache is empty."
                            } else null
                        )
                    )
                }
            } catch (e: Exception) {
                logWarn("Network request for assets failed: ${e.message}. Falling back to encrypted cache.", e)
                val cachedList = localDb.getCachedAssets(categoryKey, searchQuery)
                return@withContext Result.success(
                    AssetListResult(
                        assets = cachedList.map { it.toDomain() },
                        dataSource = DataSource.LOADED_FROM_CACHE,
                        isOffline = true,
                        errorMessage = "Network error: ${e.localizedMessage ?: "Failed to reach server"}. Loaded from local cache."
                    )
                )
            }
        } else {
            // Offline / Airplane Mode fallback
            logDebug("Device is offline. Serving assets directly from SQLCipher cache.")
            val cachedList = localDb.getCachedAssets(categoryKey, searchQuery)
            return@withContext Result.success(
                AssetListResult(
                    assets = cachedList.map { it.toDomain() },
                    dataSource = DataSource.LOADED_FROM_CACHE,
                    isOffline = true
                )
            )
        }
    }

    override suspend fun getAssetById(
        id: String,
        forceRefresh: Boolean
    ): Result<AssetDetailResult> = withContext(ioDispatcher) {
        val isOnline = connectivityObserver.isConnected()

        if (isOnline && forceRefresh) {
            try {
                val response = apiService.getAssetById(id)
                if (response.isSuccessful && response.body() != null) {
                    val dto = response.body()!!
                    localDb.saveAsset(dto.toCachedAsset())
                    return@withContext Result.success(
                        AssetDetailResult(
                            asset = dto.toDomain(),
                            dataSource = DataSource.LIVE_NETWORK,
                            isOffline = false
                        )
                    )
                }
            } catch (e: Exception) {
                logWarn("Network error fetching asset $id: ${e.message}. Falling back to cache.", e)
            }
        }

        // Check local encrypted cache first for sub-100ms ultra-fast lookup
        val cached = localDb.getCachedAssetById(id)
        if (cached != null) {
            return@withContext Result.success(
                AssetDetailResult(
                    asset = cached.toDomain(),
                    dataSource = DataSource.LOADED_FROM_CACHE,
                    isOffline = !isOnline
                )
            )
        }

        // If not in cache and online, attempt network fetch
        if (isOnline) {
            try {
                val response = apiService.getAssetById(id)
                if (response.isSuccessful && response.body() != null) {
                    val dto = response.body()!!
                    localDb.saveAsset(dto.toCachedAsset())
                    return@withContext Result.success(
                        AssetDetailResult(
                            asset = dto.toDomain(),
                            dataSource = DataSource.LIVE_NETWORK,
                            isOffline = false
                        )
                    )
                }
            } catch (e: Exception) {
                logErr("Failed to retrieve asset $id from backend: ${e.message}", e)
            }
        }

        Result.failure(NoSuchElementException("Asset with ID '$id' could not be found locally or on the server."))
    }

    override suspend fun getAssetBySerialNumber(
        serialNumber: String
    ): Result<AssetDetailResult> = withContext(ioDispatcher) {
        val isOnline = connectivityObserver.isConnected()

        // Look up by indexed serial number in SQLCipher
        val cached = localDb.getCachedAssetBySerialNumber(serialNumber)
        if (cached != null) {
            return@withContext Result.success(
                AssetDetailResult(
                    asset = cached.toDomain(),
                    dataSource = DataSource.LOADED_FROM_CACHE,
                    isOffline = !isOnline
                )
            )
        }

        // If online and not found locally, query via search query
        if (isOnline) {
            try {
                val response = apiService.getAssets(search = serialNumber)
                if (response.isSuccessful && !response.body().isNullOrEmpty()) {
                    val matched = response.body()!!.firstOrNull {
                        it.serialNumber.equals(serialNumber, ignoreCase = true)
                    } ?: response.body()!!.first()

                    localDb.saveAsset(matched.toCachedAsset())
                    return@withContext Result.success(
                        AssetDetailResult(
                            asset = matched.toDomain(),
                            dataSource = DataSource.LIVE_NETWORK,
                            isOffline = false
                        )
                    )
                }
            } catch (e: Exception) {
                logErr("Network lookup by serial number failed: ${e.message}", e)
            }
        }

        Result.failure(NoSuchElementException("Asset with serial number '$serialNumber' not found."))
    }

    override suspend fun seedInitialAssetsIfEmpty(initialAssets: List<Asset>): Int = withContext(ioDispatcher) {
        val count = localDb.getCachedAssetCount()
        if (count == 0 && initialAssets.isNotEmpty()) {
            logDebug("Seeding ${initialAssets.size} baseline grid assets into SQLCipher cache.")
            localDb.saveAssets(initialAssets.map { it.toCachedAsset() })
        } else {
            0
        }
    }
}
