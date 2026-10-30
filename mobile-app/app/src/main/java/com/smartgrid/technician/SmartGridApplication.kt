package com.smartgrid.technician

import android.app.Application
import com.smartgrid.technician.core.di.AppContainer
import com.smartgrid.technician.core.di.DefaultAppContainer

/**
 * Base Application class for the Smart Grid Technician mobile app.
 */
class SmartGridApplication : Application() {

    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = DefaultAppContainer(this)
        // Ensure database initializes safely in the background
        Thread {
            try {
                container.localDb
            } catch (_: Exception) {}
        }.start()
    }
}
