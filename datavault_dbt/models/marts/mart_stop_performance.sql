WITH trips AS (
    SELECT * FROM {{ ref('int_trips_enriched') }}
    WHERE tap_in_stop_id IS NOT NULL
),

stop_raw AS (
    SELECT
        tap_in_stop_id                              AS stop_id,
        tap_in_stop_name                            AS stop_name,
        tap_in_lat                                  AS lat,
        tap_in_lon                                  AS lon,
        COUNT(*)                                    AS total_boardings,
        SUM(pay_amount)                             AS total_revenue,
        COUNT(DISTINCT card_id)                     AS unique_riders,
        COUNT(DISTINCT corridor_id)                 AS corridors_served
    FROM trips
    GROUP BY 1, 2, 3, 4
),

stats AS (
    SELECT
        MIN(total_boardings)    AS min_vol,
        MAX(total_boardings)    AS max_vol,
        MIN(total_revenue)      AS min_rev,
        MAX(total_revenue)      AS max_rev
    FROM stop_raw
),

scored AS (
    SELECT
        s.stop_id,
        s.stop_name,
        s.lat,
        s.lon,
        s.total_boardings,
        s.total_revenue,
        s.unique_riders,
        s.corridors_served,
        -- normalize volume 0-100, revenue 0-100, composite 50/50
        ROUND(100.0 * (s.total_boardings - st.min_vol)
              / NULLIF(st.max_vol - st.min_vol, 0), 2)  AS volume_score,
        ROUND(100.0 * (COALESCE(s.total_revenue, 0) - st.min_rev)
              / NULLIF(st.max_rev - st.min_rev, 0), 2)  AS revenue_score,
        ROUND(
            0.5 * (100.0 * (s.total_boardings - st.min_vol)
                   / NULLIF(st.max_vol - st.min_vol, 0))
          + 0.5 * (100.0 * (COALESCE(s.total_revenue, 0) - st.min_rev)
                   / NULLIF(st.max_rev - st.min_rev, 0))
        , 2)                                            AS performance_score
    FROM stop_raw s CROSS JOIN stats st
)

SELECT * FROM scored
ORDER BY performance_score DESC
