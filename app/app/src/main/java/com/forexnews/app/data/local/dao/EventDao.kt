package com.forexnews.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import androidx.room.Upsert
import com.forexnews.app.data.local.entity.EventEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface EventDao {

    @Query("SELECT * FROM events ORDER BY date_time ASC")
    fun getAllEvents(): Flow<List<EventEntity>>

    @Query("SELECT * FROM events WHERE date_time BETWEEN :startDate AND :endDate ORDER BY date_time ASC")
    fun getEventsByDateRange(startDate: String, endDate: String): Flow<List<EventEntity>>

    @Transaction
    suspend fun replaceAllEvents(events: List<EventEntity>) {
        clearAllEvents()
        insertEvents(events)
    }

    @Query(
        """
        SELECT * FROM events 
        WHERE date_time BETWEEN :startDate AND :endDate
        AND (:currencies IS NULL OR currency IN (:currencyList))
        AND (:impacts IS NULL OR impact IN (:impactList))
        ORDER BY date_time ASC
        """
    )
    fun getFilteredEvents(
        startDate: String,
        endDate: String,
        currencies: String?,
        currencyList: List<String>,
        impacts: String?,
        impactList: List<String>
    ): Flow<List<EventEntity>>

    @Query(
        """
        SELECT * FROM events 
        WHERE date_time BETWEEN :startDate AND :endDate 
        AND impact = 'red' 
        ORDER BY date_time ASC
        """
    )
    fun getHighImpactEvents(startDate: String, endDate: String): Flow<List<EventEntity>>

    @Query(
        """
        SELECT * FROM events 
        WHERE date_time >= :startDate 
        AND impact = 'red' 
        ORDER BY date_time ASC
        """
    )
    fun getHighImpactEventsFrom(startDate: String): Flow<List<EventEntity>>

    @Query("SELECT * FROM events WHERE id = :eventId LIMIT 1")
    fun getEventById(eventId: String): Flow<EventEntity?>

    @Query(
        """
        SELECT * FROM events 
        WHERE title LIKE '%' || :query || '%' 
        OR currency LIKE '%' || :query || '%' 
        OR country LIKE '%' || :query || '%'
        ORDER BY date_time ASC
        """
    )
    fun searchEvents(query: String): Flow<List<EventEntity>>

    @Query(
        """
        SELECT * FROM events 
        WHERE title = :title AND currency = :currency 
        ORDER BY date_time DESC 
        LIMIT 12
        """
    )
    fun getEventHistory(title: String, currency: String): Flow<List<EventEntity>>

    @Upsert
    suspend fun upsertEvents(events: List<EventEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEvents(events: List<EventEntity>)

    @Query("DELETE FROM events WHERE date_time < :beforeDate")
    suspend fun deleteOldEvents(beforeDate: String)

    @Query("SELECT COUNT(*) FROM events")
    suspend fun getEventCount(): Int

    @Query("SELECT * FROM events WHERE id = :eventId LIMIT 1")
    suspend fun getEventByIdSync(eventId: String): EventEntity?

    @Query("DELETE FROM events")
    suspend fun clearAllEvents()
}
