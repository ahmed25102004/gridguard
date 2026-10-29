package com.smartgrid.technician.core.database

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FieldRecordTest {

    @Test
    fun `field record creation sets default values and fields correctly`() {
        val record = FieldRecord(
            id = "rec_001",
            assetId = "transformer_substation_4",
            technicianId = "tech_12",
            inspectionNotes = "Voltage levels normal, oil pressure stable.",
            status = "INSPECTED"
        )

        assertEquals("rec_001", record.id)
        assertEquals("transformer_substation_4", record.assetId)
        assertEquals("tech_12", record.technicianId)
        assertEquals("Voltage levels normal, oil pressure stable.", record.inspectionNotes)
        assertEquals("INSPECTED", record.status)
        assertFalse(record.isSynced)
        assertTrue(record.timestamp > 0)
    }

    @Test
    fun `field record copy allows updating sync status`() {
        val original = FieldRecord(
            id = "rec_002",
            assetId = "circuit_breaker_9",
            technicianId = "tech_12",
            inspectionNotes = "Trip test successful.",
            status = "PASSED",
            isSynced = false
        )

        val synced = original.copy(isSynced = true)

        assertFalse(original.isSynced)
        assertTrue(synced.isSynced)
    }
}
