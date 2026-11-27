package com.smartgrid.technician.features.assets.domain

import com.smartgrid.technician.core.database.CachedAsset
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class AssetDomainTest {

    @Test
    fun `formatting helper functions format technical fields correctly`() {
        val transformer = Asset(
            id = "t1",
            serialNumber = "TRF-001",
            name = "Test Transformer",
            category = AssetCategory.TRANSFORMERS,
            kvaRating = 2500.0,
            voltageClass = "33 kV / 11 kV",
            manufacturer = "Siemens Energy",
            installationYear = 2020,
            status = "OPERATIONAL"
        )

        assertEquals("2500 kVA", transformer.formattedKvaRating)
        assertEquals("33 kV / 11 kV", transformer.formattedVoltageClass)
        assertEquals("Siemens Energy", transformer.formattedManufacturer)
        assertEquals("2020", transformer.formattedInstallationYear)
    }

    @Test
    fun `null or empty technical fields format safely to NA without crashing`() {
        val cable = Asset(
            id = "c1",
            serialNumber = "CBL-001",
            name = "Underground Feeder",
            category = AssetCategory.CABLES,
            kvaRating = null,
            voltageClass = null,
            manufacturer = null,
            installationYear = null,
            status = "OPERATIONAL"
        )

        assertEquals("N/A", cable.formattedKvaRating)
        assertEquals("N/A", cable.formattedVoltageClass)
        assertEquals("N/A", cable.formattedManufacturer)
        assertEquals("N/A", cable.formattedInstallationYear)
    }

    @Test
    fun `conversion between domain and cached entity preserves all fields`() {
        val original = Asset(
            id = "cb_1",
            serialNumber = "CB-SF6-99",
            name = "Gas Breaker",
            category = AssetCategory.CIRCUIT_BREAKERS,
            kvaRating = null,
            voltageClass = "132 kV",
            manufacturer = "ABB",
            installationYear = 2022,
            status = "OPERATIONAL",
            substationId = "SUB-01",
            substationName = "Main Substation",
            lastInspectedAt = 123456789L,
            cachedAt = 987654321L
        )

        val cached: CachedAsset = original.toCachedAsset()
        assertEquals("cb_1", cached.id)
        assertEquals("CB-SF6-99", cached.serialNumber)
        assertEquals("CIRCUIT_BREAKER", cached.category)
        assertNull(cached.kvaRating)
        assertEquals("132 kV", cached.voltageClass)

        val domainBack = cached.toDomain()
        assertEquals(original.id, domainBack.id)
        assertEquals(original.serialNumber, domainBack.serialNumber)
        assertEquals(original.category, domainBack.category)
        assertEquals(original.voltageClass, domainBack.voltageClass)
        assertEquals(original.manufacturer, domainBack.manufacturer)
        assertEquals(original.installationYear, domainBack.installationYear)
    }
}
