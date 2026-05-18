WITH trips AS (
    SELECT * FROM {{ ref('int_trips_enriched') }}
)

SELECT
    trip_date,
    corridor_id,
    MAX(corridor_name)                              AS corridor_name,
    COUNT(*)                                        AS total_trips,
    COUNT(*) FILTER (WHERE has_tap_out)             AS complete_trips,
    COUNT(*) FILTER (WHERE NOT has_tap_out)         AS incomplete_trips,
    SUM(pay_amount)                                 AS total_revenue,
    ROUND(AVG(pay_amount) FILTER (WHERE pay_amount IS NOT NULL), 2) AS avg_fare,
    COUNT(DISTINCT card_id)                         AS unique_riders
FROM trips
GROUP BY 1, 2
ORDER BY 1, 2
