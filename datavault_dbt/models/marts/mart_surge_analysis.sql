WITH trips AS (
    SELECT * FROM {{ ref('int_trips_enriched') }}
),

hourly_counts AS (
    SELECT
        corridor_id,
        MAX(corridor_name)      AS corridor_name,
        day_of_week,
        hour_of_day,
        COUNT(*)                AS trip_count,
        COUNT(DISTINCT card_id) AS unique_riders
    FROM trips
    GROUP BY corridor_id, day_of_week, hour_of_day
),

corridor_avg AS (
    SELECT
        corridor_id,
        AVG(trip_count) AS avg_hourly_trips
    FROM hourly_counts
    GROUP BY 1
),

indexed AS (
    SELECT
        h.corridor_id,
        h.corridor_name,
        h.day_of_week,
        h.hour_of_day,
        h.trip_count,
        h.unique_riders,
        ROUND(h.trip_count::DOUBLE / NULLIF(c.avg_hourly_trips, 0), 3) AS demand_index
    FROM hourly_counts h
    JOIN corridor_avg c USING (corridor_id)
)

SELECT * FROM indexed
ORDER BY demand_index DESC
