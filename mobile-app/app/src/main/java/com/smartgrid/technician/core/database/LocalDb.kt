package com.smartgrid.technician.core.database

import android.content.ContentValues
import android.content.Context
import android.util.Log
import net.sqlcipher.Cursor
import net.sqlcipher.database.SQLiteDatabase
import java.io.File

/**
 * Interface defining local encrypted database operations for offline technician records and assets.
 */
interface LocalDb {
    fun initialize(passphrase: ByteArray): Boolean
    fun isInitialized(): Boolean

    // Field Records operations
    fun saveFieldRecord(record: FieldRecord): Long
    fun getFieldRecords(): List<FieldRecord>
    fun getPendingSyncRecords(): List<FieldRecord>
    fun markRecordSynced(id: String): Boolean
    fun clearAllRecords()

    // Encrypted Asset Cache operations
    fun saveAsset(asset: CachedAsset): Long
    fun saveAssets(assets: List<CachedAsset>): Int
    fun getCachedAssets(category: String? = null, searchQuery: String? = null): List<CachedAsset>
    fun getCachedAssetById(id: String): CachedAsset?
    fun getCachedAssetBySerialNumber(serialNumber: String): CachedAsset?
    fun deleteCachedAsset(id: String): Boolean
    fun clearAllCachedAssets(): Int
    fun getCachedAssetCount(): Int

    fun close()
}

/**
 * Encrypted SQLite implementation using SQLCipher with AES-256 encryption.
 * The encryption key is supplied as a raw 256-bit passphrase obtained from Android Keystore.
 */
class SqlCipherLocalDb(
    private val context: Context,
    private val databaseName: String = DB_NAME
) : LocalDb {

    private var database: SQLiteDatabase? = null

    companion object {
        private const val TAG = "SqlCipherLocalDb"
        const val DB_NAME = "smartgrid_technician_encrypted.db"

        // Field Records Table
        const val TABLE_FIELD_RECORDS = "field_records"
        const val COL_ID = "id"
        const val COL_ASSET_ID = "asset_id"
        const val COL_TECHNICIAN_ID = "technician_id"
        const val COL_INSPECTION_NOTES = "inspection_notes"
        const val COL_STATUS = "status"
        const val COL_TIMESTAMP = "timestamp"
        const val COL_IS_SYNCED = "is_synced"

        // Cached Assets Table
        const val TABLE_CACHED_ASSETS = "cached_assets"
        const val COL_ASSET_PK_ID = "id"
        const val COL_ASSET_SERIAL = "serial_number"
        const val COL_ASSET_NAME = "name"
        const val COL_ASSET_CATEGORY = "category"
        const val COL_ASSET_KVA_RATING = "kva_rating"
        const val COL_ASSET_VOLTAGE_CLASS = "voltage_class"
        const val COL_ASSET_MANUFACTURER = "manufacturer"
        const val COL_ASSET_INSTALLATION_YEAR = "installation_year"
        const val COL_ASSET_STATUS = "status"
        const val COL_ASSET_SUBSTATION_ID = "substation_id"
        const val COL_ASSET_SUBSTATION_NAME = "substation_name"
        const val COL_ASSET_LAST_INSPECTED_AT = "last_inspected_at"
        const val COL_ASSET_CACHED_AT = "cached_at"

        private var isNativeLibLoaded = false

        private fun logDebug(msg: String) {
            try { Log.d(TAG, msg) } catch (_: Throwable) {}
        }

        private fun logWarn(msg: String, tr: Throwable? = null) {
            try { if (tr != null) Log.w(TAG, msg, tr) else Log.w(TAG, msg) } catch (_: Throwable) {}
        }

        private fun logErr(msg: String, tr: Throwable? = null) {
            try { if (tr != null) Log.e(TAG, msg, tr) else Log.e(TAG, msg) } catch (_: Throwable) {}
        }

        private fun loadNativeLibrary(context: Context) {
            if (!isNativeLibLoaded) {
                try {
                    SQLiteDatabase.loadLibs(context)
                    isNativeLibLoaded = true
                } catch (e: UnsatisfiedLinkError) {
                    logWarn("SQLCipher native library could not be loaded directly: ${e.message}")
                }
            }
        }
    }

    override fun initialize(passphrase: ByteArray): Boolean {
        return synchronized(this) {
            try {
                loadNativeLibrary(context)
                val dbFile: File = context.getDatabasePath(databaseName)
                dbFile.parentFile?.let { parent ->
                    if (!parent.exists()) {
                        parent.mkdirs()
                    }
                }

                // Open or create SQLiteDatabase encrypted with SQLCipher AES-256
                database = SQLiteDatabase.openOrCreateDatabase(
                    dbFile.absolutePath,
                    String(passphrase, Charsets.UTF_8),
                    null
                )
                createTablesIfNotExist()
                logDebug("Encrypted SQLCipher database initialized successfully.")
                true
            } catch (e: Exception) {
                logErr("Failed to initialize encrypted database: ${e.message}", e)
                database = null
                false
            }
        }
    }

    private fun createTablesIfNotExist() {
        // Field Records
        val createFieldRecordsSql = """
            CREATE TABLE IF NOT EXISTS $TABLE_FIELD_RECORDS (
                $COL_ID TEXT PRIMARY KEY,
                $COL_ASSET_ID TEXT NOT NULL,
                $COL_TECHNICIAN_ID TEXT NOT NULL,
                $COL_INSPECTION_NOTES TEXT,
                $COL_STATUS TEXT NOT NULL,
                $COL_TIMESTAMP INTEGER NOT NULL,
                $COL_IS_SYNCED INTEGER NOT NULL DEFAULT 0
            )
        """.trimIndent()
        database?.execSQL(createFieldRecordsSql)

        // Cached Assets with technical fields and indexes
        val createCachedAssetsSql = """
            CREATE TABLE IF NOT EXISTS $TABLE_CACHED_ASSETS (
                $COL_ASSET_PK_ID TEXT PRIMARY KEY,
                $COL_ASSET_SERIAL TEXT NOT NULL UNIQUE,
                $COL_ASSET_NAME TEXT NOT NULL,
                $COL_ASSET_CATEGORY TEXT NOT NULL,
                $COL_ASSET_KVA_RATING REAL,
                $COL_ASSET_VOLTAGE_CLASS TEXT,
                $COL_ASSET_MANUFACTURER TEXT,
                $COL_ASSET_INSTALLATION_YEAR INTEGER,
                $COL_ASSET_STATUS TEXT NOT NULL,
                $COL_ASSET_SUBSTATION_ID TEXT,
                $COL_ASSET_SUBSTATION_NAME TEXT,
                $COL_ASSET_LAST_INSPECTED_AT INTEGER,
                $COL_ASSET_CACHED_AT INTEGER NOT NULL
            )
        """.trimIndent()
        database?.execSQL(createCachedAssetsSql)

        val createCategoryIndexSql = """
            CREATE INDEX IF NOT EXISTS idx_cached_assets_category ON $TABLE_CACHED_ASSETS ($COL_ASSET_CATEGORY)
        """.trimIndent()
        database?.execSQL(createCategoryIndexSql)

        val createSerialIndexSql = """
            CREATE INDEX IF NOT EXISTS idx_cached_assets_serial ON $TABLE_CACHED_ASSETS ($COL_ASSET_SERIAL)
        """.trimIndent()
        database?.execSQL(createSerialIndexSql)
    }

    override fun isInitialized(): Boolean {
        return synchronized(this) {
            database != null && database?.isOpen == true
        }
    }

    // ==========================================
    // Field Records implementation
    // ==========================================

    override fun saveFieldRecord(record: FieldRecord): Long {
        return synchronized(this) {
            val db = database ?: return -1L
            val values = ContentValues().apply {
                put(COL_ID, record.id)
                put(COL_ASSET_ID, record.assetId)
                put(COL_TECHNICIAN_ID, record.technicianId)
                put(COL_INSPECTION_NOTES, record.inspectionNotes)
                put(COL_STATUS, record.status)
                put(COL_TIMESTAMP, record.timestamp)
                put(COL_IS_SYNCED, if (record.isSynced) 1 else 0)
            }
            db.insertWithOnConflict(
                TABLE_FIELD_RECORDS,
                null,
                values,
                SQLiteDatabase.CONFLICT_REPLACE
            )
        }
    }

    override fun getFieldRecords(): List<FieldRecord> {
        return synchronized(this) {
            val db = database ?: return emptyList()
            val list = mutableListOf<FieldRecord>()
            var cursor: Cursor? = null
            try {
                cursor = db.query(
                    TABLE_FIELD_RECORDS,
                    null,
                    null,
                    null,
                    null,
                    null,
                    "$COL_TIMESTAMP DESC"
                )
                while (cursor != null && cursor.moveToNext()) {
                    list.add(cursorToFieldRecord(cursor))
                }
            } catch (e: Exception) {
                logErr("Error querying field records: ${e.message}", e)
            } finally {
                cursor?.close()
            }
            list
        }
    }

    override fun getPendingSyncRecords(): List<FieldRecord> {
        return synchronized(this) {
            val db = database ?: return emptyList()
            val list = mutableListOf<FieldRecord>()
            var cursor: Cursor? = null
            try {
                cursor = db.query(
                    TABLE_FIELD_RECORDS,
                    null,
                    "$COL_IS_SYNCED = ?",
                    arrayOf("0"),
                    null,
                    null,
                    "$COL_TIMESTAMP ASC"
                )
                while (cursor != null && cursor.moveToNext()) {
                    list.add(cursorToFieldRecord(cursor))
                }
            } catch (e: Exception) {
                logErr("Error querying pending sync records: ${e.message}", e)
            } finally {
                cursor?.close()
            }
            list
        }
    }

    override fun markRecordSynced(id: String): Boolean {
        return synchronized(this) {
            val db = database ?: return false
            val values = ContentValues().apply {
                put(COL_IS_SYNCED, 1)
            }
            val rows = db.update(
                TABLE_FIELD_RECORDS,
                values,
                "$COL_ID = ?",
                arrayOf(id)
            )
            rows > 0
        }
    }

    override fun clearAllRecords() {
        synchronized(this) {
            database?.delete(TABLE_FIELD_RECORDS, null, null)
        }
    }

    // ==========================================
    // Encrypted Asset Cache Implementation
    // ==========================================

    override fun saveAsset(asset: CachedAsset): Long {
        return synchronized(this) {
            val db = database ?: return -1L
            val values = assetToContentValues(asset)
            db.insertWithOnConflict(
                TABLE_CACHED_ASSETS,
                null,
                values,
                SQLiteDatabase.CONFLICT_REPLACE
            )
        }
    }

    override fun saveAssets(assets: List<CachedAsset>): Int {
        return synchronized(this) {
            val db = database ?: return 0
            var count = 0
            db.beginTransaction()
            try {
                for (asset in assets) {
                    val values = assetToContentValues(asset)
                    val result = db.insertWithOnConflict(
                        TABLE_CACHED_ASSETS,
                        null,
                        values,
                        SQLiteDatabase.CONFLICT_REPLACE
                    )
                    if (result != -1L) {
                        count++
                    }
                }
                db.setTransactionSuccessful()
            } catch (e: Exception) {
                logErr("Error saving batch of cached assets: ${e.message}", e)
            } finally {
                db.endTransaction()
            }
            count
        }
    }

    override fun getCachedAssets(category: String?, searchQuery: String?): List<CachedAsset> {
        return synchronized(this) {
            val db = database ?: return emptyList()
            val list = mutableListOf<CachedAsset>()
            var cursor: Cursor? = null

            val selectionClauses = mutableListOf<String>()
            val selectionArgs = mutableListOf<String>()

            // Filter by category if specified and not "ALL"
            if (!category.isNullOrBlank() && !category.equals("ALL", ignoreCase = true)) {
                selectionClauses.add("$COL_ASSET_CATEGORY = ?")
                selectionArgs.add(category)
            }

            // Local search by serial number or name
            if (!searchQuery.isNullOrBlank()) {
                val queryPattern = "%${searchQuery.trim()}%"
                selectionClauses.add("($COL_ASSET_SERIAL LIKE ? OR $COL_ASSET_NAME LIKE ?)")
                selectionArgs.add(queryPattern)
                selectionArgs.add(queryPattern)
            }

            val selection = if (selectionClauses.isNotEmpty()) {
                selectionClauses.joinToString(" AND ")
            } else null

            val args = if (selectionArgs.isNotEmpty()) {
                selectionArgs.toTypedArray()
            } else null

            try {
                cursor = db.query(
                    TABLE_CACHED_ASSETS,
                    null,
                    selection,
                    args,
                    null,
                    null,
                    "$COL_ASSET_CATEGORY ASC, $COL_ASSET_NAME ASC"
                )
                while (cursor != null && cursor.moveToNext()) {
                    list.add(cursorToCachedAsset(cursor))
                }
            } catch (e: Exception) {
                logErr("Error querying cached assets: ${e.message}", e)
            } finally {
                cursor?.close()
            }
            list
        }
    }

    override fun getCachedAssetById(id: String): CachedAsset? {
        return synchronized(this) {
            val db = database ?: return null
            var cursor: Cursor? = null
            try {
                cursor = db.query(
                    TABLE_CACHED_ASSETS,
                    null,
                    "$COL_ASSET_PK_ID = ?",
                    arrayOf(id),
                    null,
                    null,
                    null,
                    "1"
                )
                if (cursor != null && cursor.moveToNext()) {
                    return cursorToCachedAsset(cursor)
                }
            } catch (e: Exception) {
                logErr("Error querying cached asset by ID: ${e.message}", e)
            } finally {
                cursor?.close()
            }
            null
        }
    }

    override fun getCachedAssetBySerialNumber(serialNumber: String): CachedAsset? {
        return synchronized(this) {
            val db = database ?: return null
            var cursor: Cursor? = null
            try {
                cursor = db.query(
                    TABLE_CACHED_ASSETS,
                    null,
                    "$COL_ASSET_SERIAL = ?",
                    arrayOf(serialNumber),
                    null,
                    null,
                    null,
                    "1"
                )
                if (cursor != null && cursor.moveToNext()) {
                    return cursorToCachedAsset(cursor)
                }
            } catch (e: Exception) {
                logErr("Error querying cached asset by serial number: ${e.message}", e)
            } finally {
                cursor?.close()
            }
            null
        }
    }

    override fun deleteCachedAsset(id: String): Boolean {
        return synchronized(this) {
            val db = database ?: return false
            val rows = db.delete(
                TABLE_CACHED_ASSETS,
                "$COL_ASSET_PK_ID = ?",
                arrayOf(id)
            )
            rows > 0
        }
    }

    override fun clearAllCachedAssets(): Int {
        return synchronized(this) {
            database?.delete(TABLE_CACHED_ASSETS, null, null) ?: 0
        }
    }

    override fun getCachedAssetCount(): Int {
        return synchronized(this) {
            val db = database ?: return 0
            var cursor: Cursor? = null
            try {
                cursor = db.rawQuery("SELECT COUNT(*) FROM $TABLE_CACHED_ASSETS", null)
                if (cursor != null && cursor.moveToNext()) {
                    return cursor.getInt(0)
                }
            } catch (e: Exception) {
                logErr("Error counting cached assets: ${e.message}", e)
            } finally {
                cursor?.close()
            }
            0
        }
    }

    override fun close() {
        synchronized(this) {
            try {
                database?.close()
            } catch (_: Exception) {}
            database = null
        }
    }

    // ==========================================
    // Private Helpers
    // ==========================================

    private fun assetToContentValues(asset: CachedAsset): ContentValues {
        return ContentValues().apply {
            put(COL_ASSET_PK_ID, asset.id)
            put(COL_ASSET_SERIAL, asset.serialNumber)
            put(COL_ASSET_NAME, asset.name)
            put(COL_ASSET_CATEGORY, asset.category)
            if (asset.kvaRating != null) put(COL_ASSET_KVA_RATING, asset.kvaRating) else putNull(COL_ASSET_KVA_RATING)
            if (asset.voltageClass != null) put(COL_ASSET_VOLTAGE_CLASS, asset.voltageClass) else putNull(COL_ASSET_VOLTAGE_CLASS)
            if (asset.manufacturer != null) put(COL_ASSET_MANUFACTURER, asset.manufacturer) else putNull(COL_ASSET_MANUFACTURER)
            if (asset.installationYear != null) put(COL_ASSET_INSTALLATION_YEAR, asset.installationYear) else putNull(COL_ASSET_INSTALLATION_YEAR)
            put(COL_ASSET_STATUS, asset.status)
            if (asset.substationId != null) put(COL_ASSET_SUBSTATION_ID, asset.substationId) else putNull(COL_ASSET_SUBSTATION_ID)
            if (asset.substationName != null) put(COL_ASSET_SUBSTATION_NAME, asset.substationName) else putNull(COL_ASSET_SUBSTATION_NAME)
            if (asset.lastInspectedAt != null) put(COL_ASSET_LAST_INSPECTED_AT, asset.lastInspectedAt) else putNull(COL_ASSET_LAST_INSPECTED_AT)
            put(COL_ASSET_CACHED_AT, asset.cachedAt)
        }
    }

    private fun cursorToCachedAsset(cursor: Cursor): CachedAsset {
        val id = cursor.getString(cursor.getColumnIndexOrThrow(COL_ASSET_PK_ID))
        val serial = cursor.getString(cursor.getColumnIndexOrThrow(COL_ASSET_SERIAL))
        val name = cursor.getString(cursor.getColumnIndexOrThrow(COL_ASSET_NAME))
        val category = cursor.getString(cursor.getColumnIndexOrThrow(COL_ASSET_CATEGORY))

        val kvaIdx = cursor.getColumnIndexOrThrow(COL_ASSET_KVA_RATING)
        val kvaRating = if (!cursor.isNull(kvaIdx)) cursor.getDouble(kvaIdx) else null

        val voltIdx = cursor.getColumnIndexOrThrow(COL_ASSET_VOLTAGE_CLASS)
        val voltageClass = if (!cursor.isNull(voltIdx)) cursor.getString(voltIdx) else null

        val mfgIdx = cursor.getColumnIndexOrThrow(COL_ASSET_MANUFACTURER)
        val manufacturer = if (!cursor.isNull(mfgIdx)) cursor.getString(mfgIdx) else null

        val yrIdx = cursor.getColumnIndexOrThrow(COL_ASSET_INSTALLATION_YEAR)
        val installationYear = if (!cursor.isNull(yrIdx)) cursor.getInt(yrIdx) else null

        val status = cursor.getString(cursor.getColumnIndexOrThrow(COL_ASSET_STATUS))

        val subIdIdx = cursor.getColumnIndexOrThrow(COL_ASSET_SUBSTATION_ID)
        val substationId = if (!cursor.isNull(subIdIdx)) cursor.getString(subIdIdx) else null

        val subNameIdx = cursor.getColumnIndexOrThrow(COL_ASSET_SUBSTATION_NAME)
        val substationName = if (!cursor.isNull(subNameIdx)) cursor.getString(subNameIdx) else null

        val inspIdx = cursor.getColumnIndexOrThrow(COL_ASSET_LAST_INSPECTED_AT)
        val lastInspectedAt = if (!cursor.isNull(inspIdx)) cursor.getLong(inspIdx) else null

        val cachedAt = cursor.getLong(cursor.getColumnIndexOrThrow(COL_ASSET_CACHED_AT))

        return CachedAsset(
            id = id,
            serialNumber = serial,
            name = name,
            category = category,
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

    private fun cursorToFieldRecord(cursor: Cursor): FieldRecord {
        val id = cursor.getString(cursor.getColumnIndexOrThrow(COL_ID))
        val assetId = cursor.getString(cursor.getColumnIndexOrThrow(COL_ASSET_ID))
        val technicianId = cursor.getString(cursor.getColumnIndexOrThrow(COL_TECHNICIAN_ID))
        val notes = cursor.getString(cursor.getColumnIndexOrThrow(COL_INSPECTION_NOTES)) ?: ""
        val status = cursor.getString(cursor.getColumnIndexOrThrow(COL_STATUS))
        val timestamp = cursor.getLong(cursor.getColumnIndexOrThrow(COL_TIMESTAMP))
        val isSynced = cursor.getInt(cursor.getColumnIndexOrThrow(COL_IS_SYNCED)) == 1

        return FieldRecord(
            id = id,
            assetId = assetId,
            technicianId = technicianId,
            inspectionNotes = notes,
            status = status,
            timestamp = timestamp,
            isSynced = isSynced
        )
    }
}
