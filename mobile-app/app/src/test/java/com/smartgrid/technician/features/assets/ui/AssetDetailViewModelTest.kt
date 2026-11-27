package com.smartgrid.technician.features.assets.ui

import com.smartgrid.technician.core.network.ConnectivityObserver
import com.smartgrid.technician.core.network.models.AssetDto
import com.smartgrid.technician.fakes.FakeApiService
import com.smartgrid.technician.fakes.FakeConnectivityObserver
import com.smartgrid.technician.fakes.FakeLocalDb
import com.smartgrid.technician.features.assets.data.AssetRepository
import com.smartgrid.technician.features.assets.data.AssetRepositoryImpl
import com.smartgrid.technician.features.assets.data.BaselineAssets
import com.smartgrid.technician.features.assets.domain.AssetCategory
import com.smartgrid.technician.features.assets.domain.DataSource
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AssetDetailViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var fakeApiService: FakeApiService
    private lateinit var fakeLocalDb: FakeLocalDb
    private lateinit var fakeConnectivityObserver: FakeConnectivityObserver
    private lateinit var repository: AssetRepository
    private lateinit var viewModel: AssetDetailViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        fakeApiService = FakeApiService()
        fakeLocalDb = FakeLocalDb()
        fakeConnectivityObserver = FakeConnectivityObserver(ConnectivityObserver.Status.AVAILABLE)
        repository = AssetRepositoryImpl(
            apiService = fakeApiService,
            localDb = fakeLocalDb,
            connectivityObserver = fakeConnectivityObserver,
            ioDispatcher = testDispatcher
        )
        fakeLocalDb.saveAssets(BaselineAssets.initialList.map { it.toCachedAsset() })
        viewModel = AssetDetailViewModel(repository, fakeConnectivityObserver)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `loadAsset loads details from local cache when offline`() = runTest(testDispatcher) {
        fakeConnectivityObserver.setStatus(ConnectivityObserver.Status.UNAVAILABLE)

        viewModel.loadAsset("demo_trf_001")
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertNotNull(state.asset)
        assertEquals("demo_trf_001", state.asset?.id)
        assertEquals("TRF-9021-TX", state.asset?.serialNumber)
        assertEquals(AssetCategory.TRANSFORMERS, state.asset?.category)
        assertEquals(2500.0, state.asset?.kvaRating)
        assertEquals("33 kV / 11 kV", state.asset?.voltageClass)
        assertEquals("Siemens Energy", state.asset?.manufacturer)
        assertEquals(2019, state.asset?.installationYear)
        assertEquals(DataSource.LOADED_FROM_CACHE, state.dataSource)
        assertTrue(state.isOffline)
    }

    @Test
    fun `loadAsset loads live network data when forceRefresh is requested online`() = runTest(testDispatcher) {
        fakeApiService.getAssetByIdResult = Result.success(
            AssetDto(
                id = "demo_trf_001",
                serialNumber = "TRF-9021-TX",
                name = "Updated Step-Down T1",
                category = "TRANSFORMER",
                kvaRating = 3000.0,
                voltageClass = "33 kV / 11 kV",
                manufacturer = "Siemens Energy",
                installationYear = 2019
            )
        )

        viewModel.loadAsset("demo_trf_001", forceRefresh = true)
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertNotNull(state.asset)
        assertEquals("Updated Step-Down T1", state.asset?.name)
        assertEquals(3000.0, state.asset?.kvaRating)
        assertEquals(DataSource.LIVE_NETWORK, state.dataSource)
        assertFalse(state.isOffline)
    }

    @Test
    fun `loadBySerialNumber loads matching circuit breaker`() = runTest(testDispatcher) {
        viewModel.loadBySerialNumber("CB-404-SF6")
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertNotNull(state.asset)
        assertEquals("CB-404-SF6", state.asset?.serialNumber)
        assertEquals(AssetCategory.CIRCUIT_BREAKERS, state.asset?.category)
        assertEquals("Schneider Electric", state.asset?.manufacturer)
        assertEquals("132 kV", state.asset?.voltageClass)
        assertNull(state.asset?.kvaRating)
    }

    @Test
    fun `loadAsset sets errorMessage when asset does not exist`() = runTest(testDispatcher) {
        fakeConnectivityObserver.setStatus(ConnectivityObserver.Status.UNAVAILABLE)

        viewModel.loadAsset("non_existent_id")
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertNull(state.asset)
        assertNotNull(state.errorMessage)
    }
}
