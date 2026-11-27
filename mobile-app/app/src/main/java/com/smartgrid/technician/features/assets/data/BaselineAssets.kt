package com.smartgrid.technician.features.assets.data

import com.smartgrid.technician.features.assets.domain.Asset
import com.smartgrid.technician.features.assets.domain.AssetCategory

/**
 * Standard baseline asset registry dataset for initial local cache initialization.
 * Clearly identified as local demo/sample data to distinguish from real backend data.
 * Covers all required asset categories: Transformers, Circuit Breakers, and Cables.
 */
object BaselineAssets {

    val initialList: List<Asset> = listOf(
        // Transformers
        Asset(
            id = "demo_trf_001",
            serialNumber = "TRF-9021-TX",
            name = "[Demo] Primary Substation Step-Down Transformer T1",
            category = AssetCategory.TRANSFORMERS,
            kvaRating = 2500.0,
            voltageClass = "33 kV / 11 kV",
            manufacturer = "Siemens Energy",
            installationYear = 2019,
            status = "OPERATIONAL (SAMPLE)",
            substationId = "SUB-NORTH-01",
            substationName = "North Central Substation (Sample Vault)",
            lastInspectedAt = System.currentTimeMillis() - 86400000L * 14
        ),
        Asset(
            id = "demo_trf_002",
            serialNumber = "TRF-4412-HV",
            name = "[Demo] Auxiliary Distribution Transformer T2",
            category = AssetCategory.TRANSFORMERS,
            kvaRating = 1000.0,
            voltageClass = "11 kV / 415 V",
            manufacturer = "ABB Power Grids",
            installationYear = 2021,
            status = "OPERATIONAL (SAMPLE)",
            substationId = "SUB-SOUTH-04",
            substationName = "South Valley Substation (Sample Vault)",
            lastInspectedAt = System.currentTimeMillis() - 86400000L * 30
        ),

        // Circuit Breakers
        Asset(
            id = "demo_cb_001",
            serialNumber = "CB-404-SF6",
            name = "[Demo] High-Voltage SF6 Gas Circuit Breaker Q01",
            category = AssetCategory.CIRCUIT_BREAKERS,
            kvaRating = null,
            voltageClass = "132 kV",
            manufacturer = "Schneider Electric",
            installationYear = 2020,
            status = "OPERATIONAL (SAMPLE)",
            substationId = "SUB-NORTH-01",
            substationName = "North Central Substation (Sample Vault)",
            lastInspectedAt = System.currentTimeMillis() - 86400000L * 7
        ),
        Asset(
            id = "demo_cb_002",
            serialNumber = "CB-882-VAC",
            name = "[Demo] Medium-Voltage Vacuum Circuit Breaker Q02",
            category = AssetCategory.CIRCUIT_BREAKERS,
            kvaRating = null,
            voltageClass = "33 kV",
            manufacturer = "Eaton Electrical",
            installationYear = 2022,
            status = "MAINTENANCE_REQUIRED (SAMPLE)",
            substationId = "SUB-WEST-02",
            substationName = "West Ridge Substation (Sample Vault)",
            lastInspectedAt = System.currentTimeMillis() - 86400000L * 60
        ),

        // Cables
        Asset(
            id = "demo_cbl_001",
            serialNumber = "CBL-HV-132-A",
            name = "[Demo] XLPE Underground Transmission Feeder A1",
            category = AssetCategory.CABLES,
            kvaRating = null,
            voltageClass = "132 kV",
            manufacturer = "Prysmian Group",
            installationYear = 2018,
            status = "OPERATIONAL (SAMPLE)",
            substationId = "SUB-NORTH-01",
            substationName = "North Central Substation (Sample Vault)",
            lastInspectedAt = System.currentTimeMillis() - 86400000L * 90
        ),
        Asset(
            id = "demo_cbl_002",
            serialNumber = "CBL-MV-033-B",
            name = "[Demo] Armored Substation Intertie Feeder B2",
            category = AssetCategory.CABLES,
            kvaRating = null,
            voltageClass = "33 kV",
            manufacturer = "Nexans Power",
            installationYear = 2023,
            status = "OPERATIONAL (SAMPLE)",
            substationId = "SUB-EAST-03",
            substationName = "East Industrial Substation (Sample Vault)",
            lastInspectedAt = System.currentTimeMillis() - 86400000L * 20
        )
    )
}
