WITH trips AS (
    SELECT * FROM {{ ref('int_trips_enriched') }}
)

SELECT
    corridor_id,
    MAX(corridor_name)                                      AS corridor_name,
    COUNT(*)                                                AS total_trips,
    COUNT(*) FILTER (WHERE is_complete_trip)                AS complete_trips,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_complete_trip)
        / NULLIF(COUNT(*), 0), 2)                           AS completion_rate_pct,
    COUNT(DISTINCT trip_date)                               AS active_days,
    COUNT(DISTINCT card_id)                                 AS unique_riders,
    SUM(pay_amount)                                         AS total_revenue,
    ROUND(AVG(distance_km) FILTER (WHERE distance_km IS NOT NULL), 3) AS avg_distance_km,
    ROUND(AVG(duration_min) FILTER (WHERE duration_min IS NOT NULL), 1) AS avg_duration_min
FROM trips
GROUP BY 1
ORDER BY total_trips DESC
