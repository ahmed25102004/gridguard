package com.smartgrid.technician.features.assets.data

import com.smartgrid.technician.core.network.ConnectivityObserver
import com.smartgrid.technician.core.network.models.AssetDto
import com.smartgrid.technician.fakes.FakeApiService
import com.smartgrid.technician.fakes.FakeConnectivityObserver
import com.smartgrid.technician.fakes.FakeLocalDb
import com.smartgrid.technician.features.assets.domain.AssetCategory
import com.smartgrid.technician.features.assets.domain.DataSource
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AssetRepositoryTest {

    private lateinit var fakeApiService: FakeApiService
    private lateinit var fakeLocalDb: FakeLocalDb
    private lateinit var fakeConnectivityObserver: FakeConnectivityObserver
    private lateinit var repository: AssetRepository

    private val testDispatcher = UnconfinedTestDispatcher()

    private val networkDtoList = listOf(
        AssetDto(
            id = "net_trf_1",
            serialNumber = "TRF-9021-TX",
            name = "Substation North Step-Down T1",
            category = "TRANSFORMER",
            kvaRating = 2500.0,
            voltageClass = "33 kV / 11 kV",
            manufacturer = "Siemens Energy",
            installationYear = 2019,
            status = "OPERATIONAL"
        ),
        AssetDto(
            id = "net_cb_1",
            serialNumber = "CB-404-SF6",
            name = "HV SF6 Gas Circuit Breaker Q01",
            category = "CIRCUIT_BREAKER",
            kvaRating = null,
            voltageClass = "132 kV",
            manufacturer = "Schneider Electric",
            installationYear = 2020,
            status = "OPERATIONAL"
        ),
        AssetDto(
            id = "net_cbl_1",
            serialNumber = "CBL-HV-132-A",
            name = "XLPE Underground Feeder A1",
            category = "CABLE",
            kvaRating = null,
            voltageClass = "132 kV",
            manufacturer = "Prysmian Group",
            installationYear = 2018,
            status = "OPERATIONAL"
        )
    )

    @Before
    fun setUp() {
        fakeApiService = FakeApiService()
        fakeLocalDb = FakeLocalDb()
        fakeConnectivityObserver = FakeConnectivityObserver(ConnectivityObserver.Status.AVAILABLE)
        repository = AssetRepositoryImpl(
            apiService = fakeApiService,
            localDb = fakeLocalDb,
            connectivityObserver = fakeConnectivityObserver,
            ioDispatcher = testDispatcher
        )
    }

    @Test
    fun `getAssets when online fetches from network, caches into LocalDb, and returns LIVE_NETWORK`() = runTest(testDispatcher) {
        fakeApiService.getAssetsResult = Result.success(networkDtoList)

        val result = repository.getAssets()

        assertTrue(result.isSuccess)
        val listResult = result.getOrNull()
        assertNotNull(listResult)
        assertEquals(3, listResult!!.assets.size)
        assertEquals(DataSource.LIVE_NETWORK, listResult.dataSource)
        assertFalse(listResult.isOffline)

        // Verify assets were persisted into encrypted LocalDb
        assertEquals(3, fakeLocalDb.getCachedAssetCount())
        val cachedTransformer = fakeLocalDb.getCachedAssetBySerialNumber("TRF-9021-TX")
        assertNotNull(cachedTransformer)
        assertEquals("Siemens Energy", cachedTransformer?.manufacturer)
        assertEquals(2500.0, cachedTransformer?.kvaRating)
    }

    @Test
    fun `getAssets when offline returns cached assets with LOADED_FROM_CACHE`() = runTest(testDispatcher) {
        // Pre-populate encrypted cache
        repository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)
        val initialCount = fakeLocalDb.getCachedAssetCount()
        assertTrue(initialCount > 0)

        // Set device offline
        fakeConnectivityObserver.setStatus(ConnectivityObserver.Status.UNAVAILABLE)

        val result = repository.getAssets()

        assertTrue(result.isSuccess)
        val listResult = result.getOrNull()
        assertNotNull(listResult)
        assertEquals(initialCount, listResult!!.assets.size)
        assertEquals(DataSource.LOADED_FROM_CACHE, listResult.dataSource)
        assertTrue(listResult.isOffline)
    }

    @Test
    fun `getAssets falls back to encrypted cache when backend returns 404 or 500 error`() = runTest(testDispatcher) {
        // Pre-populate cache
        repository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)
        // Backend returns error (e.g., endpoint not implemented or 500)
        fakeApiService.getAssetsResult = Result.failure(Exception("Backend endpoint not found"))

        val result = repository.getAssets()

        assertTrue(result.isSuccess)
        val listResult = result.getOrNull()
        assertNotNull(listResult)
        assertEquals(BaselineAssets.initialList.size, listResult!!.assets.size)
        assertEquals(DataSource.LOADED_FROM_CACHE, listResult.dataSource)
    }

    @Test
    fun `getAssets falls back to cache safely on network timeout or IOException`() = runTest(testDispatcher) {
        repository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)
        fakeApiService.shouldThrowNetworkExceptionOnAssets = true

        val result = repository.getAssets()

        assertTrue(result.isSuccess)
        val listResult = result.getOrNull()
        assertNotNull(listResult)
        assertEquals(BaselineAssets.initialList.size, listResult!!.assets.size)
        assertEquals(DataSource.LOADED_FROM_CACHE, listResult.dataSource)
        assertTrue(listResult.isOffline)
    }

    @Test
    fun `getAssets correctly filters by Transformers category`() = runTest(testDispatcher) {
        repository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)
        fakeConnectivityObserver.setStatus(ConnectivityObserver.Status.UNAVAILABLE)

        val result = repository.getAssets(category = AssetCategory.TRANSFORMERS)

        assertTrue(result.isSuccess)
        val assets = result.getOrNull()!!.assets
        assertTrue(assets.isNotEmpty())
        assertTrue(assets.all { it.category == AssetCategory.TRANSFORMERS })
    }

    @Test
    fun `getAssets correctly filters by Circuit Breakers category`() = runTest(testDispatcher) {
        repository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)
        fakeConnectivityObserver.setStatus(ConnectivityObserver.Status.UNAVAILABLE)

        val result = repository.getAssets(category = AssetCategory.CIRCUIT_BREAKERS)

        assertTrue(result.isSuccess)
        val assets = result.getOrNull()!!.assets
        assertTrue(assets.isNotEmpty())
        assertTrue(assets.all { it.category == AssetCategory.CIRCUIT_BREAKERS })
    }

    @Test
    fun `getAssets correctly filters by Cables category`() = runTest(testDispatcher) {
        repository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)
        fakeConnectivityObserver.setStatus(ConnectivityObserver.Status.UNAVAILABLE)

        val result = repository.getAssets(category = AssetCategory.CABLES)

        assertTrue(result.isSuccess)
        val assets = result.getOrNull()!!.assets
        assertTrue(assets.isNotEmpty())
        assertTrue(assets.all { it.category == AssetCategory.CABLES })
    }

    @Test
    fun `getAssets correctly searches by serial number`() = runTest(testDispatcher) {
        repository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)
        fakeConnectivityObserver.setStatus(ConnectivityObserver.Status.UNAVAILABLE)

        val result = repository.getAssets(searchQuery = "TRF-9021")

        assertTrue(result.isSuccess)
        val assets = result.getOrNull()!!.assets
        assertEquals(1, assets.size)
        assertEquals("TRF-9021-TX", assets.first().serialNumber)
        assertEquals("Siemens Energy", assets.first().manufacturer)
        assertEquals(2500.0, assets.first().kvaRating)
    }

    @Test
    fun `getAssetById retrieves asset from cache when offline`() = runTest(testDispatcher) {
        repository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)
        fakeConnectivityObserver.setStatus(ConnectivityObserver.Status.UNAVAILABLE)

        val result = repository.getAssetById("demo_trf_001")

        assertTrue(result.isSuccess)
        val detail = result.getOrNull()
        assertNotNull(detail)
        assertEquals("demo_trf_001", detail!!.asset.id)
        assertEquals("TRF-9021-TX", detail.asset.serialNumber)
        assertEquals(DataSource.LOADED_FROM_CACHE, detail.dataSource)
        assertTrue(detail.isOffline)
    }

    @Test
    fun `getAssetBySerialNumber retrieves asset successfully from cache`() = runTest(testDispatcher) {
        repository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)

        val result = repository.getAssetBySerialNumber("CB-404-SF6")

        assertTrue(result.isSuccess)
        val detail = result.getOrNull()
        assertNotNull(detail)
        assertEquals("CB-404-SF6", detail!!.asset.serialNumber)
        assertEquals(AssetCategory.CIRCUIT_BREAKERS, detail.asset.category)
        assertEquals("Schneider Electric", detail.asset.manufacturer)
        assertEquals("132 kV", detail.asset.voltageClass)
    }

    @Test
    fun `empty cache and failed network does not crash and returns safe error message`() = runTest(testDispatcher) {
        // Cache is completely empty
        assertEquals(0, fakeLocalDb.getCachedAssetCount())
        fakeApiService.getAssetsResult = Result.failure(Exception("503 Service Unavailable"))

        val result = repository.getAssets()

        assertTrue(result.isSuccess)
        val listResult = result.getOrNull()
        assertNotNull(listResult)
        assertTrue(listResult!!.assets.isEmpty())
        assertNotNull(listResult.errorMessage)
    }

    @Test
    fun `seedInitialAssetsIfEmpty only seeds once and does not overwrite existing assets`() = runTest(testDispatcher) {
        val seededCount = repository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)
        assertEquals(BaselineAssets.initialList.size, seededCount)

        // Second call should return 0 since cache is already seeded
        val secondSeedCount = repository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)
        assertEquals(0, secondSeedCount)
    }
}
