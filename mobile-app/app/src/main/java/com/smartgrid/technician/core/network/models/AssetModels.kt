package com.smartgrid.technician.core.network.models

import com.google.gson.annotations.SerializedName
import com.smartgrid.technician.core.database.CachedAsset
import com.smartgrid.technician.features.assets.domain.Asset
import com.smartgrid.technician.features.assets.domain.AssetCategory

/**
 * Data transfer object representing an asset payload returned by the backend API.
 */
data class AssetDto(
    @SerializedName("id")
    val id: String,

    @SerializedName("serial_number")
    val serialNumber: String,

    @SerializedName("name")
    val name: String,

    @SerializedName("category")
    val category: String,

    @SerializedName("kva_rating")
    val kvaRating: Double? = null,

    @SerializedName("voltage_class")
    val voltageClass: String? = null,

    @SerializedName("manufacturer")
    val manufacturer: String? = null,

    @SerializedName("installation_year")
    val installationYear: Int? = null,

    @SerializedName("status")
    val status: String? = "OPERATIONAL",

    @SerializedName("substation_id")
    val substationId: String? = null,

    @SerializedName("substation_name")
    val substationName: String? = null,

    @SerializedName("last_inspected_at")
    val lastInspectedAt: Long? = null
) {
    fun toDomain(): Asset {
        return Asset(
            id = id,
            serialNumber = serialNumber,
            name = name,
            category = AssetCategory.fromKey(category),
            kvaRating = kvaRating,
            voltageClass = voltageClass,
            manufacturer = manufacturer,
            installationYear = installationYear,
            status = status ?: "OPERATIONAL",
            substationId = substationId,
            substationName = substationName,
            lastInspectedAt = lastInspectedAt
        )
    }

    fun toCachedAsset(): CachedAsset {
        return CachedAsset(
            id = id,
            serialNumber = serialNumber,
            name = name,
            category = category,
            kvaRating = kvaRating,
            voltageClass = voltageClass,
            manufacturer = manufacturer,
            installationYear = installationYear,
            status = status ?: "OPERATIONAL",
            substationId = substationId,
            substationName = substationName,
            lastInspectedAt = lastInspectedAt,
            cachedAt = System.currentTimeMillis()
        )
    }
}
