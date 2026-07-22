package com.forexnews.app.data.repository

import com.forexnews.app.BuildConfig
import com.forexnews.app.data.local.dao.EventDao
import com.forexnews.app.data.local.dao.FavoriteDao
import com.forexnews.app.data.local.dao.SyncMetadataDao
import com.forexnews.app.data.local.entity.SyncMetadataEntity
import com.forexnews.app.data.remote.api.ForexNewsApi
import com.forexnews.app.data.remote.mapper.DtoMapper
import com.forexnews.app.domain.model.CalendarFilter
import com.forexnews.app.domain.model.Currency
import com.forexnews.app.domain.model.EconomicEvent
import com.forexnews.app.domain.model.Impact
import com.forexnews.app.domain.repository.EventRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import timber.log.Timber
import java.time.DayOfWeek
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import java.time.temporal.TemporalAdjusters
import javax.inject.Inject
import javax.inject.Singleton
import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import com.forexnews.app.data.remote.dto.NewsResponseDto

@Singleton
class EventRepositoryImpl @Inject constructor(
    @ApplicationContext private val context: Context,
    private val eventDao: EventDao,
    private val favoriteDao: FavoriteDao,
    private val syncMetadataDao: SyncMetadataDao,
    private val api: ForexNewsApi,
    private val mapper: DtoMapper
) : EventRepository {

    private val isoFormatter = DateTimeFormatter.ISO_LOCAL_DATE_TIME

    override fun getTodayHighImpactEvents(): Flow<List<EconomicEvent>> {
        val today = LocalDate.now()
        val startOfDay = LocalDateTime.of(today, LocalTime.MIN).format(isoFormatter)
        val endOfDay = LocalDateTime.of(today, LocalTime.MAX).format(isoFormatter)

        return combine(
            eventDao.getEventsByDateRange(startOfDay, endOfDay),
            favoriteDao.getAllFavoriteIds()
        ) { events, favoriteIds ->
            events
                .filter { it.impact == "red" } // High impact only on home screen
                .map { entity ->
                    mapper.entityToDomain(entity, favoriteIds.contains(entity.id))
                }
        }
    }


    override fun getEventsByFilter(
        filter: CalendarFilter,
        currencies: List<Currency>?,
        impacts: List<Impact>?,
        searchQuery: String?
    ): Flow<List<EconomicEvent>> {
        val (startDate, endDate) = getDateRange(filter)
        val start = LocalDateTime.of(startDate, LocalTime.MIN).format(isoFormatter)
        val end = LocalDateTime.of(endDate, LocalTime.MAX).format(isoFormatter)

        val eventsFlow = if (searchQuery.isNullOrBlank()) {
            if (currencies == null && impacts == null) {
                eventDao.getEventsByDateRange(start, end)
            } else {
                val currencyList = if (currencies.isNullOrEmpty()) listOf("") else currencies.map { it.code }
                val impactList = if (impacts.isNullOrEmpty()) listOf("") else impacts.map { impactToColor(it) }
                eventDao.getFilteredEvents(
                    startDate = start,
                    endDate = end,
                    currencies = if (currencies != null) "set" else null,
                    currencyList = currencyList,
                    impacts = if (impacts != null) "set" else null,
                    impactList = impactList
                )
            }
        } else {
            eventDao.searchEvents(searchQuery)
        }

        return combine(eventsFlow, favoriteDao.getAllFavoriteIds()) { events, favoriteIds ->
            events.map { entity ->
                mapper.entityToDomain(entity, favoriteIds.contains(entity.id))
            }
        }
    }

    override fun getEventById(id: String): Flow<EconomicEvent?> {
        return combine(
            eventDao.getEventById(id),
            favoriteDao.isFavorite(id)
        ) { entity, isFav ->
            entity?.let { mapper.entityToDomain(it, isFav) }
        }
    }

    override fun searchEvents(query: String): Flow<List<EconomicEvent>> {
        return combine(
            eventDao.searchEvents(query),
            favoriteDao.getAllFavoriteIds()
        ) { events, favoriteIds ->
            events.map { entity ->
                mapper.entityToDomain(entity, favoriteIds.contains(entity.id))
            }
        }
    }

    override fun getEventHistory(eventTitle: String, currency: String): Flow<List<EconomicEvent>> {
        return eventDao.getEventHistory(eventTitle, currency).map { entities ->
            entities.map { mapper.entityToDomain(it) }
        }
    }



    override suspend fun syncEvents(): Result<Unit> {
        return try {
            val cdnUrl = "https://cdn.jsdelivr.net/gh/VenomxTeam/Forex-News@main/scraper/news.json"
            val response = api.getNewsJson(cdnUrl)
            
            val entities = mapper.dtosToEntities(response.events)
            if (entities.isNotEmpty()) {
                eventDao.replaceAllEvents(entities)
                
                val newMetadata = SyncMetadataEntity(
                    syncKey = SYNC_KEY_EVENTS,
                    lastSync = System.currentTimeMillis()
                )
                syncMetadataDao.upsert(newMetadata)
                Timber.d("Successfully synced %d events from CDN", entities.size)
            }
            Result.success(Unit)
        } catch (e: Exception) {
            Timber.e(e, "Failed to sync events from cdn JSON, trying local assets fallback")
            
            // Fallback to local assets/news.json
            try {
                val jsonString = context.assets.open("news.json").bufferedReader().use { it.readText() }
                val moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build()
                val jsonAdapter = moshi.adapter(NewsResponseDto::class.java)
                val response = jsonAdapter.fromJson(jsonString)
                if (response != null) {
                    val fallbackEntities = mapper.dtosToEntities(response.events)
                    if (fallbackEntities.isNotEmpty()) {
                        eventDao.replaceAllEvents(fallbackEntities)
                        Timber.d("Successfully synced %d events from local fallback", fallbackEntities.size)
                    }
                }
                Result.success(Unit)
            } catch (ex: Exception) {
                Timber.e(ex, "Failed to sync events from local assets/news.json")
                Result.failure(e)
            }
        }
    }

    override suspend fun syncIfNeeded(): Result<Unit> {
        val metadata = syncMetadataDao.getByKey(SYNC_KEY_EVENTS)
        val lastSync = metadata?.lastSync ?: 0L
        val elapsed = System.currentTimeMillis() - lastSync
        val intervalMs = 15 * 60 * 1000L // 15 minutes

        return if (elapsed > intervalMs || eventDao.getEventCount() == 0) {
            syncEvents()
        } else {
            Timber.d("Sync not needed, last sync was %d minutes ago", elapsed / 60000)
            Result.success(Unit)
        }
    }

    private fun getDateRange(filter: CalendarFilter): Pair<LocalDate, LocalDate> {
        val today = LocalDate.now()
        return when (filter) {
            CalendarFilter.Today -> today to today
            CalendarFilter.Tomorrow -> today.plusDays(1) to today.plusDays(1)
            CalendarFilter.ThisWeek -> {
                val startOfWeek = today.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY))
                val endOfWeek = today.with(TemporalAdjusters.nextOrSame(DayOfWeek.SUNDAY))
                startOfWeek to endOfWeek
            }
            CalendarFilter.ThisMonth -> {
                val startOfMonth = today.withDayOfMonth(1)
                val endOfMonth = today.with(TemporalAdjusters.lastDayOfMonth())
                startOfMonth to endOfMonth
            }
            is CalendarFilter.Custom -> filter.date to filter.date
        }
    }

    private fun impactToColor(impact: Impact): String = when (impact) {
        Impact.HIGH -> "red"
        Impact.MEDIUM -> "orange"
        Impact.LOW -> "yellow"
        Impact.HOLIDAY -> "gray"
    }

    companion object {
        private const val SYNC_KEY_EVENTS = "events_sync"
    }
}
