package com.smartgrid.technician.features.assets.ui

import com.smartgrid.technician.core.network.ConnectivityObserver
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
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AssetListViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var fakeApiService: FakeApiService
    private lateinit var fakeLocalDb: FakeLocalDb
    private lateinit var fakeConnectivityObserver: FakeConnectivityObserver
    private lateinit var repository: AssetRepository
    private lateinit var viewModel: AssetListViewModel

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
        // Pre-populate with baseline assets
        fakeLocalDb.saveAssets(BaselineAssets.initialList.map { it.toCachedAsset() })
        viewModel = AssetListViewModel(repository, fakeConnectivityObserver)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `initialization loads assets and exposes state`() = runTest(testDispatcher) {
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertTrue(state.assets.isNotEmpty())
        assertEquals(BaselineAssets.initialList.size, state.assets.size)
        assertEquals(AssetCategory.ALL, state.selectedCategory)
    }

    @Test
    fun `onCategorySelected filters state by category`() = runTest(testDispatcher) {
        advanceUntilIdle()

        viewModel.onCategorySelected(AssetCategory.TRANSFORMERS)
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals(AssetCategory.TRANSFORMERS, state.selectedCategory)
        assertTrue(state.assets.isNotEmpty())
        assertTrue(state.assets.all { it.category == AssetCategory.TRANSFORMERS })
    }

    @Test
    fun `onSearchQueryChanged filters assets by serial number`() = runTest(testDispatcher) {
        advanceUntilIdle()

        viewModel.onSearchQueryChanged("CB-404")
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals("CB-404", state.searchQuery)
        assertEquals(1, state.assets.size)
        assertEquals("CB-404-SF6", state.assets.first().serialNumber)
    }

    @Test
    fun `clearSearch resets query and reloads full list`() = runTest(testDispatcher) {
        advanceUntilIdle()

        viewModel.onSearchQueryChanged("TRF")
        advanceUntilIdle()
        assertEquals("TRF", viewModel.uiState.value.searchQuery)

        viewModel.clearSearch()
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals("", state.searchQuery)
        assertEquals(BaselineAssets.initialList.size, state.assets.size)
    }

    @Test
    fun `connectivity changes update isOffline in UI state`() = runTest(testDispatcher) {
        advanceUntilIdle()
        assertFalse(viewModel.uiState.value.isOffline)

        fakeConnectivityObserver.setStatus(ConnectivityObserver.Status.UNAVAILABLE)
        advanceUntilIdle()

        assertTrue(viewModel.uiState.value.isOffline)
    }
}
