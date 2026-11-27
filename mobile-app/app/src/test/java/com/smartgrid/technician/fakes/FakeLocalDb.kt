package com.smartgrid.technician.fakes

import com.smartgrid.technician.core.database.CachedAsset
import com.smartgrid.technician.core.database.FieldRecord
import com.smartgrid.technician.core.database.LocalDb

/**
 * In-memory test double for LocalDb supporting full offline cache validation.
 */
class FakeLocalDb : LocalDb {

    private val fieldRecords = mutableMapOf<String, FieldRecord>()
    private val cachedAssets = mutableMapOf<String, CachedAsset>()
    private var initialized = false

    override fun initialize(passphrase: ByteArray): Boolean {
        initialized = true
        return true
    }

    override fun isInitialized(): Boolean = initialized

    override fun saveFieldRecord(record: FieldRecord): Long {
        fieldRecords[record.id] = record
        return 1L
    }

    override fun getFieldRecords(): List<FieldRecord> {
        return fieldRecords.values.sortedByDescending { it.timestamp }
    }

    override fun getPendingSyncRecords(): List<FieldRecord> {
        return fieldRecords.values.filter { !it.isSynced }.sortedBy { it.timestamp }
    }

    override fun markRecordSynced(id: String): Boolean {
        val existing = fieldRecords[id] ?: return false
        fieldRecords[id] = existing.copy(isSynced = true)
        return true
    }

    override fun clearAllRecords() {
        fieldRecords.clear()
    }

    override fun saveAsset(asset: CachedAsset): Long {
        cachedAssets[asset.id] = asset
        return 1L
    }

    override fun saveAssets(assets: List<CachedAsset>): Int {
        var count = 0
        for (asset in assets) {
            cachedAssets[asset.id] = asset
            count++
        }
        return count
    }

    override fun getCachedAssets(category: String?, searchQuery: String?): List<CachedAsset> {
        return cachedAssets.values.filter { asset ->
            val matchesCategory = if (category.isNullOrBlank() || category.equals("ALL", ignoreCase = true)) {
                true
            } else {
                asset.category.equals(category, ignoreCase = true)
            }

            val matchesSearch = if (searchQuery.isNullOrBlank()) {
                true
            } else {
                val q = searchQuery.trim()
                asset.serialNumber.contains(q, ignoreCase = true) || asset.name.contains(q, ignoreCase = true)
            }

            matchesCategory && matchesSearch
        }.sortedWith(compareBy({ it.category }, { it.name }))
    }

    override fun getCachedAssetById(id: String): CachedAsset? {
        return cachedAssets[id]
    }

    override fun getCachedAssetBySerialNumber(serialNumber: String): CachedAsset? {
        return cachedAssets.values.firstOrNull {
            it.serialNumber.equals(serialNumber, ignoreCase = true)
        }
    }

    override fun deleteCachedAsset(id: String): Boolean {
        return cachedAssets.remove(id) != null
    }

    override fun clearAllCachedAssets(): Int {
        val size = cachedAssets.size
        cachedAssets.clear()
        return size
    }

    override fun getCachedAssetCount(): Int {
        return cachedAssets.size
    }

    override fun close() {
        initialized = false
    }
}
