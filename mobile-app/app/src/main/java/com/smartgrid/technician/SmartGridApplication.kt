package com.smartgrid.technician

import android.app.Application
import com.smartgrid.technician.core.di.AppContainer
import com.smartgrid.technician.core.di.DefaultAppContainer
import com.smartgrid.technician.features.assets.data.BaselineAssets
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Base Application class for the Smart Grid Technician mobile app.
 */
class SmartGridApplication : Application() {

    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = DefaultAppContainer(this)

        // Initialize encrypted database and seed baseline asset cache safely in background
        CoroutineScope(Dispatchers.IO).launch {
            try {
                container.localDb
                container.assetRepository.seedInitialAssetsIfEmpty(BaselineAssets.initialList)
            } catch (_: Exception) {}
        }
    }
}
