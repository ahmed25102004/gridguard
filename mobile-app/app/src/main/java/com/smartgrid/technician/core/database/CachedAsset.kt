package com.smartgrid.technician.core.database

/**
 * Domain entity stored in the SQLCipher-encrypted SQLite database representing a cached power grid asset.
 * Includes all required technical fields: serial number, category, kVA rating, voltage class,
 * manufacturer, and installation year.
 */
data class CachedAsset(
    val id: String,
    val serialNumber: String,
    val name: String,
    val category: String,
    val kvaRating: Double? = null,
    val voltageClass: String? = null,
    val manufacturer: String? = null,
    val installationYear: Int? = null,
    val status: String = "OPERATIONAL",
    val substationId: String? = null,
    val substationName: String? = null,
    val lastInspectedAt: Long? = null,
    val cachedAt: Long = System.currentTimeMillis()
)
