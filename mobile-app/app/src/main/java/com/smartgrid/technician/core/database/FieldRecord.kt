package com.smartgrid.technician.core.database

/**
 * Domain entity representing an offline field inspection or work record stored in the encrypted database.
 */
data class FieldRecord(
    val id: String,
    val assetId: String,
    val technicianId: String,
    val inspectionNotes: String,
    val status: String,
    val timestamp: Long = System.currentTimeMillis(),
    val isSynced: Boolean = false
)
