package com.smartgrid.technician.core.database

import android.content.ContentValues
import android.content.Context
import android.util.Log
import net.sqlcipher.Cursor
import net.sqlcipher.database.SQLiteDatabase
import java.io.File

/**
- Interface defining local encrypted database operations for offline technician records.
 */
interface LocalDb {
    fun initialize(passphrase: ByteArray): Boolean
    fun isInitialized(): Boolean
    fun saveFieldRecord(record: FieldRecord): Long
    fun getFieldRecords(): List<FieldRecord>
    fun getPendingSyncRecords(): List<FieldRecord>
    fun markRecordSynced(id: String): Boolean
    fun clearAllRecords()
    fun close()
}

/**
- Encrypted SQLite implementation using SQLCipher with AES-256 encryption.
- The encryption key is supplied as a raw 256-bit passphrase obtained from Android Keystore.
 */
class SqlCipherLocalDb(
    private val context: Context,
    private val databaseName: String = DB_NAME
) : LocalDb {

    private var database: SQLiteDatabase? = null

    companion object {
        private const val TAG = "SqlCipherLocalDb"
        const val DB_NAME = "smartgrid_technician_encrypted.db"

        const val TABLE_FIELD_RECORDS = "field_records"
        const val COL_ID = "id"
        const val COL_ASSET_ID = "asset_id"
        const val COL_TECHNICIAN_ID = "technician_id"
        const val COL_INSPECTION_NOTES = "inspection_notes"
        const val COL_STATUS = "status"
        const val COL_TIMESTAMP = "timestamp"
        const val COL_IS_SYNCED = "is_synced"

        private var isNativeLibLoaded = false

        private fun loadNativeLibrary(context: Context) {
            if (!isNativeLibLoaded) {
                try {
                    SQLiteDatabase.loadLibs(context)
                    isNativeLibLoaded = true
                } catch (e: UnsatisfiedLinkError) {
                    Log.w(TAG, "SQLCipher native library could not be loaded directly: ${e.message}")
                }
            }
        }
    }

    override fun initialize(passphrase: ByteArray): Boolean {
        return synchronized(this) {
            try {
                loadNativeLibrary(context)
                val dbFile: File = context.getDatabasePath(databaseName)
                if (!dbFile.parentFile.exists()) {
                    dbFile.parentFile.mkdirs()
                }

                // Open or create SQLiteDatabase encrypted with SQLCipher AES-256
                database = SQLiteDatabase.openOrCreateDatabase(dbFile.absolutePath, String(passphrase, Charsets.UTF_8), null)
                createTablesIfNotExist()
                Log.d(TAG, "Encrypted SQLCipher database initialized successfully.")
                true
            } catch (e: Exception) {
                Log.e(TAG, "Failed to initialize encrypted database: ${e.message}", e)
                database = null
                false
            }
        }
    }

    private fun createTablesIfNotExist() {
        val createSql = """
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
        database?.execSQL(createSql)
    }

    override fun isInitialized(): Boolean {
        return synchronized(this) {
            database != null && database?.isOpen == true
        }
    }

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
                Log.e(TAG, "Error querying field records: ${e.message}", e)
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
                Log.e(TAG, "Error querying pending sync records: ${e.message}", e)
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

    override fun close() {
        synchronized(this) {
            try {
                database?.close()
            } catch (_: Exception) {}
            database = null
        }
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