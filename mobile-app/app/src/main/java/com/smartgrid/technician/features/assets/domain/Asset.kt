package com.smartgrid.technician.features.assets.domain

import com.smartgrid.technician.core.database.CachedAsset

/**
 * Supported asset categories for smart grid field operations.
 */
enum class AssetCategory(val displayName: String, val categoryKey: String) {
    ALL("All", "ALL"),
    TRANSFORMERS("Transformers", "TRANSFORMER"),
    CIRCUIT_BREAKERS("Circuit Breakers", "CIRCUIT_BREAKER"),
    CABLES("Cables", "CABLE");

    companion object {
        fun fromKey(key: String?): AssetCategory {
            if (key == null) return ALL
            return entries.firstOrNull {
                it.categoryKey.equals(key, ignoreCase = true) ||
                it.name.equals(key, ignoreCase = true) ||
                it.displayName.equals(key, ignoreCase = true)
            } ?: TRANSFORMERS
        }
    }
}

/**
 * Data source indicator identifying whether an asset or asset list was loaded
 * fresh from the backend network API or served from the encrypted local cache.
 */
enum class DataSource(val label: String) {
    LIVE_NETWORK("Live Network"),
    LOADED_FROM_CACHE("Loaded from Cache")
}

/**
 * Clean domain entity representing a smart grid asset with all required technical fields.
 */
data class Asset(
    val id: String,
    val serialNumber: String,
    val name: String,
    val category: AssetCategory,
    val kvaRating: Double? = null,
    val voltageClass: String? = null,
    val manufacturer: String? = null,
    val installationYear: Int? = null,
    val status: String = "OPERATIONAL",
    val substationId: String? = null,
    val substationName: String? = null,
    val lastInspectedAt: Long? = null,
    val cachedAt: Long = System.currentTimeMillis()
) {
    /**
     * Formats kVA rating safely (e.g., "2,500 kVA" or "N/A" if not applicable/null).
     */
    val formattedKvaRating: String
        get() = if (kvaRating != null && kvaRating > 0) {
            if (kvaRating % 1.0 == 0.0) {
                "${kvaRating.toLong()} kVA"
            } else {
                "%.1f kVA".format(kvaRating)
            }
        } else {
            "N/A"
        }

    /**
     * Formats voltage class safely (or "N/A").
     */
    val formattedVoltageClass: String
        get() = voltageClass?.takeIf { it.isNotBlank() } ?: "N/A"

    /**
     * Formats manufacturer safely (or "N/A").
     */
    val formattedManufacturer: String
        get() = manufacturer?.takeIf { it.isNotBlank() } ?: "N/A"

    /**
     * Formats installation year safely (or "N/A").
     */
    val formattedInstallationYear: String
        get() = installationYear?.toString() ?: "N/A"

    fun toCachedAsset(): CachedAsset {
        return CachedAsset(
            id = id,
            serialNumber = serialNumber,
            name = name,
            category = category.categoryKey,
            kvaRating = kvaRating,
            voltageClass = voltageClass,
            manufacturer = manufacturer,
            installationYear = installationYear,
            status = status,
            substationId = substationId,
            substationName = substationName,
            lastInspectedAt = lastInspectedAt,
            cachedAt = cachedAt
        )
    }
}

fun CachedAsset.toDomain(): Asset {
    return Asset(
        id = id,
        serialNumber = serialNumber,
        name = name,
        category = AssetCategory.fromKey(category),
        kvaRating = kvaRating,
        voltageClass = voltageClass,
        manufacturer = manufacturer,
        installationYear = installationYear,
        status = status,
        substationId = substationId,
        substationName = substationName,
        lastInspectedAt = lastInspectedAt,
        cachedAt = cachedAt
    )
}
